from fastapi import APIRouter, HTTPException
import httpx
import os
from typing import Optional
import re

router = APIRouter()

SIREN_API_BASE_URL = "https://data.siren-api.fr/v3"
SIREN_API_KEY = os.getenv("SIREN_API_KEY")

@router.get("/validate/{siren}")
async def validate_siren(siren: str):
    # Vérifier le format du SIREN (9 chiffres)
    if not re.match(r'^\d{9}$', siren):
        raise HTTPException(status_code=400, detail="Format du SIREN incorrect")
    
    if not SIREN_API_KEY:
        raise HTTPException(status_code=500, detail="SIREN API key is not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SIREN_API_BASE_URL}/unites_legales/{siren}",
                headers={"X-Client-Secret": SIREN_API_KEY}
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="SIREN invalide")
            elif response.status_code == 400:
                raise HTTPException(status_code=400, detail="Format du SIREN incorrect")
            
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification du SIREN") 