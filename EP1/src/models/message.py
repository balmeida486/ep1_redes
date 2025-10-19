from typing import List


class Message:
    """
    Representa uma mensagem trocada entre peers no sistema distribuído.

    A mensagem é composta por:
    - endereço do peer remetente (host:port)
    - clock lógico
    - conteúdo da mensagem (ex: "GET_PEERS", "PEER_LIST ...")
    - ação (ex: "GET_PEERS", "PEER_LIST", "BYE")
    - argumentos adicionais (args), extraídos a partir do restante da string
    """

    host: str
    port: int
    clock: int
    message: str
    action: str
    args: List[str]

    def __init__(self, data: bytes):
        """
        Inicializa uma instância de Message a partir de um payload em bytes.

        Espera-se que a mensagem recebida tenha o seguinte formato:
        "<host>:<port> <clock> <mensagem> [args...]"

        Exemplo:
            b"127.0.0.1:9001 5 GET_PEERS"
            b"127.0.0.1:9002 7 PEER_LIST 2 127.0.0.1:9003:ONLINE:0 ..."

        Args:
            data (bytes): A mensagem recebida via socket TCP.
        """
        m = data.decode()
        s = m.split(" ")
        address, clock, msg, self.args = (s[0], s[1], s[2], s[3:])
        s = address.split(":")
        self.host, self.port = s[0], int(s[1])
        self.clock = int(clock)
        self.message = msg
        self.action = msg.strip().split(" ")[0]

    def __str__(self):
        """
        Retorna a representação string da mensagem original (sem args extras).
        """
        return f"{self.host}:{self.port} {self.clock} {self.message}"
