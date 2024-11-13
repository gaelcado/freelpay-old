from fastapi import APIRouter, Request, HTTPException
from database.db import update_invoice_status, get_invoice_by_pandadoc_id
import logging

router = APIRouter()

@router.post("/pandadoc")
async def pandadoc_webhook(request: Request):
    try:
        payload = await request.json()
        
        # Log du webhook reçu
        logging.info(f"Received PandaDoc webhook: {payload}")
        
        # Vérifier le type d'événement
        if payload.get('event') == 'document_state_changed':
            document_status = payload['data']['status']
            document_id = payload['data']['id']
            
            # Récupérer l'invoice correspondante
            invoice = await get_invoice_by_pandadoc_id(document_id)
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Mettre à jour le statut selon l'état du document
            if document_status == 'document.completed':
                await update_invoice_status(
                    invoice_id=invoice['id'],
                    user_id=invoice['user_id'],
                    status="Signed"
                )
                
        return {"status": "success"}
        
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 