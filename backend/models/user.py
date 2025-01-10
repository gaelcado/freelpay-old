from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional, Annotated
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    id: UUID4 = Field(
        default_factory=uuid.uuid4,
        description="UUID v4 automatically generated",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    username: Annotated[str, Field(
        min_length=3, 
        max_length=50,
        example="john_doe"
    )]
    email: EmailStr = Field(
        example="john.doe@example.com"
    )
    siren_number: Optional[str] = Field(
        default=None,
        example="123456789"
    )
    phone: Optional[str] = Field(
        default=None,
        example="+33612345678"
    )
    address: Optional[str] = Field(
        default=None,
        example="123 Rue de Paris, 75001 Paris"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "john_doe",
                    "email": "john.doe@example.com",
                    "siren_number": "123456789",
                    "phone": "+33612345678",
                    "address": "123 Rue de Paris, 75001 Paris"
                }
            ]
        }
    }

class UserInDB(BaseModel):
    username: str
    email: EmailStr
    password: str
    siren_number: Optional[str] = None
    siren_validated: Optional[bool] = False
    phone: Optional[str] = None
    address: Optional[str] = None
    id_document: Optional[str] = None
    id_document_status: Optional[str] = "not_uploaded"

class User(BaseModel):
    id: str
    username: str
    email: str
    siren_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    siren_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    id_document: Optional[str] = None
    id_document_status: Optional[str] = None
