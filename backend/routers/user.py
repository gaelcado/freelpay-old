import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from models.user import UserUpdate, User
from database.db import update_user_profile, update_user_id_document
from dependencies import get_current_user
from fastapi.responses import JSONResponse
import logging

router = APIRouter()

UPLOAD_DIRECTORY = "user_documents"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "application/pdf"]

@router.post("/upload-id")
async def upload_id_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get('id_document_status') == "pending":
        raise HTTPException(status_code=403, detail="You cannot upload an ID document at this time.")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and PDF are allowed.")

    unique_filename = f"{current_user['username']}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    try:
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)

        result = await update_user_id_document(current_user['username'], file_path)

        await update_user_profile(current_user['id'], {"id_document_status": "pending"})

        return JSONResponse(
            status_code=200,
            content={"message": "ID document uploaded successfully", "file_path": file_path}
        )

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logging.error(f"Error uploading ID document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.put("/update")
async def update_user_profile_route(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user.get('id_document_status') == "pending":
        update_data = user_update.model_dump(exclude_unset=True)
        if 'id_document' in update_data:
            del update_data['id_document']
    else:
        update_data = user_update.model_dump(exclude_unset=True)

    result = await update_user_profile(current_user['id'], update_data)
    if result:
        return {"message": "Profile updated successfully"}
    raise HTTPException(status_code=400, detail="Failed to update profile")

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "siren_number": current_user.get("siren_number"),
        "phone": current_user.get("phone"),
        "address": current_user.get("address")
    }