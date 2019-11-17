from enum import Enum
from Cryptodome.Hash import SHA256
from Cryptodome.Signature import DSS
from Cryptodome.PublicKey import ECC
import json

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
        self.signature = ""
        self.chunk_hash = ""
        self.metadata = ""
        self.data = ""
        return

    def to_json(self):
        return json.dumps({
            "type": self.type,
            "key": self.key,
            "signature": self.signature,
            "chunk_hash": self.chunk_hash,
            "metadata": self.metadata,
            "data": self.data
        })

    def from_json(self, data):
        result = json.loads(data)
        self.type = result.typ
        self.key = result.key
        self.signature = result.signature
        self.chunk_hash = result.chunk_hash
        self.metadata = result.metadata
        self.data = result.data
        return
    
    def do_crypto_shit(self, key):
        signer = DSS.new(key, 'fips-186-3')
        self.key = key.public_key
        self.chunk_hash = SHA256.new(self.to_json().encode())
        self.signature = signer.sign(self.chunk_hash)
        return