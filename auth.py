from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from models import User
from azure.identity import DefaultAzureCredential
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key-for-local-dev")
ALGORITHM = "HS256"
AZURE_AD_TENANT_ID = os.getenv("AZURE_AD_TENANT_ID", "your-tenant-id")
AZURE_AD_CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID", "your-client-id")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}/oauth2/v2.0/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], 
                           options={"verify_aud": True, "aud": AZURE_AD_CLIENT_ID})
        username: str = payload.get("preferred_username")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_data = {"id": payload.get("sub"), "username": username, "role": "customer", "account_id": "acc1"}
        if username == "admin@yourdomain.com":
            user_data["role"] = "admin"
        return User(**user_data)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")