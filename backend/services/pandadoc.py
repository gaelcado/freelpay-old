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
        
        # 1. Créer le document avec les champs de signature
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
            "fields": {
                "signature": {
                    "name": "Signature",
                    "type": "signature",
                    "role": "signer",
                    "required": True,
                    "page_number": 1,
                    "x": 100,
                    "y": 700,
                    "width": 200,
                    "height": 50
                },
                "date": {
                    "name": "Date",
                    "type": "date",
                    "role": "signer",
                    "required": True,
                    "page_number": 1,
                    "x": 350,
                    "y": 700,
                    "width": 150,
                    "height": 50
                }
            },
            "metadata": {
                "source": "pennylane"
            },
            "parse_form_fields": False,
            "tags": ["signature_required"]
        }
        
        # Log de la requête pour déboguer
        logging.info(f"Creating document with data: {create_data}")
        
        create_response = requests.post(
            f"{PANDADOC_API_URL}/documents",
            headers=headers,
            json=create_data
        )
        
        # Log de la réponse pour déboguer
        logging.info(f"Create document response: {create_response.text}")
        
        if create_response.status_code != 201:
            raise HTTPException(
                status_code=create_response.status_code,
                detail=f"Error creating document: {create_response.text}"
            )
        
        document_id = create_response.json()['id']
        
        # 2. Attendre que le document soit en état "document.draft"
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            status_response = requests.get(
                f"{PANDADOC_API_URL}/documents/{document_id}",
                headers=headers
            )
            
            status = status_response.json().get('status')
            if status == 'document.draft':
                break
                
            attempt += 1
            await asyncio.sleep(1)
        
        # 3. Envoyer le document
        send_response = requests.post(
            f"{PANDADOC_API_URL}/documents/{document_id}/send",
            headers=headers,
            json={
                "message": "Please review and sign this document",
                "subject": "Document ready for signature",
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

async def setup_pandadoc_webhook(app_url: str):
    try:
        # S'assurer que l'URL se termine par /webhook/pandadoc
        webhook_url = app_url.rstrip('/') + '/webhook/pandadoc'
        
        headers = {
            'Authorization': f'API-Key {PANDADOC_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        webhook_data = {
            "name": "Document Status Webhook",
            "url": webhook_url,
            "events": ["document_state_changed"],
            "active": True
        }
        
        logging.info(f"Setting up webhook with URL: {webhook_url}")
        
        response = requests.post(
            f"{PANDADOC_API_URL}/webhook-subscriptions",
            headers=headers,
            json=webhook_data
        )
        
        if response.status_code not in (200, 201):
            logging.error(f"Failed to setup PandaDoc webhook: {response.text}")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"Error setting up PandaDoc webhook: {str(e)}")
        return False