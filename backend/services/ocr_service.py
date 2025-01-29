import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
import logging
from typing import Optional
import json
from openai import OpenAI
from models.ocr import OCRResult
from database.db import update_invoice

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Récupérer les variables d'environnement
openai_api_key = os.getenv("OPENAI_API_KEY")

async def process_invoice_async(invoice_id: str, file_content: bytes):
    """
    Process invoice OCR asynchronously and update the database
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
            logger.error("Document is not an invoice")
            await update_invoice(invoice_id, {
                "status": "OCR_FAILED",
                "error": "Document is not an invoice"
            })
            return

        # Extraire les informations avec le LLM
        extracted_data = await extract_invoice_data(text)
        if not extracted_data:
            logger.error("Failed to extract invoice data")
            await update_invoice(invoice_id, {
                "status": "OCR_FAILED",
                "error": "Failed to extract invoice data"
            })
            return

        # Mettre à jour la facture dans la base de données
        update_data = {
            "status": "OCR_COMPLETED",
            **extracted_data.dict()
        }
        
        logger.debug(f"Updating invoice {invoice_id} with data: {update_data}")
        await update_invoice(invoice_id, update_data)
        logger.info(f"Successfully processed invoice {invoice_id}")

    except Exception as e:
        logger.error(f"Error processing invoice: {str(e)}")
        await update_invoice(invoice_id, {
            "status": "OCR_FAILED",
            "error": str(e)
        })

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
        
        # Conversion de la date en datetime
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