from typing import Dict

# Mock Data
STARBUCKS_MENU = [
    {"id": "item_1", "name": "Caffe Latte", "price": 4.50, "category": "Hot Coffees"},
    {"id": "item_2", "name": "Caramel Macchiato", "price": 5.25, "category": "Hot Coffees"},
    {"id": "item_3", "name": "Mocha Frappuccino", "price": 5.75, "category": "Frappuccino Blended Beverages"},
    {"id": "item_4", "name": "Iced Brown Sugar Oatmilk Shaken Espresso", "price": 5.95, "category": "Cold Coffees"},
]

# Mock Database
orders_db: Dict[str, dict] = {}
