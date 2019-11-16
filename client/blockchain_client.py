import docker_client
from threading import Thread
import time


class BlockchainClient:
    def __init__(self):
        super().__init__()
        self.running_containers = {}
        self.max_exec = 20

    def run(self):
        print("Started blockchain client")
        while True:
            to_delete = filter(lambda x: self.running_containers[x] < time.time(
            ), self.running_containers.keys())

            for id in to_delete:
                print(f"Found {id} to delete")
                self.running_containers.pop(id, None)
                docker_client.delete(id)

            if len(self.running_containers) == 0:
                print("No more containers, launching")
                container = docker_client.run_container(
                    "matoran/lauzhack_knn_5", "adf87ac9ceae206e19f190132ab296cdf13d1df427384a96f9a3b20db6c11ee2")
                container_expiration = time.time() + self.max_exec
                self.running_containers[f"{container.id}"] = container_expiration
                print(f"Launched {container.id}")

            time.sleep(10)
