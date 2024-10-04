from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import certifi
from bson import ObjectId
from datetime import datetime
import logging
import sys

load_dotenv()

MONGODB_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/freelpay_db")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "freelpay_db")

logging.basicConfig(level=logging.DEBUG)

print(f"Attempting to connect to MongoDB at {MONGODB_URI}")
try:
    logging.debug("Attempting to create MongoClient")
    #client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where()) #prod
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000) #test
    logging.debug("MongoClient created, attempting to get server info")
    client.server_info()
    logging.debug("Server info retrieved successfully")
    db = client[MONGODB_DB_NAME]
    users_collection = db.users
    print(f"Successfully connected to MongoDB. Database: {MONGODB_DB_NAME}")
    print(f"Collections: {db.list_collection_names()}")
    print(f"Users in the collection: {users_collection.count_documents({})}")
except Exception as err:
    logging.error(f"Failed to connect to MongoDB: {err}", exc_info=True)
    raise

print(f"Python version: {sys.version}")

def insert_user(username, email, hashed_password, siret_number, phone, address, is_admin=False):
    user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "siret_number": siret_number,
        "phone": phone,
        "address": address,
        "is_admin": is_admin,
        "is_verified": False
    }
    return users_collection.insert_one(user)

def find_user(username):
    user = users_collection.find_one({"username": username})
    if user:
        user['_id'] = str(user['_id'])
    return user

def get_user_meetings(username: str):
    meetings = list(db.contacts.find({"username": username}).sort("last_seen", -1))
    for meeting in meetings:
        meeting['_id'] = str(meeting['_id'])  # Convert ObjectId to string
    return meetings

def store_meeting_contact(username: str, contact_data: dict):
    existing_contact = db.contacts.find_one({"username": username, "name": contact_data['name']})
    
    current_date = datetime.now().isoformat()

    if existing_contact:
        # Update existing contact
        new_context = [f"{current_date}: {contact_data['context']}"] + existing_contact.get('context', [])
        update_data = {
            "name": contact_data['name'],
            "job": contact_data['job'],
            "last_seen": contact_data['last_seen'],
            "context": new_context,
            "networking_suggestions": contact_data['networking_suggestions']
        }
        db.contacts.update_one({"_id": existing_contact['_id']}, {"$set": update_data})
        result = db.contacts.find_one({"_id": existing_contact['_id']})
    else:
        # Insert new contact
        contact_data['username'] = username
        contact_data['context'] = [f"{current_date}: {contact_data['context']}"]
        result = db.contacts.insert_one(contact_data)
        result = db.contacts.find_one({"_id": result.inserted_id})
    
    # Convert ObjectId to string and ensure all fields are present
    if result:
        result['_id'] = str(result['_id'])
        result['name'] = result.get('name', 'Unknown')
        result['job'] = result.get('job', 'Not specified')
        result['last_seen'] = result.get('last_seen', current_date)
        result['context'] = result.get('context', [])
        result['networking_suggestions'] = result.get('networking_suggestions', [])
    
    return result

def update_contact(username: str, contact_id: str, updated_data: dict):
    # Remove '_id' from updated_data if it exists
    updated_data.pop('_id', None)
    
    # Ensure networking_suggestions and context are always arrays
    for field in ['networking_suggestions', 'context']:
        if field in updated_data:
            if not isinstance(updated_data[field], list):
                updated_data[field] = [updated_data[field]]
    
    result = db.contacts.find_one_and_update(
        {"_id": ObjectId(contact_id), "username": username},
        {"$set": updated_data},
        return_document=True
    )
    if result:
        result['_id'] = str(result['_id'])
    return result

def delete_contact(username: str, contact_id: str):
    result = db.contacts.find_one_and_delete(
        {"_id": ObjectId(contact_id), "username": username}
    )
    if result:
        result['_id'] = str(result['_id'])
    return result

def create_contact(username: str, contact_data: dict):
    current_date = datetime.now().isoformat()
    
    new_contact = {
        "username": username,
        "name": contact_data.get('name', 'New Contact'),
        "job": contact_data.get('job', 'Job Title'),
        "last_seen": contact_data.get('last_seen', current_date),
        "context": contact_data.get('context', 'Initial meeting'),
        "networking_suggestions": contact_data.get('networking_suggestions', ['Follow up'])
    }
    
    result = db.contacts.insert_one(new_contact)
    inserted_contact = db.contacts.find_one({"_id": result.inserted_id})
    
    if inserted_contact:
        inserted_contact['_id'] = str(inserted_contact['_id'])
    
    return inserted_contact

def update_user_admin_status(username: str, is_admin: bool):
    return users_collection.update_one(
        {"username": username},
        {"$set": {"is_admin": is_admin}}
    )

def create_invoice(invoice_data):
    invoices_collection = db.invoices
    invoice_data['_id'] = ObjectId()
    result = invoices_collection.insert_one(invoice_data)
    if result.inserted_id:
        invoice_data['id'] = str(invoice_data['_id'])
        del invoice_data['_id']
        return invoice_data
    return None

def get_user_invoices(username):
    invoices_collection = db.invoices
    invoices = list(invoices_collection.find({"user_id": username}))
    for invoice in invoices:
        invoice["id"] = str(invoice["_id"])
        del invoice["_id"]
    return invoices

def update_invoice_status(invoice_id, username, status):
    invoices_collection = db.invoices
    result = invoices_collection.update_one(
        {"_id": ObjectId(invoice_id), "user_id": username},
        {"$set": {"status": status}}
    )
    return result.modified_count > 0

def update_user_profile(user_id: str, update_data: dict):
    return users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

def update_user_id_document(username: str, file_path: str):
    return users_collection.update_one(
        {"username": username},
        {"$set": {"id_document": file_path}}
    )