from datetime import datetime
from pydantic import BaseModel

    
class OrderPickUpDetailSchema(BaseModel):
    store_id: int
    
class OrderDeliveryDetailSchema(BaseModel):
    address: str
    

class OrderSchema(BaseModel):
    order_id: int
    status: str
    order_type_id: int
    order_detail_id: int
    user_id: int
    date: datetime
    price: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
    