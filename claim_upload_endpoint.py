import os
import jwt
import time
import uuid
import json
import base64
import binascii
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import HTTPException, Request
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates



app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        
        "Referrer-Policy": "strict-origin-when-cross-origin"
    })
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],   
    allow_methods=["*"],  
    allow_headers=["*"],
    allow_credentials=True 
)



private_key_pem = os.getenv('JWT_PRIVATE_KEY')
private_key = serialization.load_pem_private_key(
    private_key_pem.encode(),
    password=None
)

if isinstance(private_key, ed25519.Ed25519PrivateKey):
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
else:
    raise ValueError("Private key is not an Ed25519 key")
HEX_PUBLIC_KEY = os.getenv('JWT_PUBLIC_KEY')
PUBLIC_KEY = Ed25519PublicKey.from_public_bytes(binascii.unhexlify(HEX_PUBLIC_KEY))

if not private_key or not PUBLIC_KEY:
    raise RuntimeError("JWT keys not found in environment variables")

class VerificationResult(BaseModel):
    status: str
    issuer: str
    verified_claims: list[str]
    error: str = None
    jwt_token: str = None  # Will contain signed JWT if verification succeeds

@app.post("/verify-claim", response_model=VerificationResult)
async def verify_claim(file: UploadFile = File(...)):
    try:
        print("\n=== Starting claim verification ===")
        
        contents = await file.read()
        print(f"Received file contents (first 200 chars):\n{contents[:200]}...") 
        
        claim_data = json.loads(contents)
        print("\nParsed JSON structure:")
        print(json.dumps(claim_data, indent=2))

        # Structural Validation
        print("\nValidating structure...")
        if not all(key in claim_data for key in ["signature", "data"]):
            error_msg = "Missing required fields: 'signature' or 'data'"
            print(f"Validation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
        required_data_fields = ["name", "id", "issued_by", "public_key", "expires_at"]
        if not all(key in claim_data["data"] for key in required_data_fields):
            missing = [f for f in required_data_fields if f not in claim_data["data"]]
            error_msg = f"Missing required data fields: {missing}"
            print(f"Validation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Check expiration
        print("\nChecking expiration...")
        expires_at = datetime.fromisoformat(claim_data["data"]["expires_at"])
        current_time = datetime.now(timezone.utc)
        print(f"Current time: {current_time.isoformat()}")
        print(f"Expires at: {expires_at.isoformat()}")
        
        if current_time > expires_at:
            error_msg = f"Claim expired on {expires_at}"
            print(f"Verification failed: {error_msg}")
            return {
                "status": "expired",
                "issuer": "",
                "verified_claims": [],
                "error": error_msg
            }

        # Cryptographic Verification
        print("\nVerifying signature...")
        try:
            public_key_bytes = bytes.fromhex(claim_data["data"]["public_key"])
            print(f"Public key bytes length: {len(public_key_bytes)}")
            
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            print("Public key loaded successfully")
            
            signature = base64.b64decode(claim_data["signature"])
            print(f"Signature length: {len(signature)} bytes")
            
            public_key.verify(
                signature,
                json.dumps(claim_data["data"], sort_keys=True).encode()
            )
            print("✓ Signature verified successfully")
        except (InvalidSignature, ValueError) as e:
            error_msg = f"Signature verification failed: {str(e)}"
            print(f"Verification failed: {error_msg}")
            return {
                "status": "invalid",
                "issuer": "",
                "verified_claims": [],
                "error": error_msg
            }

        # Prepare verified data
        data = claim_data["data"]
        verified_claims = [
            f"Name: {data['name']}",
            f"ID: {data['id']}",
            f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ]
        print("\nVerified claims:")
        for claim in verified_claims:
            print(f"- {claim}")

        # Create JWT payload
        jwt_payload = {
            "sub": data['id'],
            "name": data['name'],
            "iss": data['issued_by'],
            "iat": int(time.time()),
            "exp": int(time.time()) + 129600,  
            "public_ver_key": HEX_PUBLIC_KEY,
            "original_claim": data
        }
        print("\nJWT payload to be signed:")
        print(json.dumps(jwt_payload, indent=2))

        # Sign JWT with private key
        jwt_token = jwt.encode(
            jwt_payload,
            private_key,
            algorithm="EdDSA"
        )
        print("\nGenerated JWT token:")
        print(jwt_token)
        print(f"Token length: {len(jwt_token)} characters")

        # Return verification result with JWT token
        response_data = {
            "status": "verified",
             "issuer": data["issued_by"],
             "verified_claims": verified_claims
}

        response = JSONResponse(content=response_data)
        response.set_cookie(
        key="badge_token",
        value=jwt_token,
        httponly=True,
        secure=True,  # Enable in production
        samesite="none",
        max_age=86400,
        path="/",
    )
        print("\n=== Verification completed successfully ===")
        print(f"JWT stored in secure cookie, not response body")
        return response

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON file: {str(e)}"
        print(f"\nError: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except ValueError as e:
        if "Invalid isoformat string" in str(e):
            error_msg = f"Invalid timestamp format: {claim_data['data'].get('expires_at', 'MISSING')}"
            print(f"\nError: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        print(f"\nValue error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/badge")
async def get_badge(request: Request):
    """Secure badge endpoint using HTTP-only cookie"""
    try:
        
        token = request.cookies.get("badge_token")
        if not token:
            raise HTTPException(status_code=401, detail="Missing authentication cookie")

        
        try:
            
            decoded = jwt.decode(
                token,
                options={"verify_signature": False}  
            )
            
            # 3. Return minimal sanitized data
            return {
                "badge_id": f"B-{uuid.uuid4()}",  
                "name": decoded["name"],
                "issued_by": "GhostID Verifier",
                "issued_on": decoded["iat"],  # Unix timestamp
                "expires_on": decoded["exp"],
                
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Session expired")
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid session")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
