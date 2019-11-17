import socket
import select
import queue
import json
import struct

from BlockchainController import BlockchainController
from blockchain.messages import MessageType


class DaemonController:
    def __init__(self, blockchain_controller: 'BlockchainController'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 5602))
        sock.listen(10)
        self.sock = sock
        self.inputs = [sock]
        self.outputs = []
        self.message_queues = {}
        self.blockchain = blockchain_controller
        print("Daemon init end")

    def balance(self):
        public_key = self.blockchain.key.public_key().export_key(format='PEM')
        if public_key not in self.blockchain.user_credits:
            return {"balance": 0}
        return {"balance": self.blockchain.user_credits[self.blockchain.key.public_key()]}

    def send_message(self, message, destination: socket):
        print("send", message)
        self.message_queues[destination].put(message.encode())
        self.outputs.append(destination)

    def new_job(self, job):
        self.blockchain.publish_job(job)

    def get_jobs(self, s):
        self.send_message(json.dumps(self.blockchain.pool_jobs), s)

    def handle_message(self, s, data):
        for raw_json in data.decode().split('\n'):
            if not raw_json:
                return
            # print("receive", raw_json)
            message = json.loads(raw_json)
            if message['type'] == 'BALANCE':
                self.send_message(json.dumps(self.balance()), s)
            elif message['type'] == MessageType.NEW_JOB:
                self.new_job(message)
            elif message['type'] == 'GET_JOBS':
                self.get_jobs(s)
            elif message['type'] == MessageType.JOB_DONE:
                self.job_done(message)

    def update(self):
        readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs,1)
        for s in readable:
            if s is self.sock:
                connection, client_address = s.accept()
                self.inputs.append(connection)
                self.message_queues[connection] = queue.Queue()
            else:

                data = s.recv(4)
                if data:
                    size = struct.unpack("!i", data[:4])[0]
                    print("size WTF", size)
                    buffer = data[4:]
                    size -= len(buffer)
                    while size > 0:
                        data = s.recv(min(size, 4096))
                        buffer += data
                        size -= len(data)
                    print("size", size, len(buffer))
                    self.handle_message(s, buffer)
                else:
                    if s in self.outputs:
                        self.outputs.remove(s)
                    self.inputs.remove(s)
                    s.close()
                    del self.message_queues[s]

        for s in writable:
            try:
                next_msg = self.message_queues[s].get_nowait()
            except queue.Empty:
                self.outputs.remove(s)
            except KeyError:
                pass
            else:
                s.send(next_msg)

        for s in exceptional:
            self.inputs.remove(s)
            if s in self.outputs:
                self.outputs.remove(s)
            s.close()
            del self.message_queues[s]

    def job_done(self, message):
        self.blockchain.share_job_done(message)


