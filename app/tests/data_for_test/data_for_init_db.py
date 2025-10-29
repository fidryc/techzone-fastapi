"""
Тестовые данные для базы данных.
Порядок вставки соблюдает зависимости Foreign Keys.
"""
from datetime import datetime, timezone

# ============================================
# 1. STORES (независимая таблица)
# ============================================
STORES = [
    {
        "store_id": 1,
        "title": "Магазин на Арбате",
        "opening_hours": "Пн-Пт: 9:00-21:00, Сб-Вс: 10:00-20:00"
    },
    {
        "store_id": 2,
        "title": "Магазин в ТРЦ МегаМолл",
        "opening_hours": "Пн-Вс: 10:00-22:00"
    },
    {
        "store_id": 3,
        "title": "Магазин на Невском",
        "opening_hours": "Пн-Пт: 8:00-20:00, Сб-Вс: выходной"
    }
]

# ============================================
# 2. USERS (зависит от stores через pickup_store_id)
# ============================================
USERS = [
    {
        "user_id": 1,
        "email": "admin@shop.com",
        "hashed_password": "$2b$12$u30fnak1CpXFe0xYjIVgve3j.XkqEyaywFpl9it.HEl3Xrh7p2.le",  # Хеш для 'admin123'
        "city": "Москва",
        "home_address": "ул. Арбат, 1",
        "pickup_store_id": 1,
        "number": "+79991234567",
        "role": "admin"
    },
    {
        "user_id": 2,
        "email": "seller@shop.com",
        "hashed_password": "$2b$12$dJNDthEmismYAhvJV6nteefii1mRLGjFDrCE6YafLBdV.F5v1tBWm",  # Хеш для 'seller123'
        "city": "Москва",
        "home_address": "ул. Ленина, 5",
        "pickup_store_id": 2,
        "number": "+79992345678",
        "role": "seller"
    },
    {
        "user_id": 3,
        "email": "user1@gmail.com",
        "hashed_password": "$2b$12$vX2o.tN7RK4eOZWiTZGoGe/h3jDq/3tq3c4PwJK.qJOOqABs8lKTy",  # Хеш для 'user123'
        "city": "Москва",
        "home_address": "пр. Мира, 25",
        "pickup_store_id": 1,
        "number": "+79993456789",
        "role": "user"
    },
    {
        "user_id": 4,
        "email": "user2@gmail.com",
        "hashed_password": "$2b$12$IQU/0PosqpIuWw162BhuVePBZgt6P4TUWaUAYNSKyUE17Nv2o1GHO",  # Хеш для 'pass123'
        "city": "Санкт-Петербург",
        "home_address": "ул. Невский проспект, 10",
        "pickup_store_id": None,
        "number": "+79994567890",
        "role": "user"
    },
    {
        "user_id": 5,
        "email": "buyer@example.com",
        "hashed_password": "$2b$12$Mnl7h59HW8OH1uvAG7WF0eTIVAep4Wb0GGTQKPrgMeBU/8onvY9/y", # Пароль "pwd"
        "city": "Казань",
        "home_address": "ул. Баумана, 15",
        "pickup_store_id": 3,
        "number": "+79995678901",
        "role": "user"
    },
    {
        "user_id": 6,
        "email": "clear@gmail.com",
        "hashed_password": "$2b$12$dcqTgTnkWRVmQtFdlP4MeOC2Cjj4yKqiHYlcCGNelDEHvev8Xl.Uy", # для clear123
        "city": "Казань",
        "home_address": "ул. Баумана, 15",
        "pickup_store_id": 3,
        "number": "+79895678901",
        "role": "user"
    }
]

# ============================================
# 3. CATEGORIES (независимая таблица)
# ============================================
CATEGORIES = [
    {
        "category_id": 1,
        "title": "Телевизоры",
        "class_name": "TvSchema"
    },
    {
        "category_id": 2,
        "title": "Ноутбуки",
        "class_name": "LaptopSchema"
    },
    {
        "category_id": 3,
        "title": "Смартфоны",
        "class_name": "SmartphoneSchema"
    },
    {
        "category_id": 4,
        "title": "Холодильники",
        "class_name": "RefrigeratorSchema"
    }
]

