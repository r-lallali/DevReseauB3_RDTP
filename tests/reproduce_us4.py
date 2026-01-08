import socket
import time
import subprocess
import os
import sys
import struct

# Allow import from common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from common.protocol import *
except ImportError:
    # Backup if running from root without common in path
    sys.path.append(os.getcwd())
    from common.protocol import *

HOST = "127.0.0.1"
PORT = 5002

def run_test():
    print("Starting Server...")
    # Start server in background
    # Run server as a module to ensure imports work
    server_process = subprocess.Popen([sys.executable, "-m", "server.server_main"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.STDOUT, # Merge stderr to stdout for easier debugging
                                      cwd=os.getcwd())
    time.sleep(1) # Give it time to start
    
    clients = []

    try:
        # Client 1
        print("--- Connecting Client 1 ---")
        sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock1.connect((HOST, PORT))
        clients.append(sock1)
        
        payload1 = pack_string("User1")
        sock1.send(pack_message(LOGIN, payload1))
        
        header1 = sock1.recv(5)
        msg_type1, _ = unpack_header(header1)
        if msg_type1 == LOGIN_OK:
            print("Client 1 logged in successfully.")
        else:
            print(f"Client 1 failed to log in. Got: {msg_type1}")
            return

        # Client 2
        print("--- Connecting Client 2 ---")
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock2.settimeout(2.0)
        sock2.connect((HOST, PORT))
        clients.append(sock2)
        
        payload2 = pack_string("User2")
        sock2.send(pack_message(LOGIN, payload2))
        
        try:
            header2 = sock2.recv(5)
            msg_type2, _ = unpack_header(header2)
            if msg_type2 == LOGIN_OK:
                print("Client 2 logged in successfully.")
            else:
                print(f"Client 2 failed to log in. Got: {msg_type2}")
        except socket.timeout:
            print("Client 2 timed out waiting for response.")

        print("--- Testing Persistence ---")
        # Now, theoretically, both should be "maintained".
        # Current server implementation abandons the socket loop after handle_client returns.
        # So they are essentially zombies.
        # But let's check if the TCP connection is still open (send usage).
        # We can't really test "handling" yet because the server code handles nothing else.
        
        print("Test finished.")

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
