import os
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import httpx
from fastapi import HTTPException

openai_api_key = os.getenv("OPENAI_API_KEY")
SIREN_API_BASE_URL = "https://data.siren-api.fr/v3"
SIREN_API_KEY = os.getenv("SIREN_API_KEY")

llm = ChatOpenAI(temperature=0.2, model_name="gpt-4o-mini", openai_api_key=openai_api_key)

async def get_siren_data(siren: str):
    if not SIREN_API_KEY:
        raise HTTPException(status_code=500, detail="SIREN API key is not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SIREN_API_BASE_URL}/unites_legales/{siren}",
                headers={"X-Client-Secret": SIREN_API_KEY}
            )
            
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        return None

async def calculate_score(invoice_data, user_siren=None):
    # Get SIREN data if available
    siren_data = None
    if user_siren:
        siren_data = await get_siren_data(user_siren)
    
    system_prompt = """You are a risk assessment AI for invoice financing. 
    Provide a risk score between 0 and 1, where 0 is lowest risk and 1 is highest risk.
    Consider both the invoice data and the company's SIREN information when available."""
    
    user_prompt = f"""
    Given the following information, calculate a risk score:
    
    Invoice Data:
    - Invoice Number: {invoice_data['invoice_number']}
    - Amount: {invoice_data['amount']}
    - Client: {invoice_data['client']}
    - Due Date: {invoice_data['due_date']}
    - Description: {invoice_data['description']}
    """
    
    if siren_data:
        user_prompt += f"""
        Company SIREN Data:
        - Company Age: {siren_data.get('age_entreprise')}
        - Legal Status: {siren_data.get('forme_juridique')}
        - Activity Code: {siren_data.get('activite_principale')}
        - Employee Count: {siren_data.get('effectif')}
        """
    
    user_prompt += "\nRespond with only a number between 0 and 1, representing the risk score."

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    llm_response = llm.invoke(messages)
    score = float(llm_response.content.strip())
    return score