class File:
    name: str
    size: int
    peer_address: str

    def __init__(self, name: str, size: int, peer_address):
        self.name = name
        self.size = size
        self.peer_address = peer_address

    def __eq__(self, other):
        if not isinstance(other, File):
            return NotImplemented
        return (self.name, self.size) == (other.name, other.size)

    def __hash__(self):
        return hash((self.name, self.size))

    def __repr__(self):
        return f"File(name={self.name}, size={self.size}, peer_address={self.peer_address})"

    def key(self):
        return f"{self.name}:{self.size}"
