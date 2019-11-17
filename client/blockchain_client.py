import docker_client
from threading import Thread
import time
import Message
import socket
import os
import json

import binascii
import struct


class BlockchainClient(Thread):
    def __init__(self, messaging_queue):
        super().__init__()
        self.messaging_queue = messaging_queue
        self.running_containers = {}
        self.started_images = []
        self.max_exec = 3600
        self.minimal_bounty = 0
        self.minimal_validity = 1573957786
        self.account_balance = 0
        self.max_jobs = 4
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_backend = '127.0.0.1'
        self.socket.connect((socket_backend, 5602))
        self.stats = {}

    def run(self):
        print("Started blockchain client")
        while True:
            self.process_queue()
            self.retrieve_account_balance()
            self.retrieve_stats()
            self.check_validations()
            self.handle_expired_containers()
            self.handle_finished_containers()
            jobs = self.find_new_jobs()
            if len(jobs) > 0:
                self.start_new_jobs(jobs)

            time.sleep(1)

    def check_validations(self):
        self.send_message(json.dumps({"type": "CHECK"}))
        validations_bytes = self.receive_message_bytes()
        validations = json.loads(validations_bytes.decode())
        print("VALIDATIONS", validations)
        for validation in validations:
            self.validate(validation)

    def validate(self, validation):
        output = docker_client.run_validation(validation)
        self.send_message(json.dumps({"type": "VALIDATE", "loss": output.decode()}))

    def retrieve_stats(self):
        self.send_message(json.dumps({"type": "STATS"}))
        stats_bytes = self.receive_message_bytes()
        self.stats = json.loads(stats_bytes.decode())

    def handle_expired_containers(self):
        print("handle expired")
        to_delete = list(filter(lambda key: self.running_containers[key]['expiration'] < time.time(
        ), self.running_containers.keys()))
        for signature in to_delete:
            print("EXPIRED", signature, self.running_containers[signature]['expiration'])
            self.kill_container(signature)

    def handle_finished_containers(self):
        print("CHECKING FINISHING", self.running_containers)
        running_ids = list(self.running_containers.keys())
        for signature in running_ids:
            data = self.running_containers[signature]
            container_id = data['container_id']
            status = docker_client.status(container_id)
            print("STATUS",status)
            if status == 'exited':
                output = docker_client.retrieve_output(container_id).decode()
                print(f"Output was {output}")
                model_path = os.path.join(docker_client.BASE_PATH, signature, "model")
                model_file = open(model_path, 'rb')
                model_bytes = binascii.hexlify(model_file.read()).decode()
                model_file.close()
                finished_output = {"type": "JOB_DONE",
                                   "job_id": signature,
                                   "loss": output, "w": model_bytes}
                print("FINISHED ", finished_output["job_id"])
                self.send_message(json.dumps(finished_output))
                self.kill_container(signature)

    def find_new_jobs(self):
        self.send_message(json.dumps({"type": "GET_JOBS"}))
        jobs_bytes = self.receive_message_bytes()
        jobs_json = jobs_bytes.decode()
        jobs = json.loads(jobs_json)
        jobs = list(filter(
            lambda job: job['data']['metadata']["valid_until"] >= self.minimal_validity and job['data']['metadata'][
                'bounty'] >= self.minimal_bounty, jobs))

        return jobs

    def receive_message_bytes(self):
        data = self.socket.recv(4)
        if data:
            size = struct.unpack("!i", data[:4])[0]
            buffer = data[4:]
            size -= len(buffer)
            while size > 0:
                data = self.socket.recv(min(size, 4096))
                buffer += data
                size -= len(data)
            return buffer

    def start_new_jobs(self, jobs):
        for full_job in jobs:
            print(f"MAX_JOBS: {self.max_jobs}")
            if len(self.running_containers.keys()) < self.max_jobs:
                job = full_job['data']
                image_id = job["data"]
                if image_id not in self.started_images:
                    print(
                        f"Launching new container for image {image_id} for maximum {self.max_exec} seconds")
                    self.started_images.append(image_id)
                    print(image_id)
                    container = docker_client.run_container(image_id, full_job["signature"])
                    job_data = {
                        "image": image_id, "valid": job["metadata"]["valid_until"], "bounty": job["metadata"]["bounty"]}
                    self.running_containers[full_job['signature']] = {
                        "container": container, "expiration": int(time.time() + self.max_exec), "job": full_job,
                        "container_id": container.id}

    def retrieve_account_balance(self):
        print("Retrieving account balance")
        self.send_message(json.dumps({"type": "BALANCE"}))
        print("Waiting for receive balance")
        balance_bytes = self.receive_message_bytes()
        print("Received")
        balance_json = balance_bytes.decode()
        self.account_balance = json.loads(balance_json)["balance"]
        print(f"Account balance {self.account_balance}")

    def kill_container(self, signature):
        data = self.running_containers.pop(signature, None)
        id = data["container_id"]
        docker_client.delete(id)

    def process_queue(self):
        while not self.messaging_queue.empty():
            msg = self.messaging_queue.get(block=True)
            self.process_message(msg)

    def process_message(self, msg):
        print(f"MESSAGE: {msg}")
        if msg["type"] == Message.MAXIMAL_EXEC:
            self.max_exec = int(msg["data"])
        elif msg["type"] == Message.FORCE_QUIT:
            signature = msg["data"]
            self.kill_container(signature)
        elif msg["type"] == Message.MINIMAL_BOUNTY:
            self.minimal_bounty = int(msg["data"])
        elif msg["type"] == Message.SET_MINIMAL_VALIDITY:
            self.minimal_validity = int(time.time()) + int(msg['data'])
        elif msg["type"] == Message.JOB_QUEUE:
            self.submit_new_job(msg["data"])
        elif msg["type"] == Message.MAX_JOBS:
            self.max_jobs = int(msg['data'])
        else:
            print("Message not recognized")

    def submit_new_job(self, data):
        job = {
            "data": data["image"],
            "metadata": {"valid_until": int(data["valid"]), "bounty": int(data["bounty"])}
        }
        print(f"New job {job}")
        self.send_message(json.dumps(
            {"type": "NEW_JOB", "data": job}))

    def send_message(self, message):
        message = f"{message}\n".encode()
        size = len(message)
        print(f"Message length: {size}")
        size = struct.pack("!i", size)
        self.socket.send(size + message)
