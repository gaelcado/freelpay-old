from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import Field
import uuid

class InvoiceCreate(BaseModel):
    invoice_number: str
    client: str
    amount: float
    due_date: datetime
    description: Optional[str] = None

class InvoiceInDB(BaseModel):
    id: Optional[str] = None
    user_id: str
    invoice_number: str
    client: str
    amount: float
    due_date: datetime
    description: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.now)
    status: str = "Ongoing"  # Set default status to "Ongoing"
    financing_date: Optional[datetime] = None
    possible_financing: Optional[float] = None
    score: Optional[float] = None

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    client: str
    amount: float
    due_date: datetime
    description: Optional[str] = None
    created_date: datetime
    status: Optional[str] = None
    financing_date: Optional[datetime] = None
    possible_financing: Optional[float] = None
    score: Optional[float] = None