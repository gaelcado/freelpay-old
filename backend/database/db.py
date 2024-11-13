from .supabase_client import supabase
from fastapi import HTTPException
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
import logging

load_dotenv()
FRONTEND_URL = os.getenv('FRONTEND_URL')

async def find_user(username: str):
    try:
        response = supabase.from_('users')\
            .select('*')\
            .eq('username', username)\
            .execute()
        
        if not response.data:
            return None
            
        return response.data[0]
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

async def find_user_by_id(user_id: str):
    response = supabase.table('users').select('*').eq('id', user_id).execute()
    return response.data[0] if response.data else None

async def insert_user(username: str, email: str, password: str, siren_number: str = None, 
                     phone: str = None, address: str = None, is_admin: bool = False):
    try:
        user_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'password': password,
            'siren_number': siren_number,
            'phone': phone,
            'address': address,
            'is_admin': is_admin,
            'created_at': datetime.now().isoformat(),
            'id_document_status': 'not_uploaded'
        }
        
        response = supabase.from_('users')\
            .insert(user_data)\
            .execute()

        if not response.data:
            logging.error("No data returned from insert operation")
            raise HTTPException(status_code=400, detail="Failed to create user")
            
        logging.info(f"Successfully created user: {username}")
        return response.data[0]
        
    except Exception as e:
        logging.error(f"Error inserting user: {str(e)}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def update_user_profile(user_id: str, update_data: dict):
    response = supabase.table('users').update(update_data).eq('id', user_id).execute()
    return response.data[0] if response.data else None

async def create_invoice(invoice_data: dict):
    # Convertir les dates en chaînes ISO
    if 'created_date' in invoice_data:
        invoice_data['created_date'] = invoice_data['created_date'].isoformat()
    if 'due_date' in invoice_data:
        invoice_data['due_date'] = invoice_data['due_date'].isoformat()
    if 'financing_date' in invoice_data and invoice_data['financing_date']:
        invoice_data['financing_date'] = invoice_data['financing_date'].isoformat()
        
    invoice_data['id'] = str(uuid.uuid4())
    response = supabase.table('invoices').insert(invoice_data).execute()
    return response.data[0] if response.data else None

async def get_user_invoices(user_id: str):
    try:
        response = supabase.table('invoices')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

async def update_invoice_status(invoice_id: str, user_id: str, status: str):
    response = supabase.table('invoices')\
        .update({'status': status})\
        .eq('id', invoice_id)\
        .eq('user_id', user_id)\
        .execute()
    return response.data[0] if response.data else None 

async def update_user_id_document(username: str, file_path: str):
    try:
        full_url = f"{FRONTEND_URL}/user_documents/{os.path.basename(file_path)}"
        
        # Update the user record in Supabase
        response = supabase.table('users')\
            .update({
                'id_document': full_url,
                'id_document_status': 'pending'
            })\
            .eq('username', username)\
            .execute()
        
        logging.info(f"Update user ID document for {username}: {response}")
        
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=400, detail="Failed to update user document")
        
    except Exception as e:
        logging.error(f"Error updating user ID document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

async def find_user_by_email(email: str):
    try:
        response = supabase.from_('users')\
            .select('*')\
            .eq('email', email)\
            .execute()
        
        if not response.data:
            return None
            
        return response.data[0]
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

# Ajout de la fonction create_user
async def create_user(user_data: dict):
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = await find_user_by_email(user_data['email'])
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # S'assurer que l'ID est présent
        if 'id' not in user_data:
            user_data['id'] = str(uuid.uuid4())

        # Insérer l'utilisateur dans la table users
        response = supabase.table('users').insert(user_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
        return response.data[0]
        
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_invoice_by_id(invoice_id: str):
    response = supabase.table('invoices').select('*').eq('id', invoice_id).execute()
    return response.data[0] if response.data else None

async def update_invoice_pennylane_id(invoice_id: str, pennylane_id: str):
    response = supabase.table('invoices')\
        .update({'pennylane_id': pennylane_id})\
        .eq('id', invoice_id)\
        .execute()
    return response.data[0] if response.data else None

async def update_invoice_pandadoc_id(invoice_id: str, pandadoc_id: str):
    response = supabase.table('invoices')\
        .update({'pandadoc_id': pandadoc_id})\
        .eq('id', invoice_id)\
        .execute()
    return response.data[0] if response.data else None

async def get_invoice_by_pandadoc_id(pandadoc_id: str):
    response = supabase.table('invoices')\
        .select('*')\
        .eq('pandadoc_id', pandadoc_id)\
        .execute()
    return response.data[0] if response.data else None