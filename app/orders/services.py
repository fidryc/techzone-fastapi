

from app.orders.dao import BasketDao


class BasketService:
    def __init__(self, session):
        self.basket_dao = BasketDao(session)
        
    