from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Optional, List
from models.ocr import OCRResponse, OCRResult
from models.invoice import Invoice, InvoiceCreate, InvoiceUpdate, OCRStatus
from services.ocr_service import process_invoice_async
from database.db import create_invoice, get_invoice_by_id, update_invoice
from database.supabase_client import supabase
import logging
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

router = APIRouter(
    tags=["invoice-onboarding"],
    responses={404: {"description": "Not found"}},
    prefix="/onboarding"
)

class ManualInvoiceCreate(BaseModel):
    # Champs obligatoires
    invoice_number: str = Field(..., description="Numéro de facture unique")
    client: str = Field(..., description="Nom du client ou de l'entreprise")
    client_email: str = Field(..., description="Email du client")
    client_phone: str = Field(..., description="Téléphone du client")
    client_address: str = Field(..., description="Adresse du client")
    client_type: str = Field(..., description="Type de client")
    amount: float = Field(..., gt=0, description="Montant de la facture")
    due_date: datetime = Field(..., description="Date d'échéance")
    currency: str = Field(..., description="Devise de la facture")
    payment_conditions: str = Field(..., description="Conditions de paiement")
    client_siren: str = Field(..., description="Numéro SIREN du client")
    description: str = Field(..., description="Description des services ou produits")
    language: str = Field(..., description="Code langue ISO à 2 lettres (ex: fr, en)")
    special_mentions: str = Field(..., description="Mentions spéciales sur la facture")
    pdf_invoice_subject: str = Field(..., description="Sujet du PDF de la facture")
    
    # Champs optionnels
    client_postal_code: Optional[str] = Field(None, description="Code postal du client")
    client_city: Optional[str] = Field(None, description="Ville du client")
    client_country: str = Field("FR", description="Code pays du client")
    client_vat_number: Optional[str] = Field(None, description="Numéro de TVA du client")
    line_items: Optional[List[dict]] = Field(default_factory=list, description="Lignes de facturation détaillées")
    pdf_invoice_free_text: Optional[str] = Field(None, description="Texte libre sur le PDF de la facture")

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_number": "2024-001",
                "client": "ORIA BIOSCIENCE SAS",
                "client_email": "contact@example.com",
                "client_phone": "06 40 381 5803",
                "client_address": "6, Rue Jean Calvin",
                "client_type": "company",
                "amount": 1250.0,
                "due_date": "2024-09-06T00:00:00Z",
                "currency": "EUR",
                "payment_conditions": "30_days",
                "client_siren": "979617123",
                "description": "Développement d'un site internet responsive sous Webflow",
                "language": "fr",
                "special_mentions": "TVA non applicable, art. 293 B du CGI",
                "pdf_invoice_subject": "Facture développement site web",
                "client_postal_code": "75005",
                "client_city": "Paris"
            }
        }

@router.post(
    "/upload",
    response_model=OCRResponse,
    summary="Upload and process an invoice without authentication",
    description="""
    Uploads and processes a PDF invoice without requiring authentication.
    This endpoint is part of the onboarding flow and:
    1. Validates the PDF file
    2. Creates a pending invoice record
    3. Starts asynchronous OCR processing
    """
)
async def upload_invoice_ocr(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    try:
        if not file.content_type == "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
            
        # Create invoice with pending status
        invoice_id = str(uuid.uuid4())
        temp_invoice_number = f"TEMP-{invoice_id[:8]}"
        
        invoice_data = {
            "id": invoice_id,
            "status": "OCR_PENDING",
            "created_date": datetime.now(),
            "user_id": None,  # Will be set after OCR and user registration
            "invoice_number": temp_invoice_number,
            "client": "Pending OCR",
            "amount": 0,
            "due_date": datetime.now() + timedelta(days=30),  # Valeur temporaire
            "description": "Processing invoice...",
            "client_type": "company",
            "client_country": "FR",
            "currency": "EUR",
            "language": "fr",
            "payment_conditions": "upon_receipt"
        }
        
        # Create invoice record
        invoice = await create_invoice(invoice_data)
        
        if not invoice:
            raise HTTPException(status_code=500, detail="Failed to create invoice record")
        
        # Start OCR processing in background
        file_content = await file.read()
        background_tasks.add_task(
            process_invoice_async,
            invoice_id,
            file_content
        )
        
        return OCRResponse(
            invoice_id=invoice_id,
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/manual",
    response_model=Invoice,
    summary="Créer une facture manuellement",
    description="""
    Crée une nouvelle facture manuellement en fournissant toutes les informations nécessaires.
    Cette route fait partie du processus d'onboarding et ne nécessite pas d'authentification.
    """
)
async def create_manual_invoice(invoice: ManualInvoiceCreate):
    try:
        # Générer un ID unique pour la facture
        invoice_id = str(uuid.uuid4())
        
        # Préparer les données de la facture
        invoice_data = {
            "id": invoice_id,
            "status": "Draft",  # Statut initial pour une création manuelle
            "created_date": datetime.now(),
            "user_id": None,  # Sera défini après l'inscription
            **invoice.dict()
        }
        
        # Créer la facture dans la base de données
        created_invoice = await create_invoice(invoice_data)
        
        if not created_invoice:
            raise HTTPException(
                status_code=500,
                detail="Échec de la création de la facture"
            )
        
        return created_invoice
        
    except Exception as e:
        logging.error(f"Erreur lors de la création manuelle de la facture: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de la facture: {str(e)}"
        ) 
    
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

@router.patch(
    "/{invoice_id}",
    response_model=Invoice,
    summary="Update invoice information during onboarding",
    description="""
    Updates invoice information during the onboarding process.
    Can also be used to associate the invoice with a user, completing the onboarding.
    
    This endpoint supports partial updates, meaning you only need to send the fields you want to update.
    """,
    responses={
        200: {
            "description": "Invoice updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "invoice_number": "INV-2024-001",
                        "client": "Acme Corp",
                        "amount": 1000.50,
                        "status": "OCR_COMPLETED"
                    }
                }
            }
        },
        400: {
            "description": "Invalid update data or invoice already associated with a user",
            "content": {
                "application/json": {
                    "example": {"detail": "Invoice is already associated with a user"}
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
async def update_invoice_info(
    invoice_id: str,
    invoice_data: InvoiceUpdate
):
    """
    Met à jour partiellement les informations d'une facture pendant l'onboarding
    
    Parameters:
    - invoice_id: ID de la facture à mettre à jour
    - invoice_data: Données partielles de mise à jour
    
    Returns:
    - La facture mise à jour
    """
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
