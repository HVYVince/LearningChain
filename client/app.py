from flask import Flask
import docker
import requests

def initialize_app():
    app = Flask(__name__)
    return app

app = initialize_app()
client = docker.from_env()

# api-endpoint 
URL = "http://maps.googleapis.com/maps/api/geocode/json"
# location given here 
location = "delhi technological university"
# defining a params dict for the parameters to be sent to the API 
PARAMS = {'address':location} 
# sending get request and saving the response as response object 
r = requests.get(url = URL, params = PARAMS) 
# extracting data in json format 
data = r.json() 
  

@app.route("/")
def hello():
    return "Hello, World!"