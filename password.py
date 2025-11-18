import json
import os
import secrets
import base64
from os import urandom
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

sites = []
master_password = None  # Stores the verified master password (plain text)

def init_vault():
    if os.path.exists("vault.json"):
        with open("vault.json") as vault_file:
            data = json.load(vault_file)

        for site in data["vault"]:
            if site != "master":
                sites.append(site)

def add_to_vault(site: str, password: str) -> bool:
    vault_data = {"vault": {}}
    
    if os.path.exists("vault.json"):
        with open("vault.json", "r") as vault_file:
            vault_data = json.load(vault_file)

    if site in vault_data["vault"]:
        return False

    vault_data["vault"][site] = password

    with open("vault.json", "w") as vault_file:
        json.dump(vault_data, vault_file, indent=4)
        return True


def generate_salt():
    salt = urandom(16)
    with open("salt.bin", "wb") as salt_file:
        salt_file.write(salt)
    return salt

def load_salt():
    with open("salt.bin", "rb") as f:
        return f.read()

def password_to_fernet_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def generate_password() -> str:
    salt = load_salt()
    key = password_to_fernet_key(get_master_password(), salt)
    cipher = Fernet(key)
    random_bytes = secrets.token_bytes(16)
    password = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    token = cipher.encrypt(password.encode())
    return token.decode()


def get_master_password():
    global master_password
    if master_password is not None:
        return master_password
    with open("vault.json", "r") as vault_file:
        vault_data = json.load(vault_file)
        return vault_data["vault"]["master"]

def get_password_from_vault(site: str) -> str:
    with open("vault.json", "r") as vault_file:
        vault_data = json.load(vault_file)
        if site == "master":
            return vault_data["vault"]["master"]
        salt = load_salt()
        key = password_to_fernet_key(get_master_password(), salt)
        cipher = Fernet(key)
        password = cipher.decrypt(vault_data["vault"][site].encode())
        return password.decode()

def hash_master_password(password: str) -> str:
    ph = PasswordHasher()
    hashed_password = ph.hash(password)
    return hashed_password

def check_master_password(password: str, hashed_password: str) -> bool:
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False