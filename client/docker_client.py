import docker
import os
import binascii

client = docker.from_env()

BASE_PATH = os.path.join(os.sep, "tmp", "learningchain")


def run_container(image: str, signature: str):
    directory = os.path.join(BASE_PATH, signature)
    print(f"Using directory {directory}")
    if not os.path.isdir(directory):
        os.makedirs(directory)
    container = client.containers.run(
        image, volumes={f"{directory}": {"bind": '/tmp', 'mode': 'rw'}}, detach=True)
    return container


def get_container():
    pass


def run_validation(validation):
    print("VALIDATION RUNNING", validation)
    directory = os.path.join(BASE_PATH, validation["signature"])
    w = validation["w"]
    w_bytes = binascii.unhexlify(w.encode())
    if not os.path.isdir(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, "model"), 'wb') as file:
        file.write(w_bytes)

    output = client.containers.run(
        validation["image"], volumes={f"{directory}": {"bind": '/tmp', 'mode': 'rw'}},
        environment={"VALIDATION": "VALIDATION"})
    return output


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
