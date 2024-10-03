from fastapi import APIRouter, Depends, HTTPException
from models.user import UserBioUpdate
from database.mongodb import update_user_bio
from dependencies import get_current_user

router = APIRouter()

@router.put("/update-bio")
async def update_user_bio(bio_update: UserBioUpdate, current_user: dict = Depends(get_current_user)):
    result = update_user_bio(current_user['username'], bio_update.bio)
    if result.modified_count > 0:
        return {"message": "Bio updated successfully"}
    raise HTTPException(status_code=400, detail="Failed to update bio")