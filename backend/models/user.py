from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional, Annotated
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    """
    Représente les données utilisateur stockées dans la table users personnalisée.
    Ces données sont liées à l'utilisateur Supabase Auth via l'ID.
    """
    id: UUID4 = Field(
        default_factory=uuid.uuid4,
        description="UUID v4 correspondant à l'ID Supabase Auth",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    username: Annotated[str, Field(
        min_length=3, 
        max_length=50,
        description="Nom d'utilisateur unique",
        example="john_doe"
    )]
    email: EmailStr = Field(
        description="Email (doit correspondre à celui de Supabase Auth)",
        example="john.doe@example.com"
    )
    siren_number: Optional[str] = Field(
        default=None,
        description="Numéro SIREN de l'entreprise",
        example="123456789"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Numéro de téléphone",
        example="+33612345678"
    )
    address: Optional[str] = Field(
        default=None,
        description="Adresse postale",
        example="123 Rue de Paris, 75001 Paris"
    )

    model_config = {
        "json_schema_extra": {
            "description": """
            Les utilisateurs sont gérés via deux systèmes :
            1. Supabase Auth : gère l'authentification (email, mot de passe, tokens)
            2. Table users : stocke les informations métier (SIREN, adresse, etc.)
            
            L'ID est partagé entre les deux systèmes pour lier les données.
            """
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
