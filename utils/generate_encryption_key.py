#run one time to create the encryption key, which is then saved in the .env file
#this YouTube video was helpful: https://www.youtube.com/watch?v=S-w24LtBub8 
#
# Here is the documentation: https://cryptography.io/en/latest/fernet/

from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(key)