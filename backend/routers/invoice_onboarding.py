from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
from models.ocr import OCRResponse, OCRResult
from models.invoice import Invoice, InvoiceCreate
from services.ocr_service import process_invoice
from dependencies import get_current_user, get_optional_user
from database.db import create_invoice, get_invoice_by_id, update_invoice
import logging
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/onboarding",
    tags=["invoice-onboarding"],
    responses={404: {"description": "Not found"}}
)

@router.post("/upload", response_model=OCRResponse)
async def upload_invoice(file: UploadFile = File(...)):
    """
    1. Validate the PDF file
    2. Process OCR to extract data
    3. Create the invoice with the extracted data
    """
    try:
        if not file.content_type == "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
            
        ocr_result = await process_invoice(file)
        
        if not ocr_result or "error" in ocr_result:
            error_msg = ocr_result.get("error", "Failed to extract invoice data") if ocr_result else "Failed to extract invoice data"
            raise HTTPException(status_code=400, detail=error_msg)
            
        # Vérifier que nous avons les champs requis
        required_fields = ["invoice_number", "client", "amount", "due_date"]
        missing_fields = [field for field in required_fields if field not in ocr_result]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
            
        invoice_data = {
            "id": str(uuid.uuid4()),
            "status": "draft",
            "created_date": datetime.now(),
            "client_type": "company",
            "client_country": "FR",
            "currency": "EUR",
            **ocr_result
        }
        
        invoice = await create_invoice(invoice_data)
        
        return OCRResponse(
            invoice_id=invoice["id"],
            status="draft",
            ocr_results=OCRResult(**ocr_result)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice_info(invoice_id: str):
    """
    Récupère toutes les informations d'une facture, y compris les résultats OCR
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice_info(
    invoice_id: str,
    invoice_data: InvoiceCreate
):
    """
    Met à jour les informations d'une facture pendant l'onboarding
    """
    try:
        existing_invoice = await get_invoice_by_id(invoice_id)
        if not existing_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Filtrer les champs qui existent dans la table invoices
        update_data = {
            "invoice_number": invoice_data.invoice_number,
            "client": invoice_data.client,
            "amount": invoice_data.amount,
            "due_date": invoice_data.due_date,
            "description": invoice_data.description,
            "client_email": invoice_data.client_email,
            "client_phone": invoice_data.client_phone,
            "client_address": invoice_data.client_address,
            "client_postal_code": invoice_data.client_postal_code,
            "client_city": invoice_data.client_city,
            "client_vat_number": invoice_data.client_vat_number
        }
        
        # Retirer les champs None pour ne pas écraser les valeurs existantes
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        updated_invoice = await update_invoice(invoice_id, update_data)
        return updated_invoice
        
    except Exception as e:
        logging.error(f"Error updating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 