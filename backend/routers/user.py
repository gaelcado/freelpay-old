import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from models.user import UserUpdate
from database.mongodb import update_user_profile, update_user_id_document
from dependencies import get_current_user
from fastapi.responses import JSONResponse
from typing import List

router = APIRouter()

# Définissez le répertoire de stockage des documents d'identité
UPLOAD_DIRECTORY = "user_documents"

# Assurez-vous que le répertoire existe
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Liste des types MIME autorisés pour les documents d'identité
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "application/pdf"]

@router.post("/upload-id")
async def upload_id_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Vérifiez le type MIME du fichier
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and PDF are allowed.")

    # Générez un nom de fichier unique
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{current_user['username']}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    try:
        # Sauvegardez le fichier
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()  # lire le contenu du fichier
            await buffer.write(content)  # écrire le contenu dans le nouveau fichier
        
        # Mettez à jour le document de l'utilisateur avec le chemin du fichier
        result = update_user_id_document(current_user['username'], file_path)
        
        if result.modified_count > 0:
            return JSONResponse(
                status_code=200,
                content={"message": "ID document uploaded successfully", "file_path": file_path}
            )
        else:
            # Si la mise à jour de la base de données a échoué, supprimez le fichier
            os.remove(file_path)
            raise HTTPException(status_code=500, detail="Failed to update user record")

    except Exception as e:
        # En cas d'erreur, assurez-vous de supprimer le fichier s'il a été créé
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.put("/update")
async def update_user_profile_route(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    print("Current user:", current_user)  # Add this line for debugging
    result = update_user_profile(current_user['_id'], user_update.model_dump(exclude_unset=True))
    if result.modified_count > 0:
        return {"message": "Profile updated successfully"}
    raise HTTPException(status_code=400, detail="Failed to update profile")