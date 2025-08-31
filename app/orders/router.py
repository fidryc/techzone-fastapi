from fastapi import APIRouter, Depends, Request, Response

from app.database import get_session
from app.orders.services import BasketService
from app.products.services import ProductService
from app.users.servises import UserService

router = APIRouter(
    '/orders',
    ['Заказы']
)


@router.post('/add_products_in_basket')
async def add_products_in_basket(request: Request, response: Response, product_id: int, session=Depends(get_session)):
    user_service = UserService(session)
    user = await user_service.get_user_from_token(request, response)
    basket_service = BasketService(session)