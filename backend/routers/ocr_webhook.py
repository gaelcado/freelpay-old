from fastapi import APIRouter, Request, HTTPException, Depends, Security
from models.invoice import OCRStatus
from database.db import update_invoice
from dependencies import get_current_user
from fastapi.security import APIKeyHeader
import logging
import os
from typing import Optional
from pydantic import BaseModel

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Définir le header de sécurité pour Swagger
X_WEBHOOK_SECRET = APIKeyHeader(name="X-Webhook-Secret", auto_error=False)

router = APIRouter(
    prefix="/webhooks/ocr",
    tags=["webhooks"],
)

# Clé secrète pour sécuriser le webhook
OCR_WEBHOOK_SECRET = os.getenv("OCR_WEBHOOK_SECRET")
if not OCR_WEBHOOK_SECRET:
    logger.error("OCR_WEBHOOK_SECRET environment variable is not set")
else:
    logger.debug(f"OCR_WEBHOOK_SECRET is configured: {OCR_WEBHOOK_SECRET}")

class OCRWebhookPayload(BaseModel):
    invoice_id: str
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
                "error": None
            }
        }

@router.post(
    "/result",
    summary="Webhook pour recevoir la notification de fin d'OCR",
    description="""
    Endpoint appelé par le service OCR pour notifier que le traitement est terminé.
    Le frontend doit ensuite interroger l'API pour récupérer les résultats.
    
    Required headers:
    - X-Webhook-Secret: La clé secrète pour authentifier le service OCR (utiliser: 1234567890)
    - Content-Type: application/json
    
    Le service OCR doit fournir cette clé secrète dans le header X-Webhook-Secret.
    Cette clé doit correspondre à la variable d'environnement OCR_WEBHOOK_SECRET.
    """,
    response_model=dict,
    responses={
        200: {
            "description": "Notification reçue avec succès",
            "content": {
                "application/json": {
                    "example": {"status": "success"}
                }
            }
        },
        403: {
            "description": "Clé secrète invalide",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid webhook secret"}
                }
            }
        }
    }
)
async def ocr_webhook(
    request: Request,
    payload: OCRWebhookPayload,
    webhook_secret: str = Security(X_WEBHOOK_SECRET)
):
    try:
        # Log tous les headers pour le debug
        logger.debug("Received headers:")
        for header, value in request.headers.items():
            logger.debug(f"{header}: {value}")
            
        logger.debug(f"Received webhook secret: {webhook_secret}")
        logger.debug(f"Expected webhook secret: {OCR_WEBHOOK_SECRET}")
        
        if not webhook_secret or webhook_secret != str(OCR_WEBHOOK_SECRET):
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

        # Mettre à jour le statut de la facture
        update_data = {
            "status": "OCR_FAILED" if payload.error else "OCR_COMPLETED"
        }
        if payload.error:
            update_data["error"] = payload.error

        logger.debug(f"Updating invoice {payload.invoice_id} with status: {update_data['status']}")
        await update_invoice(payload.invoice_id, update_data)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing OCR webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 