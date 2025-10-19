from socket import socket
from typing import Dict, Optional

EOF = '\u200B'


class Buffer:
    __instances: Dict[socket, 'Buffer'] = {}

    def __init__(self, sock: socket):
        self.sock = sock
        self.buffer = b''

    @classmethod
    def get(cls, sock: socket) -> 'Buffer':
        if sock not in cls.__instances:
            cls.__instances[sock] = Buffer(sock)
        return cls.__instances[sock]

    def read_until(self, separator: bytes = EOF.encode(), buffer_size: int = 1024) -> Optional[bytes]:
        while separator not in self.buffer:
            try:
                data = self.sock.recv(buffer_size)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                if self.buffer:
                    remaining = self.buffer
                    self.buffer = b''
                    return remaining
                else:
                    return None

            if not data:
                if self.buffer:
                    remaining = self.buffer
                    self.buffer = b''
                    return remaining
                else:
                    return None

            self.buffer += data

        line, _, self.buffer = self.buffer.partition(separator)
        return line

    @staticmethod
    def readuntil(sock: socket, separator: bytes = EOF.encode(), buffer_size: int = 1024) -> Optional[bytes]:
        instance = Buffer.get(sock)
        return instance.read_until(separator=separator, buffer_size=buffer_size)
