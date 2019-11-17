import docker_client
from threading import Thread
import time
from queue import Queue
import Message
import socket
import os
import json


class BlockchainClient(Thread):
    def __init__(self, messaging_queue):
        super().__init__()
        self.messaging_queue = messaging_queue
        # TODO here key is id and then we have object with full container and expiration time and image_id
        self.running_containers = {}
        self.started_images = []
        self.max_exec = 3600
        self.minimal_bounty = 0
        self.minimal_validity = 10
        self.account_balance = 0
        self.max_jobs = 4
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_backend = '192.168.43.131'
        self.socket.connect((socket_backend, 5608))

    def run(self):
        print("Started blockchain client")
        while True:
            self.process_queue()
            self.retrieve_account_balance()
            self.handle_expired_containers()
            self.handle_finished_containers()
            jobs = self.find_new_jobs()

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

                model_path = os.path.join(docker_client.BASE_PATH, id, "model")
                model_file = open(model_path, 'rb')
                model_bytes = model_file.read()
                model_file.close()
                finished_output = {"type": "JOB_DONE",
                                   "loss": output, "w": model_bytes}
                self.send_message(json.dumps(finished_output))
                self.kill_container(id)

    def find_new_jobs(self):
        # TODO here it comes from the blockchain
        self.send_message(json.dumps({"type": "GET_JOBS"}))
        jobs_bytes = self.socket.recv(4096)
        jobs_json = jobs_bytes.decode()
        return json.loads(jobs_json)

    def start_new_jobs(self, jobs):
        for job in jobs:
            if len(self.running_containers.keys()) < self.max_jobs:
                image_id = job["data"]
                if image_id not in self.started_images:
                    print(
                        f"Launching new container for image {image_id} for maximum {self.max_exec} seconds")
                    self.started_images.append(image_id)
                    container = docker_client.run_container(image_id)
                    job_data = {
                        "image": image_id, "valid": job["metadata"]["valid_until"], "bounty": job["metadata"]["bounty"]}
                    self.running_containers[container.id] = {
                        "container": container, "expiration": int(time.time() + self.max_exec), "job": job_data}

    def retrieve_account_balance(self):
        print("Retrieving account balance")
        self.send_message(json.dumps({"type": "BALANCE"}))
        print("Waiting for receive balance")
        balance_bytes = self.socket.recv(4096)
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
        self.send_message(json.dumps(
            {"type": "NEW_JOB", "data": data}))
        # response = self.socket.recv(4096)  # TODO do we have a response?

    def send_message(self, message):
        self.socket.send(f"{message}\n".encode())