# ============================================
# 4. PRODUCTS (зависит от categories)
# ============================================
PRODUCTS = [
    {
        "product_id": 1,
        "title": "Samsung QLED 55\" 4K Smart TV",
        "category_id": 1,
        "specification": {
            "screen_size": 55,
            "resolution": "4K",
            "smart_tv": True,
            "hdmi_ports": 4,
            "refresh_rate": 120,
            "panel_type": "QLED",
            "has_hdr": True,
            "year": 2023
        },
        "price": 24999.99,
        "rating": 4.7,
        "description": "Премиум телевизор Samsung с технологией Quantum Dot для ярких цветов",
        "months_warranty": 24,
        "country_origin": "Южная Корея",
        "sale_percent": 10,
        "views": 1523
    },
    {
        "product_id": 2,
        "title": "LG OLED 65\" 4K Ultra HD",
        "category_id": 1,
        "specification": {
            "screen_size": 65,
            "resolution": "4K",
            "smart_tv": True,
            "hdmi_ports": 4,
            "refresh_rate": 120,
            "panel_type": "OLED",
            "has_hdr": True,
            "year": 2023
        },
        "price": 49999.00,
        "rating": 4.9,
        "description": "OLED телевизор с идеальным черным цветом и бесконечным контрастом",
        "months_warranty": 36,
        "country_origin": "Южная Корея",
        "sale_percent": 0,
        "views": 2341
    },
    {
        "product_id": 3,
        "title": "Sony Bravia 50\" Full HD LED",
        "category_id": 1,
        "specification": {
            "screen_size": 50,
            "resolution": "Full HD",
            "smart_tv": True,
            "hdmi_ports": 3,
            "refresh_rate": 60,
            "panel_type": "IPS",
            "has_hdr": False,
            "year": 2022
        },
        "price": 15999.50,
        "rating": 4.3,
        "description": "Качественный телевизор Sony с широкими углами обзора",
        "months_warranty": 24,
        "country_origin": "Япония",
        "sale_percent": 15,
        "views": 892
    },
    {
        "product_id": 4,
        "title": "Xiaomi Mi TV 43\" Full HD",
        "category_id": 1,
        "specification": {
            "screen_size": 43,
            "resolution": "Full HD",
            "smart_tv": True,
            "hdmi_ports": 3,
            "refresh_rate": 60,
            "panel_type": "VA",
            "has_hdr": True,
            "year": 2023
        },
        "price": 8999.00,
        "rating": 4.1,
        "description": "Бюджетный Smart TV с Android TV и Chromecast",
        "months_warranty": 12,
        "country_origin": "Китай",
        "sale_percent": 5,
        "views": 3421
    },
    {
        "product_id": 5,
        "title": "Philips 32\" HD Ready",
        "category_id": 1,
        "specification": {
            "screen_size": 32,
            "resolution": "HD",
            "smart_tv": False,
            "hdmi_ports": 2,
            "refresh_rate": 50,
            "panel_type": "VA",
            "has_hdr": False,
            "year": 2021
        },
        "price": 5499.99,
        "rating": 3.8,
        "description": "Компактный телевизор для кухни или спальни",
        "months_warranty": 12,
        "country_origin": "Польша",
        "sale_percent": 20,
        "views": 456
    },
    {
        "product_id": 6,
        "title": "TCL 75\" 4K UHD Android TV",
        "category_id": 1,
        "specification": {
            "screen_size": 75,
            "resolution": "4K",
            "smart_tv": True,
            "hdmi_ports": 4,
            "refresh_rate": 60,
            "panel_type": "VA",
            "has_hdr": True,
            "year": 2023
        },
        "price": 32999.00,
        "rating": 4.5,
        "description": "Большой телевизор с поддержкой Dolby Vision и Dolby Atmos",
        "months_warranty": 24,
        "country_origin": "Китай",
        "sale_percent": 0,
        "views": 721
    }
]

