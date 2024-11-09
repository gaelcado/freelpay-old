from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from database.supabase_client import supabase

security = HTTPBearer()

async def get_current_user(credentials: HTTPBearer = Depends(security)):
    try:
        # Vérifier le token avec Supabase Auth
        response = supabase.auth.get_user(credentials.credentials)
        user = response.user

        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Récupérer les données supplémentaires de la table users
        user_data = supabase.table('users').select('*').eq('id', user.id).single().execute()
        
        return {
            **user_data.data,
            "email": user.email,
            "id": user.id
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")