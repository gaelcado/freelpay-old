from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from database.db import find_user
import os
from dotenv import load_dotenv
from database.supabase_client import supabase

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await find_user(username)
    if user is None:
        raise credentials_exception
    
    return {
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "siret_number": user.get('siret_number', ''),
        "phone": user.get('phone', ''),
        "address": user.get('address', ''),
        "id_document": user.get('id_document', None),
        "id_document_status": user.get('id_document_status', '')
    }