import docker_client
from threading import Thread
import time
from queue import Queue
import Message


class BlockchainClient(Thread):
    def __init__(self, messaging_queue):
        super().__init__()
        self.messaging_queue = messaging_queue
        # TODO here key is id and then we have object with full container and expiration time and image_id
        self.running_containers = {}
        self.started_images = []
        self.max_exec = 20
        self.minimal_bounty = 0
        self.minimal_validity = 10  # TODOO to set
        self.account_balance = 0

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
        to_delete = list(filter(lambda x: self.running_containers[x]['expiration'] < time.time(
        ), self.running_containers.keys()))
        for id in to_delete:
            self.kill_container(id)

    def handle_finished_containers(self):
        print(self.running_containers)
        pass

    def find_new_jobs(self):
        # TODO return new jobs from blockchain with filters from parameters
        return [{"image": "matoran/lauzhack_knn_5@sha256:6520a3942ac2e2c91ab747a22c5d748b7f2e3acbd4414aa5867d752c5d60fb10"}]

    def start_new_jobs(self, jobs):
        for job in jobs:
            image_id = job["image"]
            if image_id not in self.started_images:  # TODO perhaps should we check full with the hash as well
                print(f"Launching new container for image {image_id}")
                self.started_images.append(image_id)
                container = docker_client.run_container(image_id)
                self.running_containers[container.id] = {
                    "container": container, "expiration": time.time() + self.max_exec}

    def retrieve_account_balance(self):
        # TODO retrieve account balance
        self.account_balance = 0

    def kill_container(self, id):
        self.running_containers.pop(id, None)
        docker_client.delete(id)

    def process_queue(self):
        while not self.messaging_queue.empty():
            msg = self.messaging_queue.get(block=True)
            self.process_message(msg)

    def process_message(self, msg):
        if msg["type"] == Message.MAXIMAL_EXEC:
            self.max_exec = msg["data"]
        elif msg["type"] == Message.FORCE_QUIT:
            container_id = msg["data"]
            self.kill_container(container_id)
        elif msg["type"] == Message.MINIMAL_BOUNTY:
            self.max_exec = msg["data"]
        elif msg["type"] == Message.SET_MINIMAL_VALIDITY:
            self.minimal_validity = msg['data']
        else:
            print("Message not recognized")
