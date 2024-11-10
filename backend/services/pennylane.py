import os
import requests
from datetime import datetime
from fastapi import HTTPException
import logging
from database.db import update_invoice_pennylane_id

PENNYLANE_API_KEY = os.getenv('PENNYLANE_API_KEY')
PENNYLANE_API_URL = "https://app.pennylane.com/api/external/v1"

async def create_pennylane_estimate(invoice_data: dict):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {PENNYLANE_API_KEY}'
    }

    logging.info(f"Creating Pennylane estimate with data: {invoice_data}")

    estimate_data = {
        "create_customer": True,
        "update_customer": False,
        "create_products": True,
        "estimate": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "deadline": invoice_data['due_date'],
            "external_id": str(invoice_data['id']),
            "pdf_invoice_subject": f"Quote {invoice_data['invoice_number']}",
            "draft": True,
            "currency": "EUR",
            "special_mention": invoice_data.get('description', ''),
            "language": "fr_FR",
            "customer": {
                "customer_type": "company",
                "name": invoice_data['client'],
                "address": invoice_data.get('client_address', ''),
                "postal_code": invoice_data.get('client_postal_code', ''),
                "city": invoice_data.get('client_city', ''),
                "country_alpha2": "FR"
            },
            "line_items": [
                {
                    "label": invoice_data.get('description', 'Professional Services'),
                    "quantity": 1,
                    "currency_amount": float(invoice_data['amount']),
                    "unit": "service",
                    "vat_rate": "FR_200"
                }
            ]
        }
    }

    try:
        logging.info(f"Sending request to Pennylane with data: {estimate_data}")
        response = requests.post(
            f"{PENNYLANE_API_URL}/customer_estimates",
            headers=headers,
            json=estimate_data
        )
        
        logging.info(f"Pennylane response status: {response.status_code}")
        logging.info(f"Pennylane response body: {response.text}")
        
        if response.status_code not in (200, 201):
            logging.error(f"Pennylane API error: {response.text}")
            raise HTTPException(status_code=response.status_code, 
                              detail=f"Error creating estimate in Pennylane: {response.text}")
        
        return response.json()
    except Exception as e:
        logging.error(f"Error creating Pennylane estimate: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Error creating estimate in Pennylane: {str(e)}")