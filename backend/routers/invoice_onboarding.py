from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
from models.ocr import OCRResponse, OCRResult
from models.invoice import Invoice, InvoiceCreate, InvoiceUpdate
from services.ocr_service import process_invoice
from database.db import create_invoice, get_invoice_by_id, update_invoice
from database.supabase_client import supabase
import logging
import uuid
from datetime import datetime

router = APIRouter(
    tags=["invoice-onboarding"],
    responses={404: {"description": "Not found"}},
    prefix="/onboarding"
)

@router.post(
    "/upload",
    response_model=OCRResponse,
    summary="Upload and process an invoice without authentication",
    description="""
    Uploads and processes a PDF invoice without requiring authentication.
    This endpoint is part of the onboarding flow and:
    1. Validates the PDF file
    2. Processes OCR to extract data
    3. Creates an invoice record without user association
    """
)
async def upload_invoice_ocr(file: UploadFile = File(...)):
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
            
        # Vérifier qu'aucun user_id n'est fourni dans les données OCR
        if 'user_id' in ocr_result:
            raise HTTPException(status_code=400, detail="Cannot set user_id during initial OCR upload")
            
        invoice_data = {
            "id": str(uuid.uuid4()),
            "status": "draft",
            "created_date": datetime.now(),
            "client_type": "company",
            "client_country": "FR",
            "currency": "EUR",
            "user_id": None,  # Explicitly set to None for onboarding
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

@router.get(
    "/{invoice_id}",
    response_model=Invoice,
    summary="Get invoice information during onboarding",
    description="Retrieves information for an invoice that is not yet associated with a user"
)
async def get_invoice_info(invoice_id: str):
    try:
        invoice = await get_invoice_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        # Verify this is an onboarding invoice (no user_id)
        if invoice.get('user_id'):
            raise HTTPException(
                status_code=400,
                detail="This invoice is already associated with a user"
            )
            
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/{invoice_id}",
    response_model=Invoice,
    summary="Update invoice information during onboarding",
    description="""
    Updates invoice information during the onboarding process.
    Can also be used to associate the invoice with a user, completing the onboarding.
    """
)
async def update_invoice_info(
    invoice_id: str,
    invoice_data: InvoiceUpdate
):
    try:
        existing_invoice = await get_invoice_by_id(invoice_id)
        if not existing_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        # Verify this is an onboarding invoice (no user_id)
        if existing_invoice.get('user_id'):
            raise HTTPException(
                status_code=400,
                detail="This invoice is already associated with a user"
            )
        
        # Convertir le modèle Pydantic en dict et filtrer les None
        update_data = {
            k: v for k, v in invoice_data.model_dump().items() 
            if v is not None
        }
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Si un user_id est fourni dans la mise à jour
        if 'user_id' in update_data:
            try:
                # Convertir en string si c'est un UUID
                update_data['user_id'] = str(update_data['user_id'])
                
                # Vérifier si l'utilisateur existe
                user_response = supabase.table('users').select('*').eq('id', update_data['user_id']).execute()
                if not user_response.data:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"User not found with ID: {update_data['user_id']}"
                    )
                    
                # Vérifier que c'est la première association d'utilisateur
                if existing_invoice.get('user_id'):
                    raise HTTPException(
                        status_code=400,
                        detail="Invoice is already associated with a user"
                    )
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid UUID format for user_id: {update_data['user_id']}"
                )

        updated_invoice = await update_invoice(invoice_id, update_data)
        return updated_invoice
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating invoice: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating the invoice: {str(e)}"
        ) 