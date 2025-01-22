from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer
from database.supabase_client import supabase
from typing import Optional
import jwt
import logging

security = HTTPBearer()

async def get_current_user(authorization: str = Header(...)):
    """
    Vérifie le token JWT et retourne l'utilisateur authentifié
    """
    try:
        if not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        token = authorization.split(' ')[1]
        user = supabase.auth.get_user(token)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
        return user.user.user_metadata
        
    except Exception as e:
        logging.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Similaire à get_current_user mais ne lève pas d'exception si non authentifié
    """
    try:
        if not authorization or not authorization.startswith('Bearer '):
            return None
            
        token = authorization.split(' ')[1]
        user = supabase.auth.get_user(token)
        
        if not user:
            return None
            
        return user.user.user_metadata
        
    except Exception as e:
        logging.error(f"Optional auth error: {str(e)}")
        return None