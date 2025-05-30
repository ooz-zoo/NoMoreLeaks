import json
import random
import base64
import os
from datetime import datetime, timedelta, UTC
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

# --- Helper Functions ---
def load_json(file_path: str) -> dict:
    with open(file_path, "r") as f:
        return json.load(f)

def decrypt_private_key(encrypted_key: str, password: str, salt_hex: str) -> str:
    
    
    salt = bytes.fromhex(salt_hex)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    cipher = Fernet(key)
    _, enc_hex = encrypted_key.split(":") 
    decrypted = cipher.decrypt(bytes.fromhex(enc_hex)).decode()
    
    
    return decrypted

def sign_data(private_key_hex: str, message: str) -> str:
  
    
    signing_key = ed25519.Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(private_key_hex)
    )
    signature = base64.b64encode(signing_key.sign(message.encode())).decode()
    
    
    return signature


def generate_signed_claim(temp_storage_path: str, gov_db_path: str, batch_password: str) -> dict:
    
    
    temp_data = load_json(temp_storage_path)
    temp_users = temp_data["users"]  # <- Extract the "users" list
    gov_users = load_json(gov_db_path)["ID_data"]
    
    user_temp = random.choice(temp_users)
    user_id = user_temp["id"]

    
    user_gov = next(u for u in gov_users if u["Identification_no"] == user_id)
    print(f"User Full Name: {user_gov['Full Name']}")

    # Prepare claim data
    claim_data = {
        "id": user_id,
        "name": user_gov["Full Name"],
        "dob": user_gov["Date of Birth"],
        "issued_by": f"Department of Motor Vehicles, {user_gov['issuing_state']}",
        "expires_at": (datetime.now(UTC) + timedelta(hours=24)).isoformat(),
        "public_key": user_temp["public_key"]
    }
    print("\n=== Claim Data (To Be Signed) ===")
    print(json.dumps(claim_data, indent=2))

    # Decrypt and sign
    priv_key = decrypt_private_key(
        user_temp["encrypted_private_key"],
        batch_password,
        user_temp["key_derivation_salt"]
    )
    signature = sign_data(priv_key, json.dumps(claim_data, sort_keys=True))

    return {
        "data": claim_data,
        "signature": signature
    }


if __name__ == "__main__":
    print("===== STARTING SIGNING PROCESS =====")
    signed_claim = generate_signed_claim(
        temp_storage_path= r"temp_storage\user_keys.json",
        gov_db_path="gov_db.json",
        batch_password=os.environ.get('env_var')
    )
    
    print("\n=== FINAL SIGNED CLAIM ===")
    print(json.dumps(signed_claim, indent=2))
