from fastapi import APIRouter
from schemas.orders import OrderRequest, OrderResponse
from services.order_service import create_order, fetch_order

router = APIRouter()

@router.post("/orders", response_model=OrderResponse, tags=["Orders"])
def place_order(order: OrderRequest):
    return create_order(order)

@router.get("/orders/{order_id}", tags=["Orders"])
def get_order_status(order_id: str):
    return fetch_order(order_id)
