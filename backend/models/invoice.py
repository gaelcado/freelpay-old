from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
from pydantic.json import timedelta_isoformat
from enum import Enum

class ClientType(str, Enum):
    COMPANY = "company"
    INDIVIDUAL = "individual"

class InvoiceBase(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class InvoiceCreate(InvoiceBase):
    invoice_number: str
    client: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_postal_code: Optional[str] = None
    client_city: Optional[str] = None
    client_country: str = "FR"
    client_vat_number: Optional[str] = None
    client_type: str = Field(default="company", pattern="^(company|individual)$")
    client_siren: Optional[str] = None
    amount: float = Field(gt=0)
    currency: str = "EUR"
    due_date: datetime
    description: Optional[str] = None
    payment_conditions: str = "upon_receipt"
    language: str = "fr_FR"
    line_items: Optional[List[dict]] = Field(default_factory=list)
    special_mentions: Optional[str] = None
    pdf_invoice_subject: Optional[str] = None

class InvoiceInDB(InvoiceBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    invoice_number: str
    client: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_postal_code: Optional[str] = None
    client_city: Optional[str] = None
    client_country: str = "FR"
    client_vat_number: Optional[str] = None
    client_type: Optional[ClientType] = None
    amount: float = Field(gt=0)
    currency: str = "EUR"
    due_date: datetime
    description: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.now)
    status: str = "Draft"
    financing_date: Optional[datetime] = None
    possible_financing: Optional[float] = None
    score: Optional[float] = None
    pennylane_id: Optional[str] = None
    pandadoc_id: Optional[str] = None
    payment_conditions: str = "upon_receipt"
    language: str = "fr_FR"
    line_items: Optional[List[dict]] = Field(default_factory=list)
    special_mentions: Optional[str] = None
    pdf_invoice_subject: Optional[str] = None
    pdf_invoice_free_text: Optional[str] = None

class Invoice(InvoiceBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    client: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_postal_code: Optional[str] = None
    client_city: Optional[str] = None
    client_country: str = "FR"
    client_vat_number: Optional[str] = None
    client_type: str = "company"
    amount: float
    currency: str = "EUR"
    due_date: datetime
    description: Optional[str] = None
    created_date: datetime
    status: Optional[str] = None
    financing_date: Optional[datetime] = None
    possible_financing: Optional[float] = None
    score: Optional[float] = None
    payment_conditions: str = "upon_receipt"
    language: str = "fr_FR"
    line_items: Optional[List[dict]] = Field(default_factory=list)
    special_mentions: Optional[str] = None
    pdf_invoice_subject: Optional[str] = None

class ScoreDetails(BaseModel):
    siren_score: float = Field(
        description="Score component based on SIREN validation",
        example=0.4,
        ge=0,
        le=1
    )
    amount_score: float = Field(
        description="Score component based on invoice amount",
        example=0.3,
        ge=0,
        le=1
    )
    authentication_bonus: float = Field(
        description="Bonus for authenticated users",
        example=0.1,
        ge=0,
        le=1
    )

class ScoreResponse(BaseModel):
    score: float = Field(
        description="Final risk score between 0 and 1",
        example=0.35,
        ge=0,
        le=1
    )
    possible_financing: float = Field(
        description="Amount available for financing",
        example=6500.0,
        ge=0
    )
    amount: float = Field(
        description="Original invoice amount",
        example=10000.0,
        ge=0
    )
    details: ScoreDetails = Field(
        description="Detailed breakdown of score components"
    )

    class Config:
        json_schema_extra = {
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

class InvoiceListResponse(BaseModel):
    id: str = Field(example="550e8400-e29b-41d4-a716-446655440000")
    invoice_number: str = Field(example="INV-2024-001")
    client: str = Field(example="Acme Corp")
    amount: float = Field(example=10000.0)
    due_date: datetime = Field(example="2024-12-31T23:59:59")
    status: str = Field(example="Draft")
    score: Optional[float] = Field(example=0.35)
    possible_financing: Optional[float] = Field(example=6500.0)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "invoice_number": "INV-2024-001",
                "client": "Acme Corp",
                "amount": 10000.0,
                "due_date": "2024-12-31T23:59:59",
                "status": "Draft",
                "score": 0.35,
                "possible_financing": 6500.0
            }
        }

class InvoiceCreateResponse(InvoiceBase):
    id: str = Field(example="550e8400-e29b-41d4-a716-446655440000")
    invoice_number: str = Field(example="INV-2024-001")
    client: str = Field(example="Acme Corp")
    amount: float = Field(example=10000.0)
    due_date: datetime = Field(example="2024-12-31T23:59:59")
    status: str = Field(example="Draft")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "invoice_number": "INV-2024-001",
                "client": "Acme Corp",
                "client_email": "contact@acme.com",
                "client_phone": "+33123456789",
                "client_address": "123 Business Street",
                "client_postal_code": "75001",
                "client_city": "Paris",
                "client_country": "FR",
                "client_vat_number": "FR12345678900",
                "amount": 10000.0,
                "currency": "EUR",
                "due_date": "2024-12-31T23:59:59",
                "description": "Consulting services",
                "status": "Draft"
            }
        }

class PdfUrlResponse(BaseModel):
    url: str = Field(
        description="URL temporaire pour télécharger le PDF de la facture",
        example="https://storage.googleapis.com/invoices/550e8400.pdf"
    )
    expires_at: datetime = Field(
        description="Date d'expiration de l'URL",
        example="2024-03-20T15:30:00"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://storage.googleapis.com/invoices/550e8400.pdf",
                "expires_at": "2024-03-20T15:30:00"
            }
        }

class SendInvoiceResponse(BaseModel):
    message: str = Field(
        description="Message de confirmation",
        example="Invoice sent successfully for signature"
    )

class PennylaneEstimateResponse(BaseModel):
    message: str = Field(
        description="Message de confirmation",
        example="Pennylane estimate created successfully"
    )
    estimate_id: str = Field(
        description="ID de l'estimation Pennylane",
        example="est_12345"
    )

class DemoInvoiceResponse(BaseModel):
    invoice_number: str = Field(example="INV-2024-001")
    client: str = Field(example="Acme Corp")
    amount: float = Field(example=10000.0)
    due_date: datetime = Field(example="2024-12-31T23:59:59")
    description: Optional[str] = Field(example="Consulting services")
    created_date: datetime = Field(example="2024-03-19T14:30:00")
    status: str = Field(example="Demo")
    score: float = Field(example=0.45)
    possible_financing: float = Field(example=5500.0)

    class Config:
        json_schema_extra = {
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