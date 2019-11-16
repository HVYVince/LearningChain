from flask import Flask
import docker_client
import psutil
import requests
import json
from blockchain_client import BlockchainClient


def initialize_app():
    app = Flask(__name__)
    return app


app = initialize_app()

blockchain_client = BlockchainClient()
blockchain_client.run()

settings = {
    "minimal_bounty" : 0,
    "minimal_validity_time" : 0,
    "maximal_time" : 0,
    "maximal_cpu" : 0
}


@app.route("/")
def hello():
    container = docker_client.run_container(
        "matoran/lauzhack_knn_5", "b61e1bcb6353650e44575390812bc237be1c17ec06e974745b1bf380aa4dd94e")
    return container.id


@app.route("/machine_stats")
def machine_stats():
    stats = {
        "cpu_percentage": psutil.cpu_percent(),
        "memory_percentage": psutil.virtual_memory().percent
    }
    return json.dumps(stats)


@app.route("/minimal_bounty", methods=["POST"])
def set_minimal_bounty():
    settings["minimal_bounty"] = app.request.form.get('bounty')
    return "ok"


@app.route("/minimal_time", methods=["POST"])
def set_minimal_time():
    settings["minimal_validity_time"] = app.request.form.get('minimal_time')
    return "ok"


@app.route("/max_exec", methods=["POST"])
def set_max_exec():
    settings["minimal_bounty"] = app.request.form.get('ma')
    return "ok"


@app.route("/balance")
def balance():
    # TODO query hyperledger REST
    return "NOT IMPLEMENTED"


@app.route("/job", methods=["POST"])
def queue_job():
    # TODO
    return "NOT IMPLEMENTED"


@app.route("/force_quit/:id", methods=["POST"])
def force_quit(id):
    # TODO
    return "NOT IMPLEMENTED"
