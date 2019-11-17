from blockchain.messages import Message
from blockchain.messages import MessageType
from Cryptodome.Hash import SHA256
from Cryptodome.Signature import DSS
from Cryptodome.PublicKey import ECC
import socket
import os
import time

TCP_PORT = 5599
TCP_IP = '127.0.0.1'
BUFFER_SIZE = 4096

class BlockchainSimulator:
    #data = s.recv(BUFFER_SIZE)
    def __init__(self):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.currentBalance = 10
        self.simulatorBalance = 100
        if not os.path.exists('simulatorpublickey.pem'):
            self.key = ECC.generate(curve='P-256')
            f = open('simulatorpublickey.pem', 'wt')
            f.write(key.public_key().export_key(format='PEM'))
            f.close()
            f = open('simulatorprivatekey.pem', 'wt')
            f.write(key.export_key(format='PEM'))
            f.close()
            return
        else:
            f = open('simulatorprivatekey.pem', 'rt')
            self.key = ECC.import_key(f.read())
            f.close()
        return

    def getBalanceOfUser(self):
        return self.currentBalance
    
    def payBountyToUser(self, bounty):
        self.currentBalance + bounty
        self.simulatorBalance - bounty

    def userPaysBounty(self, bounty):
        self.currentBalance - bounty
        self.simulatorBalance + bounty
    
if __name__ == "__main__":
    simulator = BlockchainSimulator()
    simulator.sock.connect((TCP_IP, TCP_PORT))

    messageBasic = Message(MessageType.NEW_JOB)
    messageBasic.metadata = {
        "bounty": 10,
        "valid-until": time.time() + 604800
    }
    messageBasic.data = "matoran/lauzhack_knn_5@sha256:6520a3942ac2e2c91ab747a22c5d748b7f2e3acbd4414aa5867d752c5d60fb10"
    messageBasic.do_crypto_shit(simulator.key)

    unpaidWorkLikeThisIsMothafuckinBangladesh = Message(MessageType.NEW_JOB)
    unpaidWorkLikeThisIsMothafuckinBangladesh.metadata = {
        "bounty": 1,
        "valid-until": time.time() + 604800
    }
    unpaidWorkLikeThisIsMothafuckinBangladesh.data = "matoran/lauzhack_knn_5@sha256:6520a3942ac2e2c91ab747a22c5d748b7f2e3acbd4414aa5867d752c5d60fb10"
    unpaidWorkLikeThisIsMothafuckinBangladesh.do_crypto_shit(simulator.key)

    messageShortLikeUDick = Message(MessageType.NEW_JOB)
    messageShortLikeUDick.metadata = {
        "bounty": 10,
        "valid-until": time.time() + 3600
    }
    messageShortLikeUDick.data = "matoran/lauzhack_knn_5@sha256:6520a3942ac2e2c91ab747a22c5d748b7f2e3acbd4414aa5867d752c5d60fb10"
    messageShortLikeUDick.do_crypto_shit(simulator.key)

    simulator.sock.send(messageBasic.to_json())
    simulator.sock.send(unpaidWorkLikeThisIsMothafuckinBangladesh.to_json())
    simulator.sock.send(messageShortLikeUDick.to_json())