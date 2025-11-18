import password as ps
import os
import json

config_dir = os.path.join(os.path.expanduser("~"), ".local/share/PassManager")
os.makedirs(config_dir, exist_ok=True)
vault_path = os.path.join(config_dir, "vault.json")

def cleanup():
    ps.master_password = None

def first_time():    
    salt_path = os.path.join(config_dir, "salt.bin")
    if not os.path.exists(salt_path):
        with open(salt_path, "x") as salt_file:
            ps.generate_salt()
            return True
    else:
        try:
            with open(vault_path, "r") as vault_file:
                vault_data = json.load(vault_file)
                if vault_data is None or "master" not in vault_data.get("vault", {}):
                    return True
        except (json.JSONDecodeError, FileNotFoundError):
            return True
    return False
