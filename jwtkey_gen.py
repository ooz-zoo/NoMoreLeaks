from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def generate_key_pair():
    """Generate Ed25519 keys in both hex and PEM formats."""
    try:
    
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        
        public_hex = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()

        # Generate PEM versions (for JWT)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    
        print(f"\nHEX FORMAT (for claim verification):")
        print(f"PUBLIC_KEY:  {public_hex}")
        
        print(f"\nPEM FORMAT (for JWT signing):")
        print(f"JWT_PRIVATE_KEY:\n{private_pem}")
        print(f"JWT_PUBLIC_KEY:\n{public_pem}")

        return {
            'pem': {'private': private_pem, 'public': public_pem}
        }

    except Exception as e:
        print(f"❌ Key generation failed: {e}")
        raise

if __name__ == "__main__":
    generate_key_pair()