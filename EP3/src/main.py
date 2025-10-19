from typing import Dict, List

from src.models.server import Server
from src.models.peer import Peer, PeerStatus
from src.utils import draw_row, standard_deviation


def load_peers(path: str) -> Dict[str, Peer]:
    """
    Carrega a lista de peers a partir de um arquivo texto.

    Cada linha do arquivo deve ter o formato: <host>:<port>

    Args:
        path (str): Caminho do arquivo contendo a lista de peers.

    Returns:
        Dict[str, Peer]: Dicionário de peers indexado por "host:port".
    """
    peers: Dict[str, Peer] = {}

    with open(file=path, mode="r", encoding="utf-8") as file:
        data = file.read()
        lines = data.split("\n")

        for line in lines:
            if len(line) == 0:
                continue

            host, port = line.strip().split(":")
            peer = Peer(host=host, port=int(port))
            key = f"{host}:{port}"
            peers[key] = peer

            print(f"Adicionando novo peer {host}:{port} status OFFLINE")

        return peers


def init_server(address: str, shared_dir: str, peers: Dict[str, Peer]) -> Server:
    """
    Inicializa a instância do servidor com o endereço e os peers conhecidos.

    Args:
        address (str): Endereço no formato "<host>:<port>".
        peers (Dict[str, Peer]): Dicionário de peers já conhecidos.

    Returns:
        Server: Instância do servidor pronta para escutar conexões.
    """
    host, port = address.split(":")
    server = Server(host=host, port=int(port),
                    shared_dir=shared_dir, peers=peers)
    return server


def menu() -> int:
    """
    Exibe o menu principal de comandos e lê a opção escolhida pelo usuário.

    Returns:
        int: Número da opção selecionada.
    """
    print("\nEscolha um comando:")
    print("\t1. Listar peers")
    print("\t2. Obter peers")
    print("\t3. Listar arquivos locais")
    print("\t4. Buscar arquivos")
    print("\t5. Exibir estatísticas")
    print("\t6. Alterar tamanho de chunk")
    print("\t[9]. Sair")
    opt = int(input("> "))
    return opt


def handle_list_peers(server: Server):
    """
    Exibe a lista de peers e permite interagir com um peer específico,
    enviando uma mensagem de "HELLO" e atualizando seu status com base na resposta.

    Args:
        server (Server): Instância do servidor atual.
    """
    peers_list: List[Peer] = list(server.peers.values())

    print("\nLista de peers:")
    print("[0] voltar para o menu anterior")
    for index, peer in enumerate(peers_list):
        print(f"[{index + 1}] {peer.host}:{peer.port} {peer.status}")
    opt = int(input("> "))

    if opt == 0:
        return
    elif opt > 0 and opt <= len(peers_list):
        peer = peers_list[opt - 1]
        ok = server.send_message(peer=peer, message="HELLO")
        new_status = PeerStatus.Online if ok is True else PeerStatus.Offline
        peer.change_status(new_status=new_status)
    else:
        print("Comando inválido, tente novamente outro")
        handle_list_peers(server=server)


def handle_show_stats(server: Server):
    widths = [15, 10, 15, 5, 50, 10]
    print(draw_row(["Tam. chunk", "N peers", "Tam. arquivo",
          "N", "Tempo[s]", "Desvio"], widths))

    for [(chunk_size, peers, file_size), ellapsed_times] in server.state["stats"].items():
        print(draw_row([chunk_size, peers, file_size, len(ellapsed_times), ", ".join(
            map(str, ellapsed_times)), standard_deviation(ellapsed_times)], widths))
