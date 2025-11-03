from datetime import datetime

from sqlalchemy import text
from app.orders.dao import (
    BasketDao,
    OrderDao,
    OrderDeliveryDetailDao,
    OrderPickUpDetailsDao,
    PurchaseDao,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.orders.models import Order
from app.orders.schema import OrderPickUpDetailSchema
from app.products.dao import ProductDao
from app.logger import logger, create_msg_db_error
from app.stores.dao import StoreQuantityInfoDao
from app.tasks.tasks_rbmq import send_courier_notification
from app.users.models import User
from app.config import settings


class BasketService:
    def __init__(self, session: AsyncSession):
        self.basket_dao = BasketDao(session)
        self.product_dao = ProductDao(session)
        self.session: AsyncSession = session

    async def add_to_basket(self, product_id: int, user_id: int):
        """
        Добавление в корзину товара

        Добавляется товар с проверкой существования товара по id, который добавляется в корзину
        """

        try:
            product = await self.product_dao.find_by_filter_one(product_id=product_id)
            if not product:
                logger.warning(
                    "Product not found for adding to basket",
                    extra={"product_id": product_id, "user_id": user_id},
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Такого товара не существует",
                )

            await self.basket_dao.add_product(product_id, user_id)
            await self.session.commit()
            logger.info(
                "Product added to basket",
                extra={"product_id": product_id, "user_id": user_id},
            )
        except HTTPException:
            raise
        except Exception:
            logger.error(
                "Failed to add product to basket",
                extra={"product_id": product_id, "user_id": user_id},
                exc_info=True,
            )
            await self.session.rollback()
            raise HTTPException(
                status_code=500, detail="Ошибка при добавлении товара в корзину"
            )


class OrderService:
    def __init__(self, session):
        self.order_dao = OrderDao(session)

    async def get_orders(self, user_id: int) -> list[Order]:
        """Получение заказов пользователя"""
        try:
            orders = await self.order_dao.find_by_filter(user_id=user_id)
            logger.info(
                "Orders retrieved",
                extra={"user_id": user_id, "orders_count": len(orders)},
            )
            return orders[::-1]
        except Exception:
            logger.error(
                "Failed to get orders", extra={"user_id": user_id}, exc_info=True
            )
            raise HTTPException(status_code=500, detail="Ошибка при получении заказов")

    async def change_status(self, user: User, order_id: int, status: str):
        """
        Смена статуса заказа

        Смена статуса заказа с валидацией прав пользователя
        """

        try:
            if user.role not in ("seller", "admin"):
                logger.warning(
                    "Access denied for changing order status",
                    extra={
                        "user_id": user.user_id,
                        "role": user.role,
                        "order_id": order_id,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Нет доступа к изменению этого заказа",
                )

            await self.order_dao.change_status(status, order_id)
            await self.order_dao.session.commit()
            logger.info(
                "Order status changed",
                extra={
                    "order_id": order_id,
                    "new_status": status,
                    "changed_by": user.user_id,
                },
            )
        except HTTPException:
            raise
        except Exception:
            logger.error(
                "Failed to change order status",
                extra={"order_id": order_id, "status": status},
                exc_info=True,
            )
            await self.order_dao.session.rollback()
            raise HTTPException(
                status_code=500, detail="Ошибка при изменении статуса заказа"
            )

    async def delete_all_user_orders(self, user_id: int):
        """Удаление всех товаров пользователя"""
        try:
            result = await self.order_dao.delete_all_user_orders(user_id)
            logger.info("All user orders deleted", extra={"user_id": user_id})
            return result
        except Exception:
            logger.error(
                "Failed to delete all user orders",
                extra={"user_id": user_id},
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Ошибка при удалении заказов пользователя"
            )

    async def get_active_user_orders(self, user_id: int) -> list[Order]:
        """Получение актуальных заказов пользователя"""
        try:
            orders = await self.order_dao.get_active_user_orders(user_id)
            logger.info(
                "Active orders retrieved",
                extra={
                    "user_id": user_id,
                    "active_orders_count": len(orders) if orders else 0,
                },
            )
            return orders
        except Exception:
            logger.error(
                "Failed to get active user orders",
                extra={"user_id": user_id},
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Ошибка при получении активных заказов"
            )


class OrderPickUpService:
    def __init__(self, session):
        self.basket_dao = BasketDao(session)
        self.order_dao = OrderDao(session)
        self.order_pickup_details_dao = OrderPickUpDetailsDao(session)
        self.purchase_dao = PurchaseDao(session)
        self.session: AsyncSession = session
        self.store_quantity_info_dao = StoreQuantityInfoDao(session)

    async def create_order_pickup(
        self, user_id: int, order_details: OrderPickUpDetailSchema
    ):
        try:
            # Получаем product_id, которые лежат в корзине пользователя
            basket_of_user: list = await self.basket_dao.basket_of_user(user_id)
            if not basket_of_user:
                logger.warning(
                    "Empty basket for pickup order", extra={"user_id": user_id}
                )
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустая корзина")

            # Проверка есть ли все нужные товары в выбранном магазине
            products_with_quantity = await self.basket_dao.product_with_quantity(user_id)
            missing_products = await self.store_quantity_info_dao.get_missing_products(
                products_with_quantity, order_details["store_id"]
            )
            if missing_products:
                raise HTTPException(
                    409,
                    detail=f"Невозможно оформить заказ. В магазине не хватает товаров: {' '.join(map(str, missing_products))}",
                )
            # возможно стоит объединить в один запрос
            price: int = await self.basket_dao.price_of_basket(user_id)
            order_details["user_id"] = user_id

            # создаем запись в order_details и получаем id тк, в orders есть поле order_details_id
            order_pickup_detail_id: int = (await self.order_pickup_details_dao.add_and_return_id(**order_details))

            # Временный вариант, возможно стоит переписать на запрос, нельзя менять order_type_id в базе
            order = {
                "status": "new",
                "order_type_id": 2,
                "order_detail_id": order_pickup_detail_id,
                "user_id": user_id,
                "price": price,
                "date": datetime.now(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            order_id = await self.order_dao.add_and_return_id(**order)

            # Переносим все данные о покупке
            await self.purchase_dao.add_products_of_order(basket_of_user=basket_of_user, order_id=order_id)

            # Убираем наличие продуктов в магазине
            await self.store_quantity_info_dao.reduction_in_quantity(
                products_with_quantity, order_details["store_id"]
            )
            #################################
            # Сервис, который проводит оплату
            #################################
            await self.basket_dao.delete_basket_of_user(user_id)

            await self.session.commit()
            logger.info(
                "Pickup order created",
                extra={
                    "user_id": user_id,
                    "order_id": order_id,
                    "price": price,
                    "products_count": len(basket_of_user),
                },
            )
            return order_id
        except HTTPException:
            await self.session.rollback()
            raise
        except Exception:
            logger.error(
                "Failed to create pickup order",
                extra={"user_id": user_id},
                exc_info=True,
            )
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании заказа самовывоза")


class OrderDeliveryService:
    def __init__(self, session):
        self.basket_dao = BasketDao(session)
        self.order_dao = OrderDao(session)
        self.order_delivery_detail_dao = OrderDeliveryDetailDao(session)
        self.purchase_dao = PurchaseDao(session)
        self.session: AsyncSession = session

    async def create_order_delivery(self, user_id: int, order_details: dict):
        """Создание заказа с доставкой"""
        try:
            # Получаем product_id, которые лежат в корзине пользователя
            basket_of_user: list = await self.basket_dao.basket_of_user(user_id)
            if not basket_of_user:
                logger.warning("Empty basket for delivery order", extra={"user_id": user_id})
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустая корзина")

            # возможно стоит объединить в один запрос
            price: int = await self.basket_dao.price_of_basket(user_id)
            order_details["user_id"] = user_id

            # создаем запись в order_details и получаем id тк, в orders есть поле order_details_id
            order_delivery_detail_id: int = (await self.order_delivery_detail_dao.add_and_return_id(**order_details))

            # Временный вариант, возможно стоит переписать на запрос, нельзя менять id в базе
            order = {
                "status": "new",
                "order_type_id": 1,
                "order_detail_id": order_delivery_detail_id,
                "user_id": user_id,
                "price": price,
                "date": datetime.now(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            order_id = await self.order_dao.add_and_return_id(**order)

            # Переносим все данные о покупке
            await self.purchase_dao.add_products_of_order(basket_of_user=basket_of_user, order_id=order_id)

            #################################
            # Сервис, который проводит оплату
            #################################
            # Отправка письма на курьерскую службу

            products_with_quantity = await self.basket_dao.basket_of_user_with_quantity(user_id)

            logger.debug(
                msg="Sending emails",
                extra={"products_with_quantity": products_with_quantity},
            )
            send_courier_notification.delay(
                settings.COURIER_EMAIL,
                order_id,
                [[p, q] for p, q in products_with_quantity],
                order_details["address"],
            )

            await self.basket_dao.delete_basket_of_user(user_id)

            await self.session.commit()
            logger.info(
                "Delivery order created",
                extra={
                    "user_id": user_id,
                    "order_id": order_id,
                    "price": price,
                    "products_count": len(basket_of_user),
                },
            )
            return order_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to create delivery order",
                extra={"user_id": user_id},
                exc_info=True,
            )
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании заказа с доставкой") from e
