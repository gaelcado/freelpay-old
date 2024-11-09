from fastapi import APIRouter, HTTPException
from models.user import UserCreate
from database.supabase_client import supabase
import logging

router = APIRouter()

@router.post("/signup")
async def create_user_record(user: UserCreate):
    try:
        # Vérifier si l'utilisateur existe déjà dans la table users
        existing_user = supabase.table('users').select('*').eq('id', user.id).execute()
        
        if existing_user.data and len(existing_user.data) > 0:
            raise HTTPException(
                status_code=400, 
                detail="User already exists. Please sign in instead."
            )

        # Si l'utilisateur n'existe pas, l'insérer
        response = supabase.table('users').insert({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'siren_number': user.siret_number,
            'phone': user.phone,
            'address': user.address,
            'id_document_status': 'not_uploaded'
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
        return response.data[0]
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
