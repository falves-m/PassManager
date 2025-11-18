import password as ps
import os
import json

def cleanup():
    ps.master_password = None

def first_time():
    if not os.path.exists("salt.bin"):
        with open("salt.bin", "x") as salt_file:
            ps.generate_salt()
            return True
    else:
        try:
            with open("vault.json", "r") as vault_file:
                vault_data = json.load(vault_file)
                if vault_data is None or "master" not in vault_data.get("vault", {}):
                    return True
        except (json.JSONDecodeError, FileNotFoundError):
            return True
    return False
