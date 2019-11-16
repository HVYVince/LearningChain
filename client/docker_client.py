import docker
import os
client = docker.from_env()

BASE_PATH = os.path.join(os.sep, "tmp", "learningchain")


def run_container(image: str):
    hash = image.split(":")[-1]
    directory = os.path.join(BASE_PATH, hash)
    print(f"Using directory {directory}")
    if not os.path.isdir:
        os.makedirs(directory)
    container = client.containers.run(
        image, volumes={f"{directory}": {"bind": '/tmp', 'mode': 'rw'}}, detach=True)
    return container


def get_container():
    pass


def delete(container_id):
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=1)
        client.containers.prune()  # This removes all stopped containers
    except:
        print("Container doesn't exist")


def status(container_id):
    try:
        container = client.containers.get(container_id)
        return container.status
    except:
        print("Container doesn't exist")


def retrieve_output(container_id):
    try:
        container = client.containers.get(container_id)
        return container.logs(stderr=False)
    except:
        print("Container doesn't exist")
