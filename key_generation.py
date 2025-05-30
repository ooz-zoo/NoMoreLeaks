import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from datetime import datetime
import os
import base64

def generate_key_pair():
    
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return private_bytes.hex(), public_bytes.hex()

def encrypt_private_key(priv_key_hex: str, password: str) -> tuple:
    
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    cipher = Fernet(key)
    encrypted = cipher.encrypt(priv_key_hex.encode())
    return f"{salt.hex()}:{encrypted.hex()}", salt.hex()

def process_users(input_file='gov_db.json', output_file='user_keys.json'):
    """Modified to include encryption"""
    with open(input_file) as f:
        data = json.load(f)
    
    # Generate a strong random password for batch encryption
    # In production, you'd want to use per-user passwords!
    batch_password = base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    results = []
    for user in data['ID_data']:
        priv_key, pub_key = generate_key_pair()
        
        # Encrypt the private key immediately after generation
        encrypted_priv, salt = encrypt_private_key(priv_key, batch_password)
        
        results.append({
            'name': user['Full Name'],
            'id': user['Identification_no'],
            'encrypted_private_key': encrypted_priv,  # Now encrypted!
            'public_key': pub_key,
            'key_derivation_salt': salt,
            'generated_at': datetime.now().isoformat()
            # Note: In real usage, don't store the password in the JSON!
        })
    
    os.makedirs('temp_storage', exist_ok=True)
    output_path = os.path.join('temp_storage', output_file)
    
    with open(output_path, 'w') as f:
        json.dump({'users': results,}, f, indent=2)
    
    print(f"Generated encrypted keys for {len(results)} users in {output_path}")
    print(f"⚠️ BATCH PASSWORD (KEEP SECURE): {batch_password}")

if __name__ == '__main__':
    process_users()