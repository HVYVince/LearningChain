from enum import Enum

class MessageType(Enum):
    NEW_JOB = 1
    JOB_DONE = 2
    BOUNTY_VALIDATION = 3
    JOB_PAYLOAD = 4

class Message:
    def __init__(self, typ):
        super().__init__()
        self.type = typ
        self.key = ""
        self.job_hash = ""
        self.metadata = ""
        self.data = ""
        return

    def to_json(self):
        json = '{"type":' + self.type
        json += ',"key":' + self.key
        json += ',"job_hash":' + self.job_hash
        json += ',"metadata":' + self.metadata
        json += ',"data":' + self.data
        json += '}'
        return

    def from_json(self, json):
        json = json[1:-1].replace('"', "")
        json = dict(json.split(":") for item in json.split(","))
        self.type = json["type"]
        self.key = json["key"]
        self.job_hash = json["job_hash"]
        self.metadata = json["metadata"]
        self.data = json["data"]
        return