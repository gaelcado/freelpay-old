from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Annotated

class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    siret_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserInDB(BaseModel):
    username: str
    email: EmailStr
    password: str
    siret_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    id_document: Optional[str] = None
    id_document_status: Optional[str] = "not_uploaded"

class User(BaseModel):
    id: str
    username: str
    email: str
    siret_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    siret_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
