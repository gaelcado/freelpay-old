import os
import requests
from fastapi import HTTPException
import logging
import os 
import asyncio
import time

from dotenv import load_dotenv
    
load_dotenv()

PANDADOC_API_URL = "https://api.pandadoc.com/public/v1"
PANDADOC_API_KEY = os.getenv("PANDADOC_API_KEY")

async def send_document_for_signature(file_url: str, recipient_email: str, recipient_name: str):
    try:
        headers = {
            'Authorization': f'API-Key {PANDADOC_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 1. Créer le document
        create_data = {
            "name": "Invoice for signature",
            "url": file_url,
            "recipients": [
                {
                    "email": recipient_email,
                    "first_name": recipient_name,
                    "role": "signer"
                }
            ],
            "parse_form_fields": True
        }
        
        create_response = requests.post(
            f"{PANDADOC_API_URL}/documents",
            headers=headers,
            json=create_data
        )
        
        if create_response.status_code != 201:
            raise HTTPException(
                status_code=create_response.status_code,
                detail=f"Error creating document: {create_response.text}"
            )
        
        document_id = create_response.json()['id']
        
        # 2. Attendre que le document soit en état "draft"
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            status_response = requests.get(
                f"{PANDADOC_API_URL}/documents/{document_id}",
                headers=headers
            )
            
            if status_response.status_code != 200:
                raise HTTPException(
                    status_code=status_response.status_code,
                    detail=f"Error checking document status: {status_response.text}"
                )
                
            status = status_response.json().get('status')
            if status == 'document.draft':
                break
                
            if status not in ['document.uploaded', 'document.draft']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unexpected document status: {status}"
                )
                
            attempt += 1
            await asyncio.sleep(1)  # Attendre 1 seconde entre chaque tentative
            
        if attempt >= max_attempts:
            raise HTTPException(
                status_code=408,
                detail="Timeout waiting for document to be ready"
            )
            
        # 3. Envoyer le document pour signature
        send_response = requests.post(
            f"{PANDADOC_API_URL}/documents/{document_id}/send",
            headers=headers,
            json={
                "message": "Please review and sign this document",
                "silent": False
            }
        )
        
        if send_response.status_code != 200:
            raise HTTPException(
                status_code=send_response.status_code,
                detail=f"Error sending document: {send_response.text}"
            )
            
        return send_response.json()
        
    except Exception as e:
        logging.error(f"Error in PandaDoc service: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        ) 