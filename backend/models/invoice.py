from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InvoiceCreate(BaseModel):
    invoice_number: str
    client: str
    amount: float
    due_date: datetime
    description: Optional[str] = None

class InvoiceInDB(BaseModel):
    id: str
    user_id: str
    invoice_number: str
    client: str
    amount: float
    due_date: datetime
    description: Optional[str] = None
    created_date: datetime
    status: str
    financing_date: Optional[datetime] = None
    possible_financing: Optional[float] = None
    score: Optional[float] = None

class Invoice(BaseModel):
    id: str
    invoice_number: str
    client: str
    amount: float