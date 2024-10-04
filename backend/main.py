from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from routers import auth, user, invoice
from database.mongodb import insert_user, find_user
import bcrypt
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from dependencies import get_current_user
from fastapi.staticfiles import StaticFiles
import logging

load_dotenv()

app = FastAPI()

# Configurez CORS et autres middlewares ici

# Augmentez la taille maximale des fichiers téléchargés à 10 Mo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustez ceci pour la sécurité en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# Configurez la taille maximale du corps de la requête à 10 Mo
app.max_request_size = 10 * 1024 * 1024  # 10 Mo en octets

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(invoice.router, prefix="/invoices", tags=["invoices"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/register", response_model=Token)
async def register_user(user: UserCreate):
    if find_user(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    insert_user(user.username, user.email, hashed_password, is_admin=False)
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = find_user(form_data.username)
    if not user or not bcrypt.checkpw(form_data.password.encode('utf-8'), user['password']):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Example protected route
@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    user_info = {
        "id": current_user['_id'],
        "username": current_user['username'],
        "email": current_user.get('email'),
        "siret_number": current_user.get('siret_number', ''),
        "phone": current_user.get('phone', ''),
        "address": current_user.get('address', ''),
        "id_document_status": current_user.get('id_document_status', 'not_uploaded'),  # Include id_document_status
    }
    logging.debug(f"User info retrieved: {user_info}")
    return user_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
