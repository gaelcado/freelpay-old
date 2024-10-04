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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")  # Load the frontend URL

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
        "id_document_status": "not_uploaded"  # Initialize the document status
    }
    return users_collection.insert_one(user)

def find_user(username):
    user = users_collection.find_one({"username": username})
    if user:
        user['_id'] = str(user['_id'])
    return user

def create_invoice(invoice_data):
    invoices_collection = db.invoices
    result = invoices_collection.insert_one(invoice_data)
    if result.inserted_id:
        return {**invoice_data, "id": str(result.inserted_id)}
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
    full_url = f"{FRONTEND_URL}/user_documents/{os.path.basename(file_path)}"
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"id_document": full_url}}
    )
    logging.debug(f"Update user ID document for {username}: {result.modified_count} document(s) modified.")
    return result