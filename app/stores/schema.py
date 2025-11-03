from pydantic import BaseModel


class StoreQuantityInfoSchema(BaseModel):
    stores_quantity_info_id: int
    store_id: int
    product_id: int
    quantity: int
