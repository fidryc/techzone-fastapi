from fastapi import APIRouter
from app.database import SessionDep
from app.stores.dao import StoreQuantityInfoDao
from app.stores.schema import StoreQuantityInfoSchema

router = APIRouter(prefix="/store", tags=["Магазины"])


@router.get("/get_quantity_of_product/{store_id}/{product_id}")
async def get_quantity_of_product(
    session: SessionDep, store_id: int, product_id: int
) -> int:
    return await StoreQuantityInfoDao(session).get_quantity_of_product(
        store_id=store_id, product_id=product_id
    )
