from fastapi import APIRouter, Depends, HTTPException
from models.ai import AIQuery
from services.ai_service import process_ai_query
from dependencies import get_current_user
from database.mongodb import get_user_meetings

router = APIRouter()

@router.post("/query")
async def ai_query(query: AIQuery, current_user: dict = Depends(get_current_user)):
    try:
        contacts = get_user_meetings(current_user['username'])
        answer = process_ai_query(query.query, contacts)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
