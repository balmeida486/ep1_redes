from enum import Enum
from typing import Optional
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_KEEPALIVE

from src.models.buffer import EOF
from src.models.clock import Clock


class PeerStatus(Enum):
    """
    Enumeração que representa o status de um peer na rede.

    Pode ser:
    - Online (ativo e acessível)
    - Offline (inativo ou inacessível)
    """

    Offline = 0
    Online = 1

    def __str__(self):
        """
        Retorna a representação em string do status, para fins de exibição.
        """
        return "OFFLINE" if self == PeerStatus.Offline else "ONLINE"

    @staticmethod
    def from_string(value: str) -> 'PeerStatus':
        """
        Converte uma string para um valor PeerStatus.

        Args:
            value (str): String contendo "online" ou "offline" (case insensitive).

        Returns:
            PeerStatus: Enum correspondente.
        """
        return PeerStatus.Online if value.lower() == "online" else PeerStatus.Offline


class Peer:
    """
    Representa um peer (nó) conhecido da rede P2P.

    A instância mantém:
    - o IP/host
    - a porta de escuta
    - o status atual (Online/Offline)
    """

    host: str
    port: int
    status: PeerStatus
    clock: Clock
    conn: Optional[socket]

    def __init__(self, host: str, port: int, status: str = "offline", conn: Optional[socket] = None):
        """
        Inicializa um peer com endereço, porta e status (padrão: offline).

        Args:
            host (str): Endereço IP ou hostname do peer.
            port (int): Porta TCP usada pelo peer.
            status (str): Status inicial do peer ("online" ou "offline").
        """
        self.host = host
        self.port = int(port)
        self.status = PeerStatus.from_string(status)
        self.clock = Clock()
        self.conn = conn

    def change_status(self, new_status: PeerStatus, clock_n: Optional[int] = None):
        """
        Atualiza o status do peer, se for diferente do atual.

        Args:
            new_status (PeerStatus): Novo status (Online ou Offline).
            clock_n (Optional[int]): Contagem do clock para mudança de status.
        """
        if clock_n is not None and clock_n < self.clock.count:
            return

        if self.status != new_status:
            self.status = new_status
            print(
                f"Atualizando peer {self.host}:{self.port} status {self.status}")

            if self.status == PeerStatus.Online and self.conn is None:
                self.connect()
            elif self.status == PeerStatus.Offline:
                self.conn = None

    def send_message(self, message: str):
        self.conn.sendall(f"{message}{EOF}".encode())

    def connect(self) -> socket:
        conn = socket(AF_INET, SOCK_STREAM)
        conn.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
        conn.connect((self.host, self.port))
        self.conn = conn
        return conn
