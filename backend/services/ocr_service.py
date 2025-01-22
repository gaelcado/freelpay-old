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

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Récupérer la clé API OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")

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

async def process_invoice(file):
    try:
        content = await file.read()
        images = convert_from_bytes(content)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        
        logger.debug("Extracted text: %s", text)

        # Vérifier si c'est une facture
        if not await is_invoice(text):
            return {
                "error": "Document is not an invoice"
            }
        
        # Extraire les informations avec le LLM
        extracted_data = await extract_invoice_data(text)
        if not extracted_data:
            return {"error": "Failed to extract invoice data"}
        
        # Convertir l'OCRResult en dictionnaire avec les champs requis
        return {
            "invoice_number": extracted_data.invoice_number,
            "client": extracted_data.client,
            "amount": extracted_data.amount,
            "due_date": extracted_data.due_date,
            "description": extracted_data.description,
            "client_email": extracted_data.client_email,
            "client_phone": extracted_data.client_phone,
            "client_address": extracted_data.client_address,
            "client_postal_code": extracted_data.client_postal_code,
            "client_city": extracted_data.client_city,
            "client_vat_number": extracted_data.client_vat_number
        }
        
    except Exception as e:
        logger.error(f"Error processing invoice: {str(e)}")
        return {"error": str(e)}

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
                You MUST extract and return ALL these required fields:
                - invoice_number (from Invoice reference)
                - client (company being billed)
                - amount (total amount as number)
                - due_date (in YYYY-MM-DD format)
                
                Return the data as a JSON with this structure:
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
                    "client_vat_number": "string or null"
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