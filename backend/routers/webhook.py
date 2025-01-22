from fastapi import APIRouter, Request, HTTPException
from database.db import update_invoice_status, get_invoice_by_pandadoc_id
import logging

router = APIRouter()

@router.post(
    "/pandadoc",
    tags=["webhooks"],
    summary="PandaDoc webhook endpoint",
    description="""
    Handles PandaDoc webhook notifications for document status changes.
    Updates invoice status when documents are signed.
    """,
    responses={
        200: {
            "description": "Webhook processed successfully",
            "content": {
                "application/json": {
                    "example": {"status": "success"}
                }
            }
        },
        404: {
            "description": "Invoice not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Invoice not found"}
                }
            }
        },
        500: {
            "description": "Processing error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error processing webhook"}
                }
            }
        }
    }
)
async def pandadoc_webhook(request: Request):
    """
    Process PandaDoc webhook notifications
    
    Parameters:
    - request: Webhook payload from PandaDoc
    
    Returns:
    - Status confirmation
    """
    try:
        payload = await request.json()
        logging.info(f"Received PandaDoc webhook: {payload}")
        
        if payload.get('event') == 'document_state_changed':
            document_status = payload['data']['status']
            document_id = payload['data']['id']
            
            invoice = await get_invoice_by_pandadoc_id(document_id)
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
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