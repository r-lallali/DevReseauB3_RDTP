import socket
import time
import subprocess
import os
import sys
import struct
import threading

# Allow import from common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from common.protocol import *
except ImportError:
    sys.path.append(os.getcwd())
    from common.protocol import *

HOST = "127.0.0.1"
PORT = 5002

def receive_msg(sock, expected_type=None):
    try:
        header = sock.recv(5)
        if not header:
            return None, None
        msg_type, length = unpack_header(header)
        payload = b""
        if length > 0:
            payload = sock.recv(length)
        
        if expected_type and msg_type != expected_type:
             print(f"WARN: Expected {expected_type} got {msg_type}")
             
        return msg_type, payload
    except Exception as e:
        print(f"Error receiving: {e}")
        return None, None

def run_test():
    print("Starting Server...")
    server_process = subprocess.Popen([sys.executable, "-m", "server.server_main"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.STDOUT,
                                      cwd=os.getcwd())
    time.sleep(1) 
    
    clients = []

    try:
        # Client 1: Alice
        print("--- Alice connecting ---")
        alice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        alice.connect((HOST, PORT))
        clients.append(alice)
        
        # Login Alice
        alice.send(pack_message(LOGIN, pack_string("Alice")))
        mt, _ = receive_msg(alice, LOGIN_OK)
        if mt != LOGIN_OK:
            print("Alice Login failed")
            return

        # Join Room
        print("--- Alice joining Room1 ---")
        alice.send(pack_message(JOIN, pack_string("Room1")))
        mt, _ = receive_msg(alice, JOIN_OK)
        if mt != JOIN_OK:
             print("Alice Join failed")
             return
        print("Alice in Room1")

        # Client 2: Bob
        print("--- Bob connecting ---")
        bob = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bob.connect((HOST, PORT))
        clients.append(bob)
        
        # Login Bob
        bob.send(pack_message(LOGIN, pack_string("Bob")))
        mt, _ = receive_msg(bob, LOGIN_OK)
        if mt != LOGIN_OK:
            print("Bob Login failed")
            return

        # Listen on Alice in background to catch broadcast
        def listen_alice():
             print("Alice waiting for broadcast...")
             mt, payload = receive_msg(alice)
             if mt == MSG_BROADCAST:
                 # decode broadcast
                 sender_len = struct.unpack(">H", payload[:2])[0]
                 sender = payload[2:2+sender_len].decode('utf-8')
                 offset = 2+sender_len
                 msg_len = struct.unpack(">H", payload[offset:offset+2])[0]
                 msg = payload[offset+2 : offset+2+msg_len].decode('utf-8')
                 
                 print(f"Alice received Broadcast from {sender}: {msg}")
                 if sender == "Serveur" and "Bob" in msg and "connecté" in msg:
                     print("SUCCESS: Notification verified!")
                 else:
                     print("FAILURE: Message content mismatch")
             else:
                 print(f"Alice received unexpected type: {mt}")

        t = threading.Thread(target=listen_alice)
        t.start()

        time.sleep(0.5)

        # Join Bob
        print("--- Bob joining Room1 ---")
        bob.send(pack_message(JOIN, pack_string("Room1")))
        mt, _ = receive_msg(bob, JOIN_OK)
        if mt != JOIN_OK:
             print("Bob Join failed")
             return
        print("Bob in Room1")
        
        t.join(timeout=2.0)
        if t.is_alive():
            print("Timeout waiting for broadcast")

    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up...")
        for s in clients:
            s.close()
        server_process.kill()
        server_process.wait()

if __name__ == "__main__":
    run_test()
