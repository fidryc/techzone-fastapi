from pydantic import BaseModel

    
class OrderPickUpDetailSchema(BaseModel):
    store_id: int
    
class OrderDeliveryDetailSchema(BaseModel):
    address: str
    