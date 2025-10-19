from sqladmin import Admin, ModelView
from app.database import engine
from app.orders.models import Order, OrderType, OrderPickUpDetail, OrderDeliveryDetail, Purchase, Basket
from app.users.models import RefreshTokenBL, User
from app.stores.models import Store, StoreQuantityInfo
from app.products.models import (
    Category, 
    Product, 
    Review, 
    FavoriteProduct, 
    HistoryQueryUser
)


class UserAdmin(ModelView, model=User):
    column_list = [User.user_id, User.email, User.number, User.role]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    category_icon = "fa-solid fa-user"
    
    can_create = True
    can_edit = False
    can_delete = True
    can_view_details = True
    
    column_details_exclude_list = [User.hashed_password]
    column_searchable_list = [User.email, User.number, User.role]
    column_default_sort = [(User.role, True)]
    column_sortable_list = [User.email, User.user_id]
    page_size = 25


class RefreshTokenBLAdmin(ModelView, model=RefreshTokenBL):
    name = "RefreshToken"
    name_plural = "Refresh Tokens"
    icon = "fa-solid fa-key"
    column_list = [c.name for c in RefreshTokenBL.__table__.c]
    can_create = False
    can_edit = False


class OrderAdmin(ModelView, model=Order):
    name = "Order"
    name_plural = "Orders"
    icon = "fa-solid fa-box"
    column_list = [Order.order_id, Order.price, Order.created_at, Order.user_id, Order.status] + [Order.relationship_user]
    column_sortable_list = [Order.created_at, Order.price]
    column_searchable_list = [Order.status]
    column_default_sort = [(Order.created_at, True)]
    can_create = False


class StoreAdmin(ModelView, model=Store):
    name = "Store"
    name_plural = "Stores"
    icon = "fa-solid fa-store"
    column_list = [c.name for c in Store.__table__.c] + [Store.relationship_user]
    column_searchable_list = [Store.title]
    column_default_sort = [(Store.title, True)]


class StoreQuantityInfoAdmin(ModelView, model=StoreQuantityInfo):
    name = "Store Quantity"
    name_plural = "Stores Quantity Info"
    icon = "fa-solid fa-warehouse"
    column_list = [c.name for c in StoreQuantityInfo.__table__.c] + [StoreQuantityInfo.relationship_store, StoreQuantityInfo.relationship_product]
    column_searchable_list = [StoreQuantityInfo.store_id, StoreQuantityInfo.product_id]


class CategoryAdmin(ModelView, model=Category):
    name = "Category"
    name_plural = "Categories"
    icon = "fa-solid fa-list"
    column_list = [c.name for c in Category.__table__.c]


class ProductAdmin(ModelView, model=Product):
    name = "Product"
    name_plural = "Products"
    icon = "fa-solid fa-laptop"
    column_list = [c.name for c in Product.__table__.c if c.name not in ('specification', 'description')] + [Product.relationship_category]
    column_searchable_list = [Product.title]
    column_sortable_list = [Product.price, Product.rating]
    page_size = 20


class ReviewAdmin(ModelView, model=Review):
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-solid fa-comment"
    column_list = [c.name for c in Review.__table__.c] + [Review.relationship_user, Review.relationship_product]


class FavoriteProductAdmin(ModelView, model=FavoriteProduct):
    name = "Favorite Product"
    name_plural = "Favorite Products"
    icon = "fa-solid fa-heart"
    column_list = [c.name for c in FavoriteProduct.__table__.c] + [FavoriteProduct.relationship_user, FavoriteProduct.relationship_product]


class HistoryQueryUserAdmin(ModelView, model=HistoryQueryUser):
    name = "Search History"
    name_plural = "Search History Users"
    icon = "fa-solid fa-clock-rotate-left"
    column_list = [c.name for c in HistoryQueryUser.__table__.c] + [HistoryQueryUser.relationship_user]


class OrderTypeAdmin(ModelView, model=OrderType):
    name = "Order Type"
    name_plural = "Order Types"
    column_list = [c.name for c in OrderType.__table__.c]


class OrderPickUpDetailAdmin(ModelView, model=OrderPickUpDetail):
    name = "PickUp Detail"
    name_plural = "Order PickUps"
    column_list = [c.name for c in OrderPickUpDetail.__table__.c] + [OrderPickUpDetail.relationship_user, OrderPickUpDetail.relationship_store]


class OrderDeliveryDetailAdmin(ModelView, model=OrderDeliveryDetail):
    name = "Delivery Detail"
    name_plural = "Order Deliveries"
    column_list = [c.name for c in OrderDeliveryDetail.__table__.c] + [OrderDeliveryDetail.relationship_user]


class PurchaseAdmin(ModelView, model=Purchase):
    name = "Purchase"
    name_plural = "Purchases"
    column_list = [c.name for c in Purchase.__table__.c] + [Purchase.relationship_order, Purchase.relationship_product]


class BasketAdmin(ModelView, model=Basket):
    name = "Basket"
    name_plural = "Baskets"
    column_list = [c.name for c in Basket.__table__.c] + [Basket.relationship_user, Basket.relationship_product]