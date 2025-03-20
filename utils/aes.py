import re

from Cryptodome.Cipher import AES
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import settings

SECRET_KEY = bytes.fromhex(settings.AES_SECRET_KEY)

# AES Encryption (GCM Mode)
def encrypt_password(password: str) -> str:
    cipher = AES.new(SECRET_KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    encrypted_data = cipher.nonce + tag + ciphertext
    return base64.b64encode(encrypted_data).decode()


# AES Decryption
def decrypt_password(encrypted_password: str) -> str:
    encrypted_data = base64.b64decode(encrypted_password)
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]

    cipher = AES.new(SECRET_KEY, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()


# Password Verification
def verify_password(input_password: str, encrypted_password: str) -> bool:
    try:
        return decrypt_password(encrypted_password) == input_password
    except ValueError:
        return False


SALT = os.urandom(16)

def derive_key(secret_key, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(secret_key)

def encrypt_token(token):
    key = derive_key(SECRET_KEY, SALT)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Ensure token length is a multiple of 16 (AES block size)
    token = token.ljust(112)
    encrypted_token = encryptor.update(token.encode()) + encryptor.finalize()

    # Encode to base64, then remove special characters
    encoded_token = base64.b64encode(iv + encrypted_token).decode()
    sanitized_token = re.sub(r'[^a-zA-Z0-9]', '', encoded_token)  # Remove special characters

    return sanitized_token

