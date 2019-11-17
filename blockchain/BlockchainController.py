import queue
import select
import socket
import json
import time
import os.path
import binascii

from messages import MessageType
from Cryptodome.Hash import SHA256
from Cryptodome.Signature import DSS
from Cryptodome.PublicKey import ECC


class BlockchainController:
    def __init__(self):
        # contains active jobs
        self.pool_jobs = []
        # contains jobs done
        self.jobs_done = []
        # job_id => job
        self.jobs = {}
        # user_id => credit
        self.user_credits = {}
        # results to be verified
        self.to_check = []
        # job_id => JOB_DONE
        self.results = {}


        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 5599))
        sock.listen(50)
        self.sock = sock
        self.inputs = [sock]
        self.outputs = []
        self.message_queues = {}

        self.key = None
        self.public_key = None

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
        self.public_key = self.key.public_key().export_key(format='PEM')
        self.user_credits[self.public_key] = 100
        print("BlockchainController init end")

    def sign(self, message):
        """create signature for a message"""
        h = SHA256.new(message)
        signer = DSS.new(self.key, 'fips-186-3')
        signature = signer.sign(h)
        return signature

    def verify_message(self, message):
        """verify message integrity"""
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
        """blockchain method which add new job to pool"""
        validity = job["type"] == MessageType.NEW_JOB and job not in self.pool_jobs
        if validity:
            self.pool_jobs.append(job)

    def sign_and_broadcast(self, message):
        message['key'] = self.public_key
        data = json.dumps(message).encode()
        message['signature'] = binascii.hexlify(self.sign(data)).decode()
        if message['type'] == MessageType.NEW_JOB:
            self.pool_jobs.append(message)
            self.jobs[message['signature']] = message
        elif message['type'] == MessageType.JOB_DONE:
            self.job_response(message)
        elif message['type'] == 'WINNER':
            self.bounty_validation(message)
        elif message['type'] == MessageType.JOB_PAYLOAD:
            self.to_check.append(message)
        self.broadcast(json.dumps(message).encode())

    def job_result(self, job_id, loss):
        """we have a job result let's go share it"""
        message = {
            'job_id': job_id,
            'loss_w': loss,
            'type': MessageType.JOB_DONE
        }
        self.sign_and_broadcast(message)

    def job_response(self, response):
        """peers send us job response"""
        job_owner = self.jobs[response['job_id']]['key']
        if job_owner == self.public_key:
            print("it's our job, nice very nice")
            message = {
                'type': 'WINNER',
                'job_id': response['job_id'],
                'winner': response['key'],
            }
            self.sign_and_broadcast(message)
        self.jobs_done.append(response)

    def bounty_validation(self, message):
        """peers send us bounty validation"""
        #if 'winner' not in message or 'job_id' not in message or 'valid_until' not in self.jobs[message['job_id']]: # \
                # or self.jobs[message['job_id']]['valid_until'] > time.time(): # comment for the demo
         #   print("bounty validation invalid")
          #  return False
        if message['winner'] == self.public_key:
            response = {
                'job_id': message['job_id'],
                'w': self.results[message['job_id']]['w'],
                'image': self.jobs[message['job_id']]['data']['data'],
                'type': MessageType.JOB_PAYLOAD
            }
            self.sign_and_broadcast(response)

    def job_payload(self, message):
        """peers send us payload"""
        job = self.jobs[message['job_id']]
        message['image'] = job['data']['data']
        self.to_check.append(message)

    def handle_message(self, s, raw_json):
        """dispatch message from type and verify signature"""
        message = json.loads(raw_json)
        # message not valid
        if 'signature' not in message or 'key' not in message or 'type' not in message \
                or not self.verify_message(message):
            print("message not valid")
            self.close(s)
            return False
        type_m = message['type']
        print("BlockchainController", type_m)
        if type_m == MessageType.NEW_JOB:
            self.new_job(message)
        elif type_m == MessageType.JOB_DONE:
            self.job_response(message)
        elif type_m == MessageType.BOUNTY_VALIDATION:
            self.bounty_validation(message)
        elif type_m == MessageType.JOB_PAYLOAD:
            self.job_payload(message)
        else:
            return False

    def broadcast(self, message):
        """send data to peers, useless to implemented. Distributed algorithms already exists"""
        # self.handle_message(message)

    def share_job_done(self, message):
        self.results[message['job_id']] = message
        self.sign_and_broadcast(message)

    def publish_job(self, job):
        if self.user_credits[self.public_key] < job['data']['metadata']['bounty']:
            return
        self.user_credits[self.public_key] -= job['data']['metadata']['bounty']
        self.sign_and_broadcast(job)

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

    def close(self, s):
        if s in self.outputs:
            self.outputs.remove(s)
        self.inputs.remove(s)
        s.close()
        del self.message_queues[s]
