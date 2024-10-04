from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from models.user import User
from models.invoice import InvoiceCreate, Invoice, InvoiceInDB
from services.ocr_service import process_invoice
from services.scoring_service import calculate_score
from dependencies import get_current_user
from database.mongodb import create_invoice, get_user_invoices, update_invoice_status
from datetime import datetime

router = APIRouter()

@router.post("/create", response_model=Invoice)
async def create_invoice_route(invoice: InvoiceCreate, current_user: User = Depends(get_current_user)):
    score = calculate_score(invoice.dict())
    possible_financing = invoice.amount * (1 - score)
    
    invoice_data = InvoiceInDB(
        **invoice.dict(),
        user_id=current_user.username,
        created_date=datetime.now(),
        status="ongoing",
        score=score,
        possible_financing=possible_financing
    )
    
    result = create_invoice(invoice_data.dict())
    if result:
        return Invoice(**result)
    raise HTTPException(status_code=400, detail="Failed to create invoice")

@router.post("/upload", response_model=Invoice)
async def upload_invoice(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    invoice_data = await process_invoice(file)
    score = calculate_score(invoice_data)
    possible_financing = invoice_data["amount"] * (1 - score)
    
    invoice_db = InvoiceInDB(
        **invoice_data,
        user_id=current_user.username,
        created_date=datetime.now(),
        status="ongoing",
        score=score,
        possible_financing=possible_financing
    )
    
    result = create_invoice(invoice_db.dict())
    if result:
        return Invoice(**result)
    raise HTTPException(status_code=400, detail="Failed to process invoice")

@router.get("/", response_model=List[Invoice])
async def get_invoices(current_user: dict = Depends(get_current_user)):
    invoices = get_user_invoices(current_user['username'])
    return [Invoice(**invoice) for invoice in invoices]

@router.post("/{invoice_id}/accept")
async def accept_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    result = update_invoice_status(invoice_id, current_user['username'], "accepted")
    if result:
        return {"message": "Invoice accepted successfully"}
    raise HTTPException(status_code=400, detail="Failed to accept invoice")

@router.post("/{invoice_id}/refuse")
async def refuse_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    result = update_invoice_status(invoice_id, current_user['username'], "refused")
    if result:
        return {"message": "Invoice refused successfully"}
    raise HTTPException(status_code=400, detail="Failed to refuse invoice")