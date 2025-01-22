from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OCRResult(BaseModel):
    invoice_number: str
    client: str
    amount: float
    due_date: datetime
    description: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_postal_code: Optional[str] = None
    client_city: Optional[str] = None
    client_vat_number: Optional[str] = None

class OCRResponse(BaseModel):
    invoice_id: str
    status: str
    ocr_results: Optional[OCRResult] = None
    error: Optional[str] = None 