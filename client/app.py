from flask import Flask, request
import docker_client
import psutil
import requests
import json
from blockchain_client import BlockchainClient
import time
from queue import Queue
import Message

from flask_cors import CORS


def initialize_app():
    app = Flask(__name__)
    CORS(app)  # This will enable CORS for all routes
    return app


app = initialize_app()

messaging_queue = Queue(maxsize=0)

blockchain_client = BlockchainClient(messaging_queue)
blockchain_client.start()


@app.route("/machine_stats")
def machine_stats():
    stats = {
        "cpu_percentage": psutil.cpu_percent(),
        "memory_percentage": psutil.virtual_memory().percent
    }
    return json.dumps(stats)


@app.route("/minimal_bounty/<value>", methods=["POST"])
def set_minimal_bounty(value):
    messaging_queue.put({"type": Message.MINIMAL_BOUNTY, "data": value})
    return "OK"


@app.route("/minimal_validity/<value>", methods=["POST"])
def set_minimal_validity_time(value):
    messaging_queue.put({"type": Message.SET_MINIMAL_VALIDITY, "data": value})
    return "OK"


@app.route("/max_exec/<value>", methods=["POST"])
def set_max_exec(value):
    messaging_queue.put({"type": Message.MAXIMAL_EXEC, "data": value})
    return "OK"


@app.route("/balance")
def balance():
    return json.dumps({"balance": blockchain_client.account_balance})


@app.route("/job", methods=["POST"])
def queue_job():
    message = {"type": Message.JOB_QUEUE, "data": {
        "image": request.form["url"], "valid": request.form["valid"], "bounty": request.form["bounty"]}}
    messaging_queue.put(message)
    return "OK"


@app.route("/force_quit/<id>", methods=["POST"])
def force_quit(id):
    messaging_queue.put({"type": Message.FORCE_QUIT, "data": id})
    return "OK"


@app.route("/jobs")
def get_running_jobs():
    jobs = list(
        map(lambda x: x['job'], blockchain_client.running_containers.values()))

    return json.dumps(jobs)


@app.route("/max_jobs/<value>", methods=["POST"])
def set_max_jobs(value):
    messaging_queue.put({"type": Message.MAX_JOBS, "data": value})
    return "OK"

@app.route("/stats")
def get_stats():
    return json.dumps(blockchain_client.stats)