from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from models.user import User
from models.invoice import InvoiceCreate, Invoice, InvoiceInDB
from services.ocr_service import process_invoice
from services.scoring_service import calculate_score
from services.pennylane import create_pennylane_estimate
from dependencies import get_current_user
from database.db import create_invoice, get_user_invoices, update_invoice_status, get_invoice_by_id, update_invoice_pennylane_id
from datetime import datetime
import logging

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

@router.post("/{invoice_id}/send", response_model=Invoice)
async def send_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    try:
        # Mettre à jour le statut de la facture à "Sent"
        updated_invoice = await update_invoice_status(invoice_id, current_user['id'], "Sent")
        if not updated_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return updated_invoice
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
        # Get invoice data from database
        invoice = await get_invoice_by_id(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        logging.info(f"Retrieved invoice: {invoice}")
            
        # Convert dates to string format for Pennylane
        invoice['due_date'] = invoice['due_date'].split('T')[0]  # Get only the date part
            
        # Create estimate in Pennylane
        pennylane_response = await create_pennylane_estimate(invoice)
        
        estimate_id = pennylane_response.get('estimate', {}).get('id')
        if not estimate_id:
            raise HTTPException(status_code=500, detail="No estimate ID in response")
            
        await update_invoice_pennylane_id(invoice_id, estimate_id)
        
        return {
            "message": "Pennylane estimate created successfully",
            "estimate_id": estimate_id
        }
        
    except Exception as e:
        logging.error(f"Error creating Pennylane estimate: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Error creating Pennylane estimate: {str(e)}")