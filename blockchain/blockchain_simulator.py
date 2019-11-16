import blockchain.messages
import socket

TCP_PORT = 5599
TCP_IP = '127.0.0.1'
BUFFER_SIZE = 4096

class BlockchainSimulator:
    #data = s.recv(BUFFER_SIZE)
    def __init__(self):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((TCP_IP, TCP_PORT))
        return
    

if __name__ == "__main__":
    simulator = BlockchainSimulator()
    simulator.sock.connect((TCP_IP, TCP_PORT))