import queue
import select
import socket
import json
import time
import os.path
import binascii

from Cryptodome.Hash import SHA256
from Cryptodome.Signature import DSS
from Cryptodome.PublicKey import ECC


class BlockchainController:
    def __init__(self):
        self.pool_jobs = []
        self.blockchain = []
        self.jobs = {}
        self.user_credits = {}
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 5599))
        sock.listen(50)
        self.sock = sock
        self.inputs = [sock]
        self.outputs = []
        self.message_queues = {}
        self.key = None

        if not os.path.exists('myprivatekey.pem'):
            print("creating new ECC private key")
            self.key = ECC.generate(curve='P-256')
            f = open('mypublickey.pem', 'wt')
            f.write(self.key.public_key().export_key(format='PEM'))
            f = open('myprivatekey.pem', 'wt')
            f.write(self.key.export_key(format='PEM'))
            f.close()
        else:
            print("reading existing key")
            f = open('myprivatekey.pem', 'rt')
            self.key = ECC.import_key(f.read())
            f.close()

        print("BlockchainController init end")

    def sign(self, message):
        h = SHA256.new(message)
        signer = DSS.new(self.key, 'fips-186-3')
        signature = signer.sign(h)
        return signature

    def verify_message(self, message):
        signature = message['signature']
        del message['signature']
        h = SHA256.new(message.encode())
        verifier = DSS.new(message['key'], 'fips-186-3')
        try:
            verifier.verify(h, signature)
            return True
        except ValueError:
            return False

    def new_job(self, job):
        if job not in self.pool_jobs:
            self.pool_jobs.append(job)

        # TODO should try this job ? From which data ?
        self.do_job()

    def do_job(self):
        pass

    def sign_and_broadcast(self, message):
        message['key'] = self.key.public_key().export_key(format='PEM')
        data = json.dumps(message).encode()
        message['signature'] = binascii.hexlify(self.sign(data)).decode()
        print(message)
        if message['type'] == 'NEW_JOB':
            self.pool_jobs.append(message)
        self.broadcast(json.dumps(message).encode())

    def job_result(self, job_id, loss):
        """we have a job result let's go share it"""
        message = {
            'job_id': job_id,
            'loss_w': loss,
            'type': 'JOB_DONE'
        }
        self.sign_and_broadcast(message)

    def job_response(self, response):
        # it's our job ?
        if response['key'] == self.key.public_key():
            print("it's our job, nice very nice")
        self.blockchain.append(response)

    def bounty_validation(self, message):
        if 'winner' not in message or 'job_id' not in message or 'valid_until' not in self.jobs[message['job_id']] \
                or self.jobs[message['job_id']]['valid_until'] > time.time():
            print("bounty validation invalid", message)
            return False
        if message['winner'] == self.key.public_key():
            response = {
                'job_id': message['job_id'],
                'w': "results",
                'type': 'JOB_PAYLOAD'
            }
            self.sign_and_broadcast(response)

    def job_payload(self, message):
        """verify the loss w with training set, if correct credit worker, else choose next winner until found"""
        w = message['w']
        # TODO verification
        if True:
            self.user_credits[message['key']] += self.jobs[message['job_id']]['bounty']
        else:
            self.user_credits[message['key']] = 0

    def handle_message(self, s, raw_json):
        message = json.loads(raw_json)
        # message not valid
        if 'signature' not in message or 'key' not in message or 'type' not in message \
                or not self.verify_message(message):
            print("message not valid")
            self.close(s)
            return False
        type_m = message['type']
        if type_m == 'NEW_JOB':
            self.new_job(message)
        elif type_m == 'JOB_DONE':
            self.job_response(message)
        elif type_m == 'BOUNTY_VALIDATION':
            self.bounty_validation(message)
        elif type_m == 'JOB_PAYLOAD':
            self.job_payload(message)
        else:
            return False

    def broadcast(self, message):
        print("emulate sending message: ", message)

    def close(self, s):
        if s in self.outputs:
            self.outputs.remove(s)
        self.inputs.remove(s)
        s.close()
        del self.message_queues[s]

    def update(self):
        readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs, 1)
        for s in readable:
            if s is self.sock:
                connection, client_address = s.accept()
                connection.setblocking(0)
                self.inputs.append(connection)
                self.message_queues[connection] = queue.Queue()
            else:
                data = s.recv(4096)
                if data:
                    print(data)
                    self.handle_message(s, data)
                    # self.message_queues[s].put(data)
                    # if s not in self.outputs:
                    #    self.outputs.append(s)
                else:
                    self.close(s)

        for s in writable:
            try:
                next_msg = self.message_queues[s].get_nowait()
            except queue.Empty:
                self.outputs.remove(s)
            else:
                s.send(next_msg)

        for s in exceptional:
            self.inputs.remove(s)
            if s in self.outputs:
                self.outputs.remove(s)
            s.close()
            del self.message_queues[s]

    def publish_job(self, job):
        self.sign_and_broadcast(job)

    def share_job_done(self, message):
        self.sign_and_broadcast(message)
