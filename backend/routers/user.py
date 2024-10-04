import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from models.user import UserUpdate
from database.mongodb import update_user_profile, update_user_id_document
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

        result = update_user_id_document(current_user['username'], file_path)

        logging.debug(f"Update result for user {current_user['username']}: {result.modified_count} document(s) modified.")

        if result.modified_count > 0:
            update_user_profile(current_user['_id'], {"id_document_status": "pending"})
            return JSONResponse(
                status_code=200,
                content={"message": "ID document uploaded successfully", "file_path": file_path}
            )
        else:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail="Failed to update user record")

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.put("/update")
async def update_user_profile_route(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user.get('id_document_status') == "pending":
        user_update.id_document = None  # Prevent ID document update

    result = update_user_profile(current_user['_id'], user_update.model_dump(exclude_unset=True))
    if result.modified_count > 0:
        return {"message": "Profile updated successfully"}
    raise HTTPException(status_code=400, detail="Failed to update profile")