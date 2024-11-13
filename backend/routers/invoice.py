from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from models.user import User
from models.invoice import InvoiceCreate, Invoice, InvoiceInDB
from services.ocr_service import process_invoice
from services.scoring_service import calculate_score
from services.pennylane import create_pennylane_estimate, send_estimate_for_signature
from services.pandadoc import send_document_for_signature
from dependencies import get_current_user
from database.db import create_invoice, get_user_invoices, update_invoice_status, get_invoice_by_id, update_invoice_pennylane_id, update_invoice_pandadoc_id
from datetime import datetime
import logging
import requests
import os

PENNYLANE_API_KEY = os.getenv('PENNYLANE_API_KEY')
PENNYLANE_API_URL = "https://app.pennylane.com/api/external/v1"

router = APIRouter()

@router.post("/create", response_model=Invoice)
async def create_invoice_route(invoice: InvoiceCreate, current_user: dict = Depends(get_current_user)):
    score = calculate_score(invoice.dict())
    possible_financing = invoice.amount * (1 - score)
    
    invoice_data = InvoiceInDB(
        **invoice.dict(),
        user_id=current_user['id'],
        created_date=datetime.now(),
        score=score,
        possible_financing=possible_financing
    )
    
    result = await create_invoice(invoice_data.dict())
    if result:
        return Invoice(**result)
    raise HTTPException(status_code=400, detail="Failed to create invoice")

@router.post("/upload", response_model=Invoice)
async def upload_invoice(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    invoice_data = await process_invoice(file)
    
    if "error" in invoice_data:
        raise HTTPException(status_code=400, detail=invoice_data["error"])
    
    score = calculate_score(invoice_data)
    possible_financing = invoice_data["amount"] * (1 - score)
    
    invoice_db = InvoiceInDB(
        **invoice_data,
        user_id=current_user['id'],
        created_date=datetime.now(),
        status="Ongoing",
        score=score,
        possible_financing=possible_financing
    )
    
    result = await create_invoice(invoice_db.dict())
    if result:
        return Invoice(**result)
    raise HTTPException(status_code=400, detail="Failed to process invoice")

@router.get("/list", response_model=List[Invoice])
async def get_invoices(current_user: dict = Depends(get_current_user)):
    invoices = await get_user_invoices(current_user['id'])
    if not invoices:
        return []
    return [
        Invoice(
            **{
                **invoice,
                'created_date': invoice['created_date'] if isinstance(invoice['created_date'], str) 
                               else invoice['created_date'].isoformat()
            }
        ) 
        for invoice in invoices
    ]

@router.post("/{invoice_id}/send")
async def send_invoice_endpoint(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        invoice = await get_invoice_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        if not invoice.get('client_email'):
            raise HTTPException(
                status_code=400,
                detail="Client email is required to send the quote"
            )
            
        if not invoice.get('pennylane_id'):
            raise HTTPException(
                status_code=400,
                detail="Invoice must be created in Pennylane first"
            )
        
        # 1. Récupérer l'URL du PDF depuis Pennylane
        pdf_response = await get_invoice_pdf_url(invoice_id, current_user)
        pdf_url = pdf_response["pdf_url"]
        
        # 2. Envoyer le document pour signature via PandaDoc
        pandadoc_response = await send_document_for_signature(
            file_url=pdf_url,
            recipient_email=invoice['client_email'],
            recipient_name=invoice['client']
        )
        
        # 3. Mettre à jour le statut de la facture
        await update_invoice_status(invoice_id, current_user['id'], "Sent")
        
        # 4. Stocker l'ID du document PandaDoc
        await update_invoice_pandadoc_id(invoice_id, pandadoc_response['id'])
        
        return {"message": "Invoice sent successfully for signature"}
        
    except Exception as e:
        logging.error(f"Error sending invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# In your invoice.py router

@router.post("/create-demo", response_model=Invoice)
async def create_demo_invoice(invoice: InvoiceCreate):
    score = calculate_score(invoice.dict())
    possible_financing = invoice.amount * (1 - score)
    
    invoice_data = Invoice(
        invoice_number=invoice.invoice_number,
        client=invoice.client,
        amount=invoice.amount,
        due_date=invoice.due_date,
        description=invoice.description,
        created_date=datetime.now(),
        status="Demo",
        score=score,
        possible_financing=possible_financing
    )
    
    return invoice_data

@router.post("/upload-demo", response_model=Invoice)
async def upload_demo_invoice(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    invoice_data = await process_invoice(file)
    
    if "error" in invoice_data:
        raise HTTPException(status_code=400, detail=invoice_data["error"])
    
    score = calculate_score(invoice_data)
    possible_financing = invoice_data["amount"] * (1 - score)
    
    invoice = Invoice(
        invoice_number=invoice_data["invoice_number"],
        client=invoice_data["client"],
        amount=invoice_data["amount"],
        due_date=invoice_data["due_date"],
        description=invoice_data.get("description"),
        created_date=datetime.now(),
        status="Demo",
        score=score,
        possible_financing=possible_financing
    )
    
    return invoice

@router.post("/{invoice_id}/create-pennylane-estimate")
async def create_pennylane_estimate_endpoint(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        invoice = await get_invoice_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Vérification des données requises
        required_fields = ['client', 'amount', 'due_date']
        for field in required_fields:
            if not invoice.get(field):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        pennylane_response = await create_pennylane_estimate(invoice)
        
        if not isinstance(pennylane_response, dict):
            raise HTTPException(
                status_code=500,
                detail="Invalid response from Pennylane"
            )
            
        estimate_id = pennylane_response.get('estimate', {}).get('id')
        if not estimate_id:
            raise HTTPException(
                status_code=500,
                detail="No estimate ID in response"
            )
            
        await update_invoice_pennylane_id(invoice_id, estimate_id)
        
        return {
            "message": "Pennylane estimate created successfully",
            "estimate_id": estimate_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@router.get("/{invoice_id}/pdf-url")
async def get_invoice_pdf_url(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        invoice = await get_invoice_by_id(invoice_id)
        if not invoice or not invoice.get('pennylane_id'):
            raise HTTPException(status_code=404, detail="Invoice or Pennylane ID not found")
            
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {PENNYLANE_API_KEY}'
        }
        
        response = requests.get(
            f"{PENNYLANE_API_URL}/customer_estimates/{invoice['pennylane_id']}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, 
                              detail="Error fetching Pennylane estimate")
                              
        estimate_data = response.json()
        return {"pdf_url": estimate_data['estimate']['file_url']}
        
    except Exception as e:
        logging.error(f"Error getting PDF URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))