# ============================================
# 5. REVIEWS (зависит от products и users)
# ============================================
REVIEWS = [
    {
        "review_id": 1,
        "product_id": 1,
        "user_id": 3,
        "months_used": 6,
        "positive": "Отличное качество изображения, быстрый Smart TV",
        "negative": "Немного сложное меню настроек",
        "comment": "Очень доволен покупкой. Картинка впечатляет, особенно в темноте.",
        "date_posted": datetime(2024, 1, 15, 10, 30),
        "date_updated": datetime(2024, 1, 15, 10, 30),
        "is_edited": False,
        "rating": 5
    },
    {
        "review_id": 2,
        "product_id": 2,
        "user_id": 4,
        "months_used": 3,
        "positive": "Идеальный черный цвет, тонкий дизайн",
        "negative": "Высокая цена",
        "comment": "OLED панель — это нечто невероятное. Но цена кусается.",
        "date_posted": datetime(2024, 2, 20, 14, 15),
        "date_updated": datetime(2024, 2, 20, 14, 15),
        "is_edited": False,
        "rating": 5
    },
    {
        "review_id": 3,
        "product_id": 3,
        "user_id": 5,
        "months_used": 12,
        "positive": "Надежный, хорошие углы обзора",
        "negative": "Нет HDR",
        "comment": "Работает уже год без проблем. Отличный выбор за свою цену.",
        "date_posted": datetime(2024, 3, 10, 9, 45),
        "date_updated": datetime(2024, 3, 12, 11, 20),
        "is_edited": True,
        "rating": 4
    },
    {
        "review_id": 4,
        "product_id": 4,
        "user_id": 3,
        "months_used": 2,
        "positive": "Дешевый, быстрый Smart TV",
        "negative": "Не очень яркий экран",
        "comment": "За такую цену — отличный вариант. Android TV работает плавно.",
        "date_posted": datetime(2024, 4, 5, 16, 0),
        "date_updated": datetime(2024, 4, 5, 16, 0),
        "is_edited": False,
        "rating": 4
    },
    {
        "review_id": 5,
        "product_id": 1,
        "user_id": 5,
        "months_used": 8,
        "positive": "Отличный HDR, много функций",
        "negative": "Большой пульт",
        "comment": "Второй Samsung в доме. Качество традиционно на высоте.",
        "date_posted": datetime(2024, 5, 1, 12, 30),
        "date_updated": datetime(2024, 5, 1, 12, 30),
        "is_edited": False,
        "rating": 5
    }
]

# ============================================
# 6. FAVORITE_PRODUCTS (зависит от products и users)
# ============================================
FAVORITE_PRODUCTS = [
    {"favorite_product_id": 1, "user_id": 3, "product_id": 1},
    {"favorite_product_id": 2, "user_id": 3, "product_id": 2},
    {"favorite_product_id": 3, "user_id": 4, "product_id": 2},
    {"favorite_product_id": 4, "user_id": 4, "product_id": 6},
    {"favorite_product_id": 5, "user_id": 5, "product_id": 3},
    {"favorite_product_id": 6, "user_id": 5, "product_id": 4},
]

# ============================================
# 7. HISTORY_QUERY_USER (зависит от users)
# ============================================
HISTORY_QUERY_USER = [
    {"history_text_user_id": 1, "user_id": 3, "query_text": "samsung tv"},
    {"history_text_user_id": 2, "user_id": 3, "query_text": "4k телевизор"},
    {"history_text_user_id": 3, "user_id": 4, "query_text": "oled"},
    {"history_text_user_id": 4, "user_id": 4, "query_text": "sony"},
    {"history_text_user_id": 5, "user_id": 5, "query_text": "дешёвый тв"},
    {"history_text_user_id": 6, "user_id": 5, "query_text": "xiaomi"},
]

# ============================================
# 8. STORES_QUANTITY_INFO (зависит от stores и products)
# ============================================
STORES_QUANTITY_INFO = [
    # Магазин 1
    {"stores_quantity_info_id": 1, "store_id": 1, "product_id": 1, "quantity": 5},
    {"stores_quantity_info_id": 2, "store_id": 1, "product_id": 2, "quantity": 2},
    {"stores_quantity_info_id": 3, "store_id": 1, "product_id": 3, "quantity": 8},
    {"stores_quantity_info_id": 4, "store_id": 1, "product_id": 4, "quantity": 15},
    
    # Магазин 2
    {"stores_quantity_info_id": 5, "store_id": 2, "product_id": 1, "quantity": 3},
    {"stores_quantity_info_id": 6, "store_id": 2, "product_id": 3, "quantity": 6},
    {"stores_quantity_info_id": 7, "store_id": 2, "product_id": 5, "quantity": 12},
    {"stores_quantity_info_id": 8, "store_id": 2, "product_id": 6, "quantity": 4},
    
    # Магазин 3
    {"stores_quantity_info_id": 9, "store_id": 3, "product_id": 2, "quantity": 1},
    {"stores_quantity_info_id": 10, "store_id": 3, "product_id": 4, "quantity": 10},
    {"stores_quantity_info_id": 11, "store_id": 3, "product_id": 5, "quantity": 7},
]

