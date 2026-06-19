from typing import Annotated

from fastapi import Depends

from app.database import SessionDep
from app.orders.dao import OrderDao
from app.orders.services import OrderService


def get_order_dao(session: SessionDep):
    return OrderDao(session)


OrderDaoDep = Annotated[OrderDao, Depends(get_order_dao)]


def get_order_service(session: SessionDep, order_dao: OrderDaoDep):
    return OrderService(session, order_dao)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
