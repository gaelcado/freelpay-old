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

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Récupérer la clé API OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")

class InvoiceData(BaseModel):
    invoice_number: str = Field(description="The unique identifier for the invoice")
    client: str = Field(description="The name of the client or company being billed")
    amount: float = Field(description="The total amount due on the invoice")
    due_date: datetime = Field(description="The date by which the invoice must be paid")
    description: str = Field(description="A brief description of the goods or services provided")

async def process_invoice(file):
    content = await file.read()
    images = convert_from_bytes(content)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image)
    
    logger.debug("Extracted text: %s", text)

    # Utiliser le LLM pour déterminer si le texte décrit une facture
    if not await is_invoice(text):
        logger.debug("Document is not an invoice.")
        return {"error": "Oops, it seems you uploaded the wrong document. Please upload an invoice to proceed."}
    
    # Utiliser ChatOpenAI pour extraire les informations de la facture
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=openai_api_key
    )
    
    parser = PydanticOutputParser(pydantic_object=InvoiceData)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant trained to extract invoice information from text. Please extract the following details: invoice number, client name, amount due, due date, and a brief description of the goods or services."),
        ("human", "Here's the text extracted from an invoice image. Please extract the required information:\n\n{text}"),
        ("human", "Please format your response as JSON according to the following schema:\n{format_instructions}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "text": text,
            "format_instructions": parser.get_format_instructions()
        })
        logger.debug("LLM result: %s", result)
        return result.dict()
    except Exception as e:
        logger.error("Error invoking LLM: %s", e)
        return {"error": "Failed to process the invoice. Please try again."}

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