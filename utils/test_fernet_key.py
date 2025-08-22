# I am having trouble getting the Fernal key loaded from an environment variable to work.
# The environment variable comes in as a string, but the key needs to be a particular type of binary array.
# pip install cryptography

import os
from cryptography.fernet import Fernet
import base64

#how I generated the one time key that I then saved as an environment variable
#key = Fernet.generate_key()
#print(key)

#when I run it like this, it works fine
#key = b'MHuprJOChSGfpDw_kKpVs4QxGqsrFqaVwJT-y1TSwBk='
#print(key)
#crypt_obj = Fernet(key)

# #when I run it like this, loading the key from my .env file, it doesn't work as it says "ValueError: Fernet key must be 32 url-safe base64-encoded bytes."
#key = os.environ.get('FERNET_KEY').encode()
#print(key)
#crypt_obj = Fernet(key)

# #so I've tried a bunch of variations to try to cast it properly, but I cannot get it working.  Here is one of these variations, which gets the error "binascii.Error: Incorrect padding"
# key_str = os.environ.get('FERNET_KEY').encode()
# key = base64.urlsafe_b64encode(key_str.ljust(32)[:32])
# print(key)
# crypt_obj = Fernet(key)

#These posts are relevant to the issue, although I cannot get it to work properly.
# https://stackoverflow.com/questions/68141153/how-to-convert-string-to-use-with-fernet-in-python
# https://stackoverflow.com/questions/63154775/fernet-key-error-fernet-key-must-be-32-url-safe-base64-encoded-bytes

key = os.environ.get('FERNET_KEY')
byte_key = key.encode()
print(byte_key)
crypt_obj = Fernet(key)
print("crypt object created")
