from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
from pydantic.json import timedelta_isoformat

class InvoiceBase(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class InvoiceCreate(InvoiceBase):
    invoice_number: str
    client: str
    amount: float = Field(gt=0)
    due_date: datetime
    description: Optional[str] = None

class InvoiceInDB(InvoiceBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    invoice_number: str
    client: str
    amount: float = Field(gt=0)
    due_date: datetime
    description: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.now)
    status: str = "Draft"
    financing_date: Optional[datetime] = None
    possible_financing: Optional[float] = None
    score: Optional[float] = None

class Invoice(InvoiceBase):
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