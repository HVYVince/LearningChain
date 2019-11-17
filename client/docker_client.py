import docker
import os
client = docker.from_env()

BASE_PATH = os.path.join(os.sep, "tmp", "learningchain")


def run_container(image: str):
    hash = "0"  # TODO extract hash
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
