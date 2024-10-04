from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    siret_number: str
    phone: str
    address: str

class UserInDB(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    siret_number: str
    phone: str
    address: str
    id_document: Optional[str] = None
    id_document_status: Optional[str] = "not_uploaded"  # New field for document status

class User(BaseModel):
    username: str
    email: EmailStr
    siret_number: str
    phone: str
    address: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    siret_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
