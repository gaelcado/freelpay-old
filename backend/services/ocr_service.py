import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import os
import logging
from typing import Optional
import json
from openai import OpenAI
from models.ocr import OCRResult
import httpx
import asyncio

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Récupérer les variables d'environnement
openai_api_key = os.getenv("OPENAI_API_KEY")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
OCR_WEBHOOK_SECRET = os.getenv("OCR_WEBHOOK_SECRET")

class InvoiceData(BaseModel):
    invoice_number: str = Field(description="The unique identifier for the invoice")
    client: str = Field(description="The name of the client or company being billed")
    client_email: Optional[str] = Field(description="Client's email address")
    client_phone: Optional[str] = Field(description="Client's phone number")
    client_address: Optional[str] = Field(description="Client's address")
    client_postal_code: Optional[str] = Field(description="Client's postal code")
    client_city: Optional[str] = Field(description="Client's city")
    client_country: str = Field(description="Client's country code", default="FR")
    client_siren: Optional[str] = Field(description="Client's SIREN number")
    client_vat_number: Optional[str] = Field(description="Client's VAT number")
    amount: float = Field(description="The total amount due on the invoice")
    due_date: datetime = Field(description="The date by which the invoice must be paid")
    description: str = Field(description="A brief description of the goods or services provided")

class InvoiceExtraction(BaseModel):
    invoice_number: str
    client: str
    amount: float
    due_date: str
    description: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    client_postal_code: Optional[str] = None
    client_city: Optional[str] = None
    client_vat_number: Optional[str] = None

async def process_invoice_async(invoice_id: str, file_content: bytes):
    """
    Process invoice OCR asynchronously and send results via webhook
    """
    try:
        # Convertir le PDF en images
        images = convert_from_bytes(file_content)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        
        logger.debug("Extracted text: %s", text)

        # Vérifier si c'est une facture
        if not await is_invoice(text):
            await send_ocr_result(invoice_id, error="Document is not an invoice")
            return

        # Extraire les informations avec le LLM
        extracted_data = await extract_invoice_data(text)
        if not extracted_data:
            await send_ocr_result(invoice_id, error="Failed to extract invoice data")
            return

        # Envoyer les résultats via webhook
        await send_ocr_result(
            invoice_id=invoice_id,
            ocr_results=extracted_data.dict()
        )

    except Exception as e:
        logger.error(f"Error processing invoice: {str(e)}")
        await send_ocr_result(invoice_id, error=str(e))

async def send_ocr_result(invoice_id: str, ocr_results: dict = None, error: str = None):
    """
    Send OCR results to the webhook endpoint
    """
    webhook_url = f"{APP_URL}/api/webhooks/ocr/result"
    
    if not OCR_WEBHOOK_SECRET:
        logger.error("OCR_WEBHOOK_SECRET is not set")
        return
        
    payload = {
        "invoice_id": invoice_id,
        "ocr_results": ocr_results,
        "error": error
    }
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Secret": str(OCR_WEBHOOK_SECRET)  # Ensure it's a string
    }

    logger.debug(f"Sending OCR results to {webhook_url}")
    logger.debug(f"Payload: {payload}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"Successfully sent OCR results for invoice {invoice_id}")
        except Exception as e:
            logger.error(f"Failed to send OCR results: {str(e)}")
            logger.error(f"Response status: {getattr(e, 'status_code', 'unknown')}")
            logger.error(f"Response text: {getattr(e, 'text', 'unknown')}")

async def is_invoice(text):
    # Utiliser le LLM pour déterminer si le texte décrit une facture
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=openai_api_key
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant trained to determine if a given text describes an invoice. An invoice typically includes details such as invoice number, client name, amount due, and due date."),
        ("human", f"Does the following text describe an invoice? Please respond with 'yes' or 'no'.\n\n{text}")
    ])
    
    try:
        response = llm.invoke(prompt.format_messages())
        logger.debug("LLM response for invoice check: %s", response.content)
        return response.content.strip().lower() == "yes"
    except Exception as e:
        logger.error("Error checking if document is an invoice: %s", e)
        return False

async def extract_invoice_data(text):
    try:
        client = OpenAI(api_key=openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": """You are an invoice data extraction assistant. 
                Extract ALL these fields from the invoice:
                - invoice_number (required): The invoice reference number
                - client (required): The company being billed
                - amount (required): The total amount as a number
                - due_date (required): The payment due date in YYYY-MM-DD format
                - description: Brief description of services
                - client_email: Client's email if present
                - client_phone: Client's phone if present
                - client_address: Client's address if present
                - client_postal_code: Client's postal code if present
                - client_city: Client's city if present
                - client_vat_number: Client's VAT number if present
                - client_siren: Client's SIREN number (9 digits) if present

                Return the data as a JSON with this exact structure:
                {
                    "invoice_number": "string",
                    "client": "string",
                    "amount": number,
                    "due_date": "YYYY-MM-DD",
                    "description": "string or null",
                    "client_email": "string or null",
                    "client_phone": "string or null",
                    "client_address": "string or null",
                    "client_postal_code": "string or null",
                    "client_city": "string or null",
                    "client_vat_number": "string or null",
                    "client_siren": "string or null"
                }"""},
                {"role": "user", "content": f"Extract ALL required fields from this invoice text and return as JSON: {text}"}
            ]
        )
        
        if not response.choices[0].message.content:
            logger.error("No content in OpenAI response")
            return None
            
        parsed_data = json.loads(response.choices[0].message.content)
        logger.debug(f"Parsed invoice data: {parsed_data}")
        
        # Vérification des champs requis
        required_fields = ["invoice_number", "client", "amount", "due_date"]
        missing_fields = [field for field in required_fields if not parsed_data.get(field)]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return None
        
        # Conversion de la date en datetime avant de créer l'OCRResult
        try:
            parsed_data["due_date"] = datetime.strptime(parsed_data["due_date"], "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return None
        
        # Validation avec OCRResult
        try:
            return OCRResult(**parsed_data)
        except Exception as e:
            logger.error(f"Failed to create OCRResult: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error invoking OpenAI: {str(e)}")
        return None