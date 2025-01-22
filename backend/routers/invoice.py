from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path
from typing import List, Optional
from models.user import User
from models.invoice import InvoiceCreate, Invoice, InvoiceInDB, ScoreResponse, InvoiceListResponse, InvoiceCreateResponse, PdfUrlResponse, SendInvoiceResponse, PennylaneEstimateResponse, DemoInvoiceResponse
from services.ocr_service import process_invoice
from services.scoring_service import calculate_score
from services.pennylane import create_pennylane_estimate, send_estimate_for_signature
from services.pandadoc import send_document_for_signature
from dependencies import get_current_user, get_optional_user
from database.db import create_invoice, get_user_invoices, update_invoice_status, get_invoice_by_id, update_invoice_pennylane_id, update_invoice_pandadoc_id, update_invoice_score, find_user_by_id
from datetime import datetime, timedelta
import logging
import requests
import os

PENNYLANE_API_KEY = os.getenv('PENNYLANE_API_KEY')
PENNYLANE_API_URL = "https://app.pennylane.com/api/external/v1"

router = APIRouter()

@router.post("/create", response_model=InvoiceCreateResponse)
async def create_invoice_route(invoice: InvoiceCreate, current_user: dict = Depends(get_current_user)):
    score = await calculate_score(
        invoice.dict(), 
        user_siren=current_user.get('siren_number'),
        is_authenticated=True
    )
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
        return InvoiceCreateResponse(**result)
    raise HTTPException(status_code=400, detail="Failed to create invoice")

@router.post(
    "/upload",
    response_model=Invoice,
    tags=["invoices"],
    summary="Upload and process an invoice PDF",
    description="""
    Uploads and processes a PDF invoice, extracts data, calculates risk score,
    and saves it to the database. Used in the invoice creation flow.
    """,
    responses={
        200: {
            "description": "Invoice processed and created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "invoice_number": "INV-2024-001",
                        "client": "Acme Corp",
                        "client_email": "contact@acme.com",
                        "client_phone": "+33123456789",
                        "client_address": "123 Business Street",
                        "amount": 10000.0,
                        "due_date": "2024-12-31T23:59:59",
                        "status": "Ongoing",
                        "score": 0.35,
                        "possible_financing": 6500.0
                    }
                }
            }
        },
        400: {
            "description": "Invalid file or processing error",
            "content": {
                "application/json": {
                    "example": {"detail": "Only PDF files are allowed"}
                }
            }
        }
    }
)
async def upload_invoice(
    file: UploadFile = File(
        ..., 
        description="PDF file containing the invoice",
        example="invoice.pdf"
    ),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process a PDF invoice
    
    Parameters:
    - file: PDF file containing the invoice
    
    Returns:
    - Processed invoice with extracted data and risk score
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    invoice_data = await process_invoice(file)
    
    if "error" in invoice_data:
        raise HTTPException(status_code=400, detail=invoice_data["error"])
    
    score = await calculate_score(
        invoice_data,
        user_siren=current_user.get('siren_number'),
        is_authenticated=True
    )
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

@router.get(
    "/list",
    response_model=List[InvoiceListResponse],
    tags=["invoices"],
    summary="List all invoices for the current user",
    responses={
        200: {
            "description": "List of invoices",
            "content": {
                "application/json": {
                    "example": [{
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "invoice_number": "INV-2024-001",
                        "client": "Acme Corp",
                        "amount": 10000.0,
                        "due_date": "2024-12-31T23:59:59",
                        "status": "Draft",
                        "score": 0.35,
                        "possible_financing": 6500.0
                    }]
                }
            }
        }
    }
)
async def list_invoices(current_user: dict = Depends(get_current_user)):
    """Liste toutes les factures de l'utilisateur courant"""
    return await get_user_invoices(current_user['id'])

@router.post(
    "/send",
    response_model=SendInvoiceResponse,
    tags=["invoices"],
    summary="Send invoice for signature",
    description="Sends the invoice to the client for electronic signature via PandaDoc",
    responses={
        200: {
            "description": "Invoice sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Invoice sent successfully for signature"
                    }
                }
            }
        },
        400: {
            "description": "Missing required information",
            "content": {
                "application/json": {
                    "example": {"detail": "Client email is required to send the quote"}
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
        }
    }
)
async def send_invoice_endpoint(
    invoice_id: str = Path(..., example="550e8400-e29b-41d4-a716-446655440000"),
    current_user: User = Depends(get_current_user)
):
    """
    Envoie une facture pour signature électronique
    
    Parameters:
    - invoice_id: ID de la facture à envoyer
    
    Returns:
    - Message de confirmation
    """
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

