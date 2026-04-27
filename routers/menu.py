from fastapi import APIRouter
from models.db import STARBUCKS_MENU

router = APIRouter()

@router.get("/menu", tags=["Menu"])
def get_menu():
    return {"menu": STARBUCKS_MENU}
