import jwt
import requests
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError
from app.core.config import settings

security = HTTPBearer()

class ClerkJWTValidator:
    def __init__(self):
        self.jwks_url = f"{settings.CLERK_JWT_ISSUER}/.well-known/jwks.json" if settings.CLERK_JWT_ISSUER else None
        self.jwks = None

    def get_jwks(self):
        if not self.jwks and self.jwks_url:
            try:
                response = requests.get(self.jwks_url)
                response.raise_for_status()
                self.jwks = response.json()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch Clerk JWKS: {str(e)}"
                )
        return self.jwks

    def verify_token(self, token: str) -> dict:
        if not settings.CLERK_JWT_ISSUER:
            # Fallback for development/testing if issuer is not set
            return {"sub": "dummy_clerk_user_id", "role": "worker"}
            
        jwks = self.get_jwks()
        try:
            unverified_header = jwt.get_unverified_header(token)
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )

        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if rsa_key:
            try:
                # Clerk JWTs are signed with RS256
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=None, # Clerk JWTs may not have standard aud or aud varies
                    issuer=settings.CLERK_JWT_ISSUER
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            except jwt.InvalidTokenError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token signature: {str(e)}"
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate public key to verify signature"
        )

clerk_validator = ClerkJWTValidator()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    return clerk_validator.verify_token(token)
