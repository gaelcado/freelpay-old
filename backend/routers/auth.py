from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from models.user import UserCreate, UserInDB, User
from database.db import find_user, insert_user
from database.supabase_client import supabase
import os
from dotenv import load_dotenv
from dependencies import SECRET_KEY, ALGORITHM
import bcrypt
import logging

# Load environment variables
load_dotenv()

router = APIRouter()

if not SECRET_KEY:
    raise ValueError("No JWT_SECRET_KEY set for JWT authentication")

ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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
    return User(**user)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/signup")
async def signup(user: UserCreate):
    try:
        # Vérification du username
        if await find_user(user.username):
            logging.warning(f"Signup failed: username {user.username} already exists")
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        # Check for duplicate email using Supabase query
        existing_user = supabase.table('users').select('*').eq('email', user.email).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(user.password)
        result = await insert_user(
            user.username,
            user.email,
            hashed_password,
            user.siret_number,
            user.phone,
            user.address,
            is_admin=False
        )
        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected signup error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await find_user(form_data.username)
        if not user:
            logging.info(f"Login failed: user not found")
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )

        if not pwd_context.verify(form_data.password, user['password']):
            logging.info(f"Login failed: invalid password")
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )

        access_token = create_access_token(
            data={"sub": user['username']}
        )

        logging.info(f"Login successful")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "siret_number": user.get('siret_number'),
                "phone": user.get('phone'),
                "address": user.get('address')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