# ============================================
# 9. ORDER_TYPES (независимая таблица)
# ============================================
ORDER_TYPES = [
    {"order_type_id": 1, "title": "Самовывоз"},
    {"order_type_id": 2, "title": "Доставка курьером"},
]

# ============================================
# 10. ORDER_PICKUP_DETAILS (зависит от stores и users)
# ============================================
ORDER_PICKUP_DETAILS = [
    {"order_pickup_detail_id": 1, "store_id": 1, "user_id": 3},
    {"order_pickup_detail_id": 2, "store_id": 2, "user_id": 4},
]

# ============================================
# 11. ORDER_DELIVERY_DETAILS (зависит от users)
# ============================================
ORDER_DELIVERY_DETAILS = [
    {
        "order_delivery_detail_id": 1,
        "address": "ул. Невский проспект, 10, Санкт-Петербург",
        "user_id": 4
    },
    {
        "order_delivery_detail_id": 2,
        "address": "ул. Баумана, 15, Казань",
        "user_id": 5
    },
]

# ============================================
# 12. ORDERS (зависит от order_types, users, order details)
# ============================================
ORDERS = [
    {
        "order_id": 1,
        "status": "finished",
        "order_type_id": 1,  # Самовивіз
        "order_detail_id": 1,  # order_pickup_detail_id
        "user_id": 3,
        "date": datetime(2024, 1, 10, 14, 30),
        "price": 24999.99,
        "created_at": datetime(2024, 1, 10, 14, 30),
        "updated_at": datetime(2024, 1, 15, 10, 0)
    },
    {
        "order_id": 2,
        "status": "delivered",
        "order_type_id": 2,  # Доставка
        "order_detail_id": 1,  # order_delivery_detail_id
        "user_id": 4,
        "date": datetime(2024, 2, 15, 11, 0),
        "price": 49999.00,
        "created_at": datetime(2024, 2, 15, 11, 0),
        "updated_at": datetime(2024, 2, 20, 16, 30)
    },
    {
        "order_id": 3,
        "status": "new",
        "order_type_id": 1,  # Самовивіз
        "order_detail_id": 2,  # order_pickup_detail_id
        "user_id": 4,
        "date": datetime(2024, 6, 1, 10, 0),
        "price": 8999.00,
        "created_at": datetime(2024, 6, 1, 10, 0),
        "updated_at": datetime(2024, 6, 1, 10, 0)
    },
]

# ============================================
# 13. PURCHASES (зависит от orders и products)
# ============================================
PURCHASES = [
    {"purchase_id": 1, "order_id": 1, "product_id": 1},
    {"purchase_id": 2, "order_id": 2, "product_id": 2},
    {"purchase_id": 3, "order_id": 3, "product_id": 4},
]

# ============================================
# 14. BASKETS (зависит от users и products)
# ============================================
BASKETS = [
    {"basket_id": 1, "user_id": 3, "product_id": 6},
    {"basket_id": 2, "user_id": 4, "product_id": 3},
    {"basket_id": 3, "user_id": 5, "product_id": 1},
    {"basket_id": 4, "user_id": 5, "product_id": 4},
]

# ============================================
# 15. REFRESH_TOKEN_BL (независимая таблица)
# ============================================
REFRESH_TOKEN_BL = [
    {"refresh_token_bl_id": 1, "jti": "abc123-def456-ghi789"},
    {"refresh_token_bl_id": 2, "jti": "xyz987-uvw654-rst321"},
]


# ============================================
# ПОРЯДОК ВСТАВКИ (важно!)
# ============================================
INSERT_TABLES = [
    ("stores", STORES),
    ("users", USERS),
    ("categories", CATEGORIES),
    ("products", PRODUCTS),
    ("reviews", REVIEWS),
    ("favorite_products", FAVORITE_PRODUCTS),
    ("history_text_user", HISTORY_QUERY_USER),
    ("stores_quantity_info", STORES_QUANTITY_INFO),
    ("order_types", ORDER_TYPES),
    ("order_pickup_details", ORDER_PICKUP_DETAILS),
    ("order_delivery_details", ORDER_DELIVERY_DETAILS),
    ("orders", ORDERS),
    ("purchases", PURCHASES),
    ("baskets", BASKETS),
    ("refresh_token_bl", REFRESH_TOKEN_BL),
]