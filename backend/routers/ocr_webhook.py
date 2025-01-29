from fastapi import APIRouter, Request, HTTPException, Depends
from models.invoice import OCRStatus
from database.db import update_invoice
from dependencies import get_current_user
import logging
import os
import json

router = APIRouter(
    prefix="/webhooks/ocr",
    tags=["webhooks"],
)

# Clé secrète pour sécuriser le webhook
OCR_WEBHOOK_SECRET = os.getenv("OCR_WEBHOOK_SECRET")
if not OCR_WEBHOOK_SECRET:
    logging.error("OCR_WEBHOOK_SECRET environment variable is not set")

@router.post(
    "/result",
    summary="OCR processing result webhook",
    description="""
    Receives OCR processing results from the OCR service.
    Updates the invoice with extracted information.
    
    The webhook is secured with a secret key that must be provided in the X-Webhook-Secret header.
    """
)
async def ocr_webhook(
    request: Request
):
    try:
        # Vérifier la clé secrète
        webhook_secret = request.headers.get("X-Webhook-Secret")
        logging.debug(f"Received webhook secret: {webhook_secret}")
        logging.debug(f"Expected webhook secret: {OCR_WEBHOOK_SECRET}")
        
        if not webhook_secret or webhook_secret != str(OCR_WEBHOOK_SECRET):
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

        # Récupérer le payload
        payload = await request.json()
        logging.info(f"Received OCR webhook: {payload}")

        invoice_id = payload.get("invoice_id")
        if not invoice_id:
            raise HTTPException(status_code=400, detail="Missing invoice_id")

        # Mettre à jour la facture avec les résultats OCR
        ocr_data = payload.get("ocr_results", {})
        update_data = {
            "status": "OCR_COMPLETED",
            **ocr_data
        }

        if payload.get("error"):
            update_data["status"] = "OCR_FAILED"

        await update_invoice(invoice_id, update_data)
        
        return {"status": "success"}
        
    except Exception as e:
        logging.error(f"Error processing OCR webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 