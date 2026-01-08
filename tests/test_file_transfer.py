import threading
from server.server import ChatServer
from common.protocol import *
from tests.utils import FakeSocket

def test_msg_blocked_during_file_offer():
    server = ChatServer()
    sock = FakeSocket()

    def send(msg):
        sock.to_recv.append(msg[:5])
        sock.to_recv.append(msg[5:])

    send(pack_message(LOGIN, pack_string("Alice")))
    send(pack_message(JOIN, pack_string("music")))
    send(pack_message(FILE_OFFER,
        pack_string("test.wav") + pack_int(123)
    ))
    send(pack_message(MSG, pack_string("hello")))

    t = threading.Thread(target=server.handle_client, args=(sock,))
    t.start()
    t.join(timeout=1)

    sent_types = [m[0] for m in sock.sent]
    assert ERROR in sent_types
