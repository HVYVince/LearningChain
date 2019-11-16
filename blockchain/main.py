import socket
import json
import time
import os.path
from Cryptodome.Hash import SHA256
from Cryptodome.Signature import DSS
from Cryptodome.PublicKey import ECC

key = None

if not os.path.exists('myprivatekey.pem'):
    print("creating new ECC private key")
    key = ECC.generate(curve='P-256')
    f = open('mypublickey.pem', 'wt')
    f.write(key.public_key().export_key(format='PEM'))
    f = open('myprivatekey.pem', 'wt')
    f.write(key.export_key(format='PEM'))
    f.close()
else:
    print("reading existing key")
    f = open('myprivatekey.pem', 'rt')
    key = ECC.import_key(f.read())
    f.close()


pool_jobs = []
blockchain = []
jobs = {}
user_credits = {}
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind(('', 5599))


def sign(message):
    h = SHA256.new(message)
    signer = DSS.new(key, 'fips-186-3')
    signature = signer.sign(h)
    return signature


def verify_message(message):
    signature = message['signature']
    del message['signature']
    h = SHA256.new(message.encode())
    verifier = DSS.new(message['key'], 'fips-186-3')
    try:
        verifier.verify(h, signature)
        return True
    except ValueError:
        return False


def new_job(job):
    if job not in pool_jobs:
        pool_jobs.append(job)

    # TODO should try this job ? From which data ?
    do_job()


def do_job():
    pass


def sign_and_broadcast(message):
    message['key'] = key.public_key()
    data = json.dumps(message).encode()
    message['signature'] = sign(data)
    broadcast(json.dumps(message).encode())


def job_result(job_id, loss):
    """we have a job result let's go share it"""
    message = {
        'job_id': job_id,
        'loss_w': loss,
        'type': 'JOB_DONE'
    }
    sign_and_broadcast(message)


def job_response(response):
    # it's our job ?
    if response['key'] == key.public_key():
        print("it's our job, nice very nice")
    blockchain.append(response)


def bounty_validation(message):
    if 'winner' not in message or 'job_id' not in message or 'valid_until' not in jobs[message['job_id']] \
            or jobs[message['job_id']]['valid_until'] > time.time():
        print("bounty validation invalid", message)
        return False
    if message['winner'] == key.public_key():
        response = {
            'job_id': message['job_id'],
            'w': "results",
            'type': 'JOB_PAYLOAD'
        }
        sign_and_broadcast(response)


def job_payload(message):
    """verify the loss w with training set, if correct credit worker, else choose next winner until found"""
    w = message['w']
    # TODO verification
    if True:
        user_credits[message['key']] += jobs[message['job_id']]['bounty']
    else:
        user_credits[message['key']] = 0


def receive_message(raw_json):
    message = json.loads(raw_json)
    # message not valid
    if 'signature' not in message or 'key' not in message or 'type' not in message or not verify_message(message):
        print("message not valid")
        return False
    type_m = message['type']
    if type_m == 'NEW_JOB':
        new_job(message)
    elif type_m == 'JOB_DONE':
        job_response(message)
    elif type_m == 'BOUNTY_VALIDATION':
        bounty_validation(message)
    elif type_m == 'JOB_PAYLOAD':
        job_payload(message)
    else:
        return False


def broadcast(message):
    print("emulate sending message: ", message)


while True:
    socket.listen(10)
    client, address = socket.accept()
    raw = client.recv(4096)
    receive_message(raw)
