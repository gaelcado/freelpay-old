from fastapi import APIRouter, HTTPException
import httpx
import os
from typing import Optional
import re
from datetime import datetime, timedelta
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

INSEE_API_BASE_URL = "https://api.insee.fr/entreprises/sirene/V3.11"
INSEE_TOKEN = os.getenv("INSEE_TOKEN", "12d5485c-0e0f-3fa3-8c0a-090966ec8b61")  # Votre token par défaut

async def get_insee_token():
    """Récupère un nouveau token INSEE si nécessaire"""
    # Pour l'instant on utilise le token statique, 
    # mais on pourrait implémenter le renouvellement automatique plus tard
    return INSEE_TOKEN

@router.get("/validate/{siren}")
async def validate_siren(siren: str):
    """
    Valide un numéro SIREN et retourne les informations de l'entreprise
    """
    # Vérifier le format du SIREN (9 chiffres)
    if not re.match(r'^\d{9}$', siren):
        raise HTTPException(status_code=400, detail="Format du SIREN incorrect")
    
    try:
        token = await get_insee_token()
        
        async with httpx.AsyncClient() as client:
            # Ajout de logging pour debug
            logger.info(f"Calling INSEE API with URL: {INSEE_API_BASE_URL}/siren/{siren}")
            logger.info(f"Using token: {token}")
            
            response = await client.get(
                f"{INSEE_API_BASE_URL}/siren/{siren}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
            )
            
            # Log de la réponse pour debug
            logger.info(f"INSEE API response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"INSEE API error response: {response.text}")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="SIREN invalide ou entreprise non trouvée")
            elif response.status_code == 403:
                raise HTTPException(status_code=403, detail="Accès non autorisé à l'API INSEE")
            
            response.raise_for_status()
            data = response.json()
            
            unite_legale = data.get("uniteLegale", {})
            periodes = unite_legale.get("periodesUniteLegale", [])
            periode_courante = periodes[0] if periodes else {}
            
            # Adapter la réponse au format attendu par le frontend
            return {
                "unite_legale": {
                    "siren": unite_legale.get("siren"),
                    "denomination": periode_courante.get("denominationUniteLegale"),
                    "activite_principale": periode_courante.get("activitePrincipaleUniteLegale"),
                    "date_creation": unite_legale.get("dateCreationUniteLegale"),
                    "etablissement_siege": {
                        "geo_adresse": periode_courante.get("adresseEtablissement", {}).get("complementAdresseEtablissement", "")
                    },
                    "categorie_entreprise": periode_courante.get("categorieEntrepriseUniteLegale"),
                    "tranche_effectifs": unite_legale.get("trancheEffectifsUniteLegale"),
                    "annee_effectifs": unite_legale.get("anneeEffectifsUniteLegale"),
                    "categorie_juridique": periode_courante.get("categorieJuridiqueUniteLegale"),
                    "economie_sociale_solidaire": periode_courante.get("economieSocialeSolidaireUniteLegale"),
                    "caractere_employeur": periode_courante.get("caractereEmployeurUniteLegale"),
                    "etat_administratif": periode_courante.get("etatAdministratifUniteLegale")
                }
            }
            
    except httpx.HTTPError as e:
        logger.error(f"Erreur lors de la vérification du SIREN: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification du SIREN") 