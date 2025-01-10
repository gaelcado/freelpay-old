import os
import requests
from datetime import datetime
from fastapi import HTTPException
import logging
import uuid

PENNYLANE_API_KEY = os.getenv('PENNYLANE_API_KEY')
PENNYLANE_API_URL = "https://app.pennylane.com/api/external/v1"

async def create_pennylane_estimate(invoice_data: dict):
    try:
        if not PENNYLANE_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Pennylane API key is missing"
            )

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {PENNYLANE_API_KEY}'
        }

        amount = float(invoice_data['amount'])
        
        # Construction d'un seul customer
        customer = {
            "source_id": str(uuid.uuid4()),
            "name": invoice_data['client'],
            "address": invoice_data.get('client_address') or '9 allée des cavaliers',
            "postal_code": invoice_data.get('client_postal_code') or '94700',
            "city": invoice_data.get('client_city') or 'Maisons-Alfort',
            "country_alpha2": invoice_data.get('client_country') or "FR",
            "phone": invoice_data.get('client_phone') or '0640315803',
            "emails": [invoice_data.get('client_email') or 'illan_knafou@hotmail.fr'],
            "payment_conditions": invoice_data.get('payment_conditions') or 'upon_receipt',
            "vat_number": invoice_data.get('client_vat_number') or '',
            "reg_no": "",
            "is_company": invoice_data.get('client_type') == 'company'
        }

        estimate_data = {
            "create_customer": True,
            "create_products": True,
            "update_customer": False,
            "estimate": {
                "customer": customer,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "deadline": invoice_data['due_date'].split('T')[0] if isinstance(invoice_data['due_date'], str) else invoice_data['due_date'].strftime("%Y-%m-%d"),
                "currency": "EUR",
                "pdf_invoice_subject": "Devis",
                "pdf_invoice_free_text": "",
                "special_mention": invoice_data.get('special_mentions') or '',
                "line_items": [
                    {
                        "currency_amount": amount,
                        "unit": "piece",
                        "vat_rate": "FR_200",
                        "description": invoice_data.get('description') or '',
                        "label": "Services",
                        "quantity": 1
                    }
                ]
            }
        }

        # Log de la requête
        logging.info(f"Full request URL: {PENNYLANE_API_URL}/customer_estimates")
        logging.info(f"Request headers: {headers}")
        logging.info(f"Request body: {estimate_data}")

        response = requests.post(
            f"{PENNYLANE_API_URL}/customer_estimates",
            headers=headers,
            json=estimate_data,
            timeout=10
        )
        
        # Log de la réponse
        logging.info(f"Response Status: {response.status_code}")
        logging.info(f"Response Headers: {dict(response.headers)}")
        logging.info(f"Response Body: {response.text}")

        if response.status_code == 500:
            raise HTTPException(
                status_code=502,
                detail=f"Pennylane service error: {response.text}"
            )
            
        if response.status_code not in (200, 201):
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Pennylane API error: {response.text}"
            )

        return response.json()
        
    except Exception as e:
        logging.error(f"Detailed error in create_pennylane_estimate: {str(e)}")
        logging.exception("Full traceback:")
        raise

async def send_estimate_for_signature(estimate_id: str, recipient_email: str):
    if not estimate_id:
        raise HTTPException(status_code=400, detail="Estimate ID is required")
    if not recipient_email:
        raise HTTPException(status_code=400, detail="Recipient email is required")

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {PENNYLANE_API_KEY}'
    }
    
    data = {
        "recipient_email": recipient_email,
        "message": "Please review and sign this quote"
    }
    
    try:
        # Log pour déboguer
        logging.info(f"Sending estimate {estimate_id} to {recipient_email}")
        logging.info(f"Request data: {data}")
        
        response = requests.post(
            f"{PENNYLANE_API_URL}/customer_estimates/{estimate_id}/send",
            headers=headers,
            json=data,
            timeout=10  # Ajout d'un timeout
        )
        
        # Log de la réponse
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response body: {response.text}")
        
        if response.status_code != 200:
            logging.error(f"Pennylane API error: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error sending estimate for signature: {response.text}"
            )
            
        return response.json()
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Timeout while sending estimate for signature"
        )
    except Exception as e:
        logging.error(f"Error sending estimate for signature: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending estimate for signature: {str(e)}"
        )