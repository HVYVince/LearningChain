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
    f.close()
    f = open('myprivatekey.pem', 'wt')
    f.write(key.export_key(format='PEM'))
    f.close()
else:
    print("reading existing key")
    f = open('myprivatekey.pem', 'rt')
    key = ECC.import_key(f.read())
    f.close()

h = SHA256.new("message".encode())
signer = DSS.new(key, 'fips-186-3')
signature = signer.sign(h)


h = SHA256.new("message".encode())
verifier = DSS.new(key.public_key(), 'fips-186-3')
try:
    verifier.verify(h, signature)
    print("The message is authentic.")
except ValueError:
    print("The message is not authentic.")
