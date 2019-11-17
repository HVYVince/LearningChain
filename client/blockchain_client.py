import docker_client
from threading import Thread
import time
from queue import Queue
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
        # TODO here key is id and then we have object with full container and expiration time and image_id
        self.running_containers = {}
        self.started_images = []
        self.max_exec = 3600
        self.minimal_bounty = 40
        self.minimal_validity = 1574561216 # in one week
        self.account_balance = 0
        self.max_jobs = 4
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_backend = '192.168.43.131'
        self.socket.connect((socket_backend, 5602))

    def run(self):
        print("Started blockchain client")
        while True:
            self.process_queue()
            self.retrieve_account_balance()
            self.handle_expired_containers()
            self.handle_finished_containers()
            jobs = self.find_new_jobs()
            print(jobs)
            if len(jobs) > 0:
                self.start_new_jobs(jobs)

            time.sleep(1)

    def handle_expired_containers(self):
        print("handle expired")
        to_delete = list(filter(lambda key: self.running_containers[key]['expiration'] < time.time(
        ), self.running_containers.keys()))
        for id in to_delete:
            self.kill_container(id)

    def handle_finished_containers(self):
        running_ids = list(self.running_containers.keys())
        for id in running_ids:
            status = docker_client.status(id)
            if status == 'exited':
                output = docker_client.retrieve_output(id).decode()
                print(f"Output was {output}")
                image_hash = self.running_containers[id]["job"]["image"].split(":")[-1]
                model_path = os.path.join(docker_client.BASE_PATH, image_hash, "model")
                model_file = open(model_path, 'rb')
                model_bytes = binascii.hexlify(model_file.read()).decode()
                model_file.close()
                finished_output = {"type": "JOB_DONE",
                                   "loss": output, "w": model_bytes}
                self.send_message(json.dumps(finished_output))
                self.kill_container(id)

    def find_new_jobs(self):
        self.send_message(json.dumps({"type": "GET_JOBS"}))
        jobs_bytes = self.receive_message_bytes()
        jobs_json = jobs_bytes.decode()
        jobs = list(map(lambda x: x['data'],json.loads(jobs_json)))

        jobs = list(filter(lambda job: job['metadata']["valid_until"] >= self.minimal_validity and job['metadata']['bounty'] >= self.minimal_bounty, jobs))

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
        for job in jobs:
            if len(self.running_containers.keys()) < self.max_jobs:
                image_id = job["data"]
                if image_id not in self.started_images:
                    print(
                        f"Launching new container for image {image_id} for maximum {self.max_exec} seconds")
                    self.started_images.append(image_id)
                    print(image_id)
                    container = docker_client.run_container(image_id)
                    job_data = {
                        "image": image_id, "valid": job["metadata"]["valid_until"], "bounty": job["metadata"]["bounty"]}
                    self.running_containers[container.id] = {
                        "container": container, "expiration": int(time.time() + self.max_exec), "job": job_data}

    def retrieve_account_balance(self):
        print("Retrieving account balance")
        self.send_message(json.dumps({"type": "BALANCE"}))
        print("Waiting for receive balance")
        balance_bytes = self.receive_message_bytes()
        print("Received")
        balance_json = balance_bytes.decode()
        self.account_balance = json.loads(balance_json)["balance"]
        print(f"Account balance {self.account_balance}")

    def kill_container(self, id):
        self.running_containers.pop(id, None)
        docker_client.delete(id)

    def process_queue(self):
        while not self.messaging_queue.empty():
            msg = self.messaging_queue.get(block=True)
            self.process_message(msg)

    def process_message(self, msg):
        print(f"MESSAGE: {msg}")
        if msg["type"] == Message.MAXIMAL_EXEC:
            self.max_exec = msg["data"]
        elif msg["type"] == Message.FORCE_QUIT:
            container_id = msg["data"]
            self.kill_container(container_id)
        elif msg["type"] == Message.MINIMAL_BOUNTY:
            self.max_exec = msg["data"]
        elif msg["type"] == Message.SET_MINIMAL_VALIDITY:
            self.minimal_validity = msg['data']
        elif msg["type"] == Message.JOB_QUEUE:
            self.submit_new_job(msg["data"])
        elif msg["type"] == Message.MAX_JOBS:
            self.max_jobs = msg['data']
        else:
            print("Message not recognized")

    def submit_new_job(self, data):
        print(f"New job {data}")
        job = {
            "data": data["image"],
            "metadata": {"valid_until": int(data["valid"]), "bounty": int(data["bounty"])}
        }
        self.send_message(json.dumps(
            {"type": "NEW_JOB", "data": job}))

    def send_message(self, message):
        message = f"{message}\n".encode()
        size = len(message)
        print(f"Message length: {size}")
        size = struct.pack("!i", size)
        self.socket.send(size + message)
