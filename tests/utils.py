class FakeSocket:
    def __init__(self):
        self.sent = []
        self.to_recv = []

    def send(self, data):
        self.sent.append(data)

    def recv(self, n):
        if not self.to_recv:
            return b""
        return self.to_recv.pop(0)

    def close(self):
        pass
