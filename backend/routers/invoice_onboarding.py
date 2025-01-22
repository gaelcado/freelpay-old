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
    invoice_data: InvoiceCreate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    existing_invoice = await get_invoice_by_id(invoice_id)
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # If user is authenticated, associate invoice with user
    if current_user and not existing_invoice["user_id"]:
        invoice_data.user_id = current_user["id"]
        
    updated_invoice = await update_invoice(invoice_id, invoice_data.dict())
    return updated_invoice 