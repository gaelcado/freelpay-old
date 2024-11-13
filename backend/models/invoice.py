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