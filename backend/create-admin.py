import sys
sys.path.append('.')  # Add the current directory to Python path

from pymongo import MongoClient
from passlib.context import CryptContext

# Spécifiez l'URI MongoDB directement ici
MONGO_URI = "mongodb://localhost:27017/users_db"  # Modifiez ceci selon votre configuration

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(username: str, email: str, password: str):
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    users_collection = db.users

    hashed_password = pwd_context.hash(password)
    user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "is_admin": True
    }
    
    result = users_collection.insert_one(user)
    if result.inserted_id:
        print(f"Admin user {username} created successfully")
    else:
        print("Failed to create admin user")

if __name__ == "__main__":
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    create_admin_user(username, email, password)
