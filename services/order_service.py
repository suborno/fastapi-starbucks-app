from fastapi import HTTPException
import uuid
from models.db import STARBUCKS_MENU, orders_db
from schemas.orders import OrderRequest, OrderResponse

def create_order(order: OrderRequest) -> OrderResponse:
    item = next((i for i in STARBUCKS_MENU if i["id"] == order.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found on the menu.")
    
    order_id = str(uuid.uuid4())
    orders_db[order_id] = {
        "order_id": order_id,
        "item_id": order.item_id,
        "item_name": item["name"],
        "quantity": order.quantity,
        "customer_name": order.customer_name,
        "status": "Preparing",
        "estimated_wait_minutes": 5 * order.quantity
    }
    
    return OrderResponse(
        order_id=order_id,
        status=orders_db[order_id]["status"],
        estimated_wait_minutes=orders_db[order_id]["estimated_wait_minutes"]
    )

def fetch_order(order_id: str) -> dict:
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order
