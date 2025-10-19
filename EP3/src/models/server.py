import os
import math
from typing import Dict, Optional, List, Tuple
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread, Lock
from pathlib import Path
from time import sleep, time
from base64 import b64encode, b64decode

from src.models.buffer import Buffer
from src.models.clock import Clock
from src.models.peer import Peer, PeerStatus
from src.models.file import File
from src.models.message import Message
from src.utils import encode, decode, draw_row
from src.exceptions.InvalidDirectoryException import InvalidDirectoryException


class Server():
    host: str
    port: int
    shared_dir: str
    _app: socket
    _clock: Clock
    chunk_size: int = 256
    peers: Dict[str, Peer]
    state: Dict[str, any]

    def __init__(self, host: str = "0.0.0.0", port: int = 19000, shared_dir: str = ".", peers: Optional[Dict[str, Peer]] = None):
        """
        Inicializa o servidor com o endereço e porta especificados.

        Args:
            host (str): Endereço IP para escutar (default: "0.0.0.0").
            port (int): Porta para escutar (default: 19000).
            shared_dir (str): Caminho do diretório compartilhado (default: pasta atual).
            peers (Optional[Dict[str, Peer]]): Mapa inicial de peers conhecidos.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.shared_dir = shared_dir
        if peers is None:
            peers = {}
        self.peers = peers
        self._app = socket(AF_INET, SOCK_STREAM)
        self._clock = Clock()
        self.state = {"peer_locks": {}, "stats": {}}

        self.load_shared_dir()

    def listen(self):
        """
        Inicia o servidor TCP, escutando conexões na porta configurada.
        Cada conexão recebida é processada em uma nova thread.
        """
        self._app.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._app.bind((self.host, self.port))
        self._app.listen()

        while True:
            try:
                (conn, _) = self._app.accept()
                t = Thread(target=self.handle_connection,
                           args=(conn,), daemon=True)
                t.start()
            except OSError:
                break

    def handle_connection(self, conn: socket):
        """
        Processa uma conexão recebida de outro peer.
        Lê a mensagem, interpreta a ação e executa a resposta apropriada.

        Args:
            conn (socket): Socket da conexão com o peer.
        """
        while True:
            data = Buffer.readuntil(sock=conn, buffer_size=self.chunk_size)
            if data is None:
                continue

            message = Message(data=data)

            self._clock.count = max(message.clock, self._clock.count)

            self._clock.increment()

            sender = f"{message.host}:{message.port}"

            if sender not in self.peers:
                self.peers[sender] = Peer(
                    host=message.host, port=message.port)

            self.peers[sender].clock.update(new_clock=message.clock)

            if sender not in self.state["peer_locks"]:
                self.state["peer_locks"][sender] = Lock()

            if message.action == "GET_PEERS":
                self.peers[sender].change_status(
                    new_status=PeerStatus.Online)
                print(f"Mensagem recebida {data.decode()}")

                # Responde com a lista de peers conhecidos, exceto ele mesmo
                filtered_peers = list(filter(
                    lambda x: f"{x.host}:{x.port}" != sender, self.peers.values()))
                if len(filtered_peers) > 0:
                    peers_str = " ".join(
                        f"{p.host}:{p.port}:{p.status}:{p.clock.count}" for p in filtered_peers
                    )
                    reply = f"PEER_LIST {len(filtered_peers)} {peers_str}"
                    self.send_message(
                        peer=self.peers[sender], message=reply)

            elif message.action == "PEER_LIST":
                self.peers[sender].change_status(
                    new_status=PeerStatus.Online)
                print(f"Resposta recebida {data.decode()}")

                # Atualiza a lista de peers com os recebidos
                peers_list = message.args[1:]
                for item in peers_list:
                    (host, port, status, clock_n) = item.split(":")
                    key = f"{host}:{port}"
                    if key not in self.peers:
                        self.peers[key] = Peer(
                            host=host, port=int(port), status=status)

                    ok = self.peers[key].clock.update(
                        new_clock=int(clock_n))
                    if ok:
                        self.peers[key].change_status(
                            new_status=PeerStatus.from_string(status))

            elif message.action == "LS":
                self.peers[sender].change_status(
                    new_status=PeerStatus.Online)
                print(f"Mensagem recebida {data.decode()}")

                files = self.get_shared_files()
                files_str = f"LS_LIST {len(files)} " + \
                    " ".join(f"{encode(x[0])}:{x[1]}" for x in files)
                self.send_message(
                    peer=self.peers[sender], message=files_str)

            elif message.action == "LS_LIST":
                print(f"Resposta recebida {data.decode()}")

                files = []
                if int(message.args[0]) > 0:
                    for data in message.args[1:]:
                        splited = data.strip().split(":")
                        name, size = decode(
                            ":".join(splited[0:-1])), int(splited[-1])
                        files.append((name, size))

                if "LS" not in self.state:
                    self.state["LS"] = {}

                self.state["LS"][f"{sender}"] = files

            elif message.action == "DL":
                print(f"Mensagem recebida {data.decode()}")

                file_name, chunk_size, chunk_index = message.args[0], int(
                    message.args[1]), int(message.args[2])
                decoded_file_name = decode(file_name)
                location = Path(self.shared_dir, decoded_file_name)
                with open(location, mode="rb+") as arq:
                    arq.seek(chunk_index * chunk_size)
                    data = arq.read(chunk_size)
                    b64chunk = b64encode(data).decode("utf-8")
                    self.send_message(
                        peer=self.peers[sender], message=f"FILE {file_name} {chunk_size} {chunk_index} {b64chunk}")

            elif message.action == "FILE":
                print(f"Resposta recebida {data.decode()}")
                file_name, chunk_size, chunk_index, b64chunk = message.args[0], int(
                    message.args[1]), int(message.args[2]), message.args[3]
                chunk_data = b64decode(b64chunk)

                temp_file = self.state["temp_file"]
                temp_file["data"][chunk_index] = chunk_data
                temp_file["downloaded"] += 1

                if temp_file["qtd_chunks"] == temp_file["downloaded"]:
                    key = (temp_file["chunk_size"],
                           temp_file["peers"], temp_file["file_size"])
                    if key not in self.state["stats"]:
                        self.state["stats"][key] = []
                    self.state["stats"][key].append(
                        time() - temp_file["started_at"])

                    decoded_file_name = decode(file_name)
                    location = Path(self.shared_dir, decoded_file_name)
                    with open(location, mode="wb") as arq:
                        for index in range(temp_file["qtd_chunks"]):
                            arq.write(temp_file["data"][index])

                        temp_file.clear()
                        print(
                            f"Download do arquivo {decoded_file_name} finalizado.")

            elif message.action == "BYE":
                # Marca o peer como offline
                print(f"Mensagem recebida: {data.decode()}")
                self.peers[sender].change_status(
                    new_status=PeerStatus.Offline)
                break

    def shutdown(self):
        """
        Envia a mensagem BYE para todos os peers online e encerra o servidor.
        """
        for peer in self.peers.values():
            if peer.status == PeerStatus.Offline:
                continue
            self.send_message(peer=peer, message="BYE")

        self.stop()

    def stop(self):
        """
        Fecha o socket principal do servidor, encerrando o loop de escuta.
        """
        try:
            self._app.close()
        except:
            pass

    def load_shared_dir(self):
        """
        Valida o diretório compartilhado. Lança exceção se for inválido.

        Raises:
            InvalidDirectoryException: Se o diretório não existir ou for ilegível.
        """
        ok = os.path.isdir(self.shared_dir) and os.access(
            self.shared_dir, os.R_OK)
        if not ok:
            raise InvalidDirectoryException

    def send_message(self, peer: Peer, message: str) -> bool:
        """
        Envia uma mensagem TCP para um peer específico.

        Args:
            peer (Peer): Peer de destino.
            message (str): Conteúdo da mensagem.

        Returns:
            bool: True se enviado com sucesso, False caso contrário.
        """
        try:
            if peer.conn is None:
                peer.connect()

            self._clock.increment()
            m = f"{self.host}:{self.port} {self._clock.count} {message}"
            peer.send_message(message=m)
            return True
        except Exception:
            return False

    def find_peers(self):
        """
        Envia a mensagem GET_PEERS para todos os peers conhecidos,
        atualizando o status de cada um como Online/Offline.
        """
        peers_list: List[Peer] = list(self.peers.values())

        for peer in peers_list:
            ok = self.send_message(peer=peer, message="GET_PEERS")
            print(
                f'Encaminhando mensagem "{self.host}:{self.port} {self._clock.count} GET_PEERS" para {peer.host}:{peer.port}')
            new_status = PeerStatus.Online if ok is True else PeerStatus.Offline
            peer.change_status(new_status=new_status)

    def get_shared_files(self) -> List[Tuple[str, int]]:
        """
        Obtém uma lista de duplas de arquivos da pasta compartilhada contendo (nome, tamanho em bytes) de cada arquivo
        """
        files: List[Tuple[str, int]] = []
        for file in Path(self.shared_dir).iterdir():
            if file.is_file():
                files.append((file.name, file.stat().st_size))
        return files

    def __discover_files(self) -> List[Peer]:
        """
        Descobre arquivos na rede.

        Envia a mensagem "LS" (List Shared) para todos os peers online
        e aguarda as respostas para preencher o estado local.

        Returns:
            List[Peer]: Lista de peers online que responderam à solicitação.
        """
        peers_list = [peer for peer in self.peers.values(
        ) if peer.status == PeerStatus.Online]

        for peer in peers_list:
            self.send_message(peer=peer, message="LS")

        if "LS" not in self.state:
            self.state["LS"] = {}

        while len(self.state["LS"]) < len(peers_list):
            sleep(0.1)

        return peers_list

    def __group_files(self) -> Dict[str, List[File]]:
        """
        Agrupa arquivos recebidos dos peers.

        Transforma a lista de arquivos recebidos (armazenados em self.state["LS"])
        em um dicionário agrupado por uma chave única (gerada por File.key()).

        Returns:
            Dict[str, List[File]]: Dicionário onde a chave é o identificador do arquivo (name+size)
                                e o valor é a lista de instâncias File compartilhadas pelos peers.
        """
        grouped_files = {}

        for peer_address in self.state["LS"]:
            peer_files = self.state["LS"][peer_address]
            for name, size in peer_files:
                file = File(name=name, size=size, peer_address=peer_address)
                key = file.key()
                if key not in grouped_files:
                    grouped_files[key] = []
                grouped_files[key].append(file)

        self.state["LS"].clear()
        return grouped_files

    def __display_files(self, grouped_files: Dict[str, List[File]]) -> List[List[File]]:
        """
        Exibe os arquivos disponíveis agrupados e permite seleção pelo usuário.

        Args:
            grouped_files (Dict[str, List[File]]): Dicionário agrupado com os arquivos da rede.

        Returns:
            List[List[File]]: Lista de grupos de arquivos (cada grupo representa um arquivo com cópias em diferentes peers).
        """
        print("Arquivos encontrados na rede: \n")

        widths = [40, 10, 15]
        print(draw_row(["Nome", "Tamanho", "Peer"], widths))
        print(draw_row(["[  0] <Cancelar>", "", ""], widths))

        groups = list(grouped_files.values())

        for index, files in enumerate(groups):
            name, size = files[0].name, files[0].size
            peer_addresses = ", ".join(f.peer_address for f in files)
            print(draw_row([f"[{index + 1:>3}] {name}",
                  size, peer_addresses], widths))

        return groups

    def __handle_download_selection(self, groups: List[List[File]]):
        """
        Lida com a seleção de download feita pelo usuário.

        Solicita ao usuário que escolha um arquivo para download e,
        com base na escolha, envia as mensagens "DL" para os peers
        de forma rotativa (round-robin) para baixar os chunks do arquivo.

        Args:
            groups (List[List[File]]): Lista de grupos de arquivos disponíveis para seleção.
        """
        print("\nDigite o número do arquivo para fazer download")
        opt = int(input(">"))

        if opt > 0 and opt < len(groups):
            selected_group_files = groups[opt - 1]
            file = selected_group_files[0]
            name, size = file.name, file.size
            peer_addresses = [f.peer_address for f in selected_group_files]
            qtd_chunks = math.ceil(size / self.chunk_size)

            self.state["temp_file"] = {
                "qtd_chunks": qtd_chunks,
                "downloaded": 0,
                "data": {},
                "chunk_size": self.chunk_size,
                "peers": len(peer_addresses),
                "file_size": size,
                "started_at": time()
            }

            for i in range(qtd_chunks):
                peer_address = peer_addresses[i % len(peer_addresses)]
                self.send_message(
                    peer=self.peers[peer_address],
                    message=f"DL {encode(name)} {self.chunk_size} {i}"
                )

    def search_files(self):
        """
        Fluxo completo de busca e seleção de arquivos na rede.

        1. Descobre arquivos disponíveis nos peers online.
        2. Agrupa os arquivos por identidade.
        3. Exibe a lista de arquivos agrupados.
        4. Lida com a seleção do usuário para iniciar o download.

        """
        self.__discover_files()
        grouped_files = self.__group_files()
        groups = self.__display_files(grouped_files)
        self.__handle_download_selection(groups)
