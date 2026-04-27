from fastapi import FastAPI
from routers import menu, orders

app = FastAPI(
    title="Starbucks Microservice API", 
    description="A FastAPI service for a Starbucks menu and ordering system.", 
    version="1.0.0"
)

# Include routers
app.include_router(menu.router)
app.include_router(orders.router)

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Starbucks Microservice API!"}
