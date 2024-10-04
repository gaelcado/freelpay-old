from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from database.mongodb import find_user
import os
from dotenv import load_dotenv

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
    
    user = find_user(username)
    if user is None:
        raise credentials_exception
    
    # Ensure all required fields are present
    user_dict = {
        "id": str(user['_id']),  # Convert ObjectId to string
        "username": user['username'],
        "email": user.get('email'),
        "siret_number": user.get('siret_number', ''),
        "phone": user.get('phone', ''),
        "address": user.get('address', ''),
        "is_verified": user.get('is_verified', False),
    }
    
    return user_dict