@router.post(
    "/create-demo",
    response_model=DemoInvoiceResponse,
    tags=["invoices"],
    summary="Create a demo invoice",
    description="Creates a demo invoice without saving it to the database",
    responses={
        200: {
            "description": "Demo invoice created",
            "content": {
                "application/json": {
                    "example": {
                        "invoice_number": "INV-2024-001",
                        "client": "Acme Corp",
                        "amount": 10000.0,
                        "due_date": "2024-12-31T23:59:59",
                        "description": "Consulting services",
                        "created_date": "2024-03-19T14:30:00",
                        "status": "Demo",
                        "score": 0.45,
                        "possible_financing": 5500.0
                    }
                }
            }
        }
    }
)
async def create_demo_invoice(invoice: InvoiceCreate):
    """
    Crée une facture de démonstration
    
    Parameters:
    - invoice: Données de la facture
    
    Returns:
    - Facture de démonstration avec score calculé
    """
    score = await calculate_score(
        invoice.dict(),
        is_authenticated=False
    )
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

@router.post(
    "/upload-demo",
    response_model=DemoInvoiceResponse,
    tags=["invoices"],
    summary="Upload and process a demo invoice",
    description="""
    Uploads and processes a PDF invoice for demonstration purposes.
    The invoice data is extracted but not saved to the database.
    
    Accepts PDF files only.
    """,
    responses={
        200: {
            "description": "Demo invoice processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "invoice_number": "INV-2024-001",
                        "client": "Acme Corp",
                        "amount": 10000.0,
                        "due_date": "2024-12-31T23:59:59",
                        "description": "Consulting services",
                        "created_date": "2024-03-19T14:30:00",
                        "status": "Demo",
                        "score": 0.45,
                        "possible_financing": 5500.0
                    }
                }
            }
        },
        400: {
            "description": "Invalid file format or processing error",
            "content": {
                "application/json": {
                    "example": {"detail": "Only PDF files are allowed"}
                }
            }
        }
    }
)
async def upload_demo_invoice(
    file: UploadFile = File(
        ...,
        description="PDF file containing the invoice",
    )
):
    """
    Upload and process a demo invoice from PDF
    
    Parameters:
    - file: PDF file containing the invoice data
    
    Returns:
    - Processed invoice data with risk score
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    invoice_data = await process_invoice(file)
    
    if "error" in invoice_data:
        raise HTTPException(status_code=400, detail=invoice_data["error"])
    
    score = await calculate_score(invoice_data)
    possible_financing = invoice_data["amount"] * (1 - score)
    
    invoice = DemoInvoiceResponse(
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

@router.post(
    "/{invoice_id}/create-pennylane-estimate",
    response_model=PennylaneEstimateResponse,
    tags=["invoices"],
    summary="Create Pennylane estimate",
    description="""
    Creates an estimate in Pennylane based on the invoice data.
    This is a required step before sending for signature.
    
    The estimate will be created with:
    - Client information
    - Invoice amount and details
    - Due date
    - VAT settings (20% by default)
    """,
    responses={
        200: {
            "description": "Estimate created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Pennylane estimate created successfully",
                        "estimate_id": "est_12345"
                    }
                }
            }
        },
        400: {
            "description": "Missing required fields",
            "content": {
                "application/json": {
                    "example": {"detail": "Missing required field: client"}
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
            "description": "Pennylane API error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to create estimate in Pennylane"}
                }
            }
        }
    }
)
async def create_pennylane_estimate_endpoint(
    invoice_id: str = Path(..., example="550e8400-e29b-41d4-a716-446655440000"),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une estimation dans Pennylane
    
    Parameters:
    - invoice_id: ID de la facture
    
    Returns:
    - Message de confirmation et ID de l'estimation
    """
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

@router.get(
    "/{invoice_id}/pdf-url",
    response_model=PdfUrlResponse,
    tags=["invoices"],
    summary="Get invoice PDF URL",
    description="""
    Generates a temporary URL to download the invoice PDF.
    Used for preview and sending to PandaDoc.
    """,
    responses={
        200: {
            "description": "PDF URL generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "url": "https://storage.googleapis.com/invoices/550e8400.pdf",
                        "expires_at": "2024-03-20T15:30:00"
                    }
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
        }
    }
)
async def get_invoice_pdf_url(
    invoice_id: str = Path(..., example="550e8400-e29b-41d4-a716-446655440000"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a temporary URL for downloading the invoice PDF
    
    Parameters:
    - invoice_id: ID of the invoice
    
    Returns:
    - URL and expiration time for the PDF
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if not invoice.get('pennylane_id'):
        raise HTTPException(
            status_code=400,
            detail="Invoice must be created in Pennylane first"
        )
    
    try:
        headers = {
            'Authorization': f'Bearer {PENNYLANE_API_KEY}',
            'Accept': 'application/json'
        }
        
        response = requests.get(
            f"{PENNYLANE_API_URL}/estimates/{invoice['pennylane_id']}/download",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Failed to get PDF URL from Pennylane"
            )
            
        return {
            "url": response.json()['url'],
            "expires_at": datetime.now() + timedelta(hours=1)
        }
        
    except Exception as e:
        logging.error(f"Error getting PDF URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get PDF URL"
        )

@router.post(
    "/calculate-score",
    response_model=ScoreResponse,
    tags=["invoices"],
    summary="Calculate risk score from invoice data",
    description="""
    Calculates a risk score from invoice data.
    Works with or without authentication.
    
    The score is calculated based on:
    - Invoice amount
    - Client information
    - SIREN number (from invoice or authenticated user)
    - Authentication status
    """,
    responses={
        200: {
            "description": "Successfully calculated score",
            "content": {
                "application/json": {
                    "example": {
                        "score": 0.35,
                        "possible_financing": 6500.0,
                        "amount": 10000.0,
                        "details": {
                            "siren_score": 0.4,
                            "amount_score": 0.3,
                            "authentication_bonus": 0.1
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid amount"}
                }
            }
        }
    }
)
async def calculate_score(
    invoice_data: InvoiceCreate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Calculate risk score from invoice data
    
    Parameters:
    - invoice_data: Complete invoice information
    - current_user: Optional authenticated user information
    
    Returns:
    - Score and possible financing amount with detailed breakdown
    """
    try:
        # Get SIREN from invoice data or authenticated user
        client_siren = invoice_data.client_siren if hasattr(invoice_data, 'client_siren') else None
        user_siren = current_user.get('siren_number') if current_user else None
        siren = user_siren or client_siren
        
        # Calculate score
        score = await calculate_score(
            invoice_data=invoice_data.dict(),
            user_siren=siren,
            is_authenticated=bool(current_user)
        )
        
        possible_financing = invoice_data.amount * (1 - score)
        
        return ScoreResponse(
            score=score,
            possible_financing=possible_financing,
            amount=invoice_data.amount,
            details={
                "siren_score": 0.4 if siren else 0.6,
                "amount_score": min(invoice_data.amount / 100000, 0.3),
                "authentication_bonus": 0.1 if current_user else 0
            }
        )
        
    except Exception as e:
        logging.error(f"Error calculating score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))