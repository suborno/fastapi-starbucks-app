from pydantic import BaseModel

class OrderRequest(BaseModel):
    item_id: str
    quantity: int
    customer_name: str

class OrderResponse(BaseModel):
    order_id: str
    status: str
    estimated_wait_minutes: int
