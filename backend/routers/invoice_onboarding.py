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
from pydantic import BaseModel, Field
from database.supabase_client import supabase  # Utiliser le client déjà configuré
import os

router = APIRouter(
    prefix="/onboarding",
    tags=["invoice-onboarding"],
    responses={404: {"description": "Not found"}}
)

class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = Field(
        default=None,
        description="Numéro unique de la facture",
        example="INV-2024-001"
    )
    client: Optional[str] = Field(
        default=None,
        description="Nom du client ou de l'entreprise",
        example="Acme Corp"
    )
    client_email: Optional[str] = Field(
        default=None,
        description="Email du client",
        example="contact@acme.com"
    )
    client_phone: Optional[str] = Field(
        default=None,
        description="Numéro de téléphone du client",
        example="+33612345678"
    )
    client_address: Optional[str] = Field(
        default=None,
        description="Adresse du client",
        example="123 Rue de Paris"
    )
    client_postal_code: Optional[str] = Field(
        default=None,
        description="Code postal du client",
        example="75001"
    )
    client_city: Optional[str] = Field(
        default=None,
        description="Ville du client",
        example="Paris"
    )
    client_country: Optional[str] = Field(
        default=None,
        description="Code pays du client (ISO)",
        example="FR"
    )
    client_vat_number: Optional[str] = Field(
        default=None,
        description="Numéro de TVA du client",
        example="FR12345678900"
    )
    client_siren: Optional[str] = Field(
        default=None,
        description="Numéro SIREN du client (9 chiffres)",
        example="123456789"
    )
    amount: Optional[float] = Field(
        default=None,
        description="Montant de la facture",
        example=1000.50,
        gt=0
    )
    currency: Optional[str] = Field(
        default=None,
        description="Devise de la facture",
        example="EUR"
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Date d'échéance de la facture",
        example="2024-12-31T23:59:59"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description des biens ou services",
        example="Prestations de conseil"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="ID de l'utilisateur propriétaire de la facture",
        example="550e8400-e29b-41d4-a716-446655440000"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_number": "INV-2024-001",
                "client": "Acme Corp",
                "client_email": "contact@acme.com",
                "amount": 1000.50,
                "currency": "EUR",
                "due_date": "2024-12-31T23:59:59",
                "user_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

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
    invoice_data: InvoiceUpdate
):
    """
    Met à jour les informations d'une facture pendant l'onboarding
    """
    try:
        existing_invoice = await get_invoice_by_id(invoice_id)
        if not existing_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Convertir le modèle Pydantic en dict et filtrer les None
        update_data = {
            k: v for k, v in invoice_data.model_dump().items() 
            if v is not None
        }
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Vérifier si user_id est fourni et valide
        if 'user_id' in update_data:
            # Vérifier si l'utilisateur existe dans la base de données
            user_response = supabase.table('users').select('*').eq('id', update_data['user_id']).execute()
            if not user_response.data:
                raise HTTPException(status_code=400, detail="Invalid user_id - User not found")
            
            # Si l'invoice a déjà un user_id différent, empêcher la mise à jour
            if existing_invoice.get('user_id') and existing_invoice['user_id'] != update_data['user_id']:
                raise HTTPException(status_code=400, detail="Invoice already associated with a different user")
        
        updated_invoice = await update_invoice(invoice_id, update_data)
        return updated_invoice
        
    except Exception as e:
        logging.error(f"Error updating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 