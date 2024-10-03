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

# Load OpenAI API key from environment variable
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
    
    # Use ChatOpenAI to extract invoice information
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview", openai_api_key=openai_api_key)
    
    parser = PydanticOutputParser(pydantic_object=InvoiceData)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant trained to extract invoice information from text. Please extract the following details: invoice number, client name, amount due, due date, and a brief description of the goods or services."),
        ("human", "Here's the text extracted from an invoice image. Please extract the required information:\n\n{text}"),
        ("human", "Please format your response as JSON according to the following schema:\n{format_instructions}")
    ])
    
    chain = prompt | llm | parser
    
    result = chain.invoke({
        "text": text,
        "format_instructions": parser.get_format_instructions()
    })
    
    return result.dict()