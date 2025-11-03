from sqlalchemy import text
from app.logger import logger


async def reset_sequences(conn):
    """
    Сбрасывает все PostgreSQL sequences после вставки данных с явными ID.
    Это гарантирует, что следующие INSERT без ID будут работать корректно.
    """
    # Список всех таблиц с автоинкрементными PK
    tables_with_sequences = [
        ('users', 'user_id'),
        ('products', 'product_id'),
        ('categories', 'category_id'),
        ('stores', 'store_id'),
        ('reviews', 'review_id'),
        ('orders', 'order_id'),
        ('order_types', 'order_type_id'),
        ('order_pickup_details', 'order_pickup_detail_id'),
        ('order_delivery_details', 'order_delivery_detail_id'),
        ('purchases', 'purchase_id'),
        ('baskets', 'basket_id'),
        ('favorite_products', 'favorite_product_id'),
        ('history_text_user', 'history_text_user_id'),
        ('stores_quantity_info', 'stores_quantity_info_id'),
        ('refresh_token_bl', 'refresh_token_bl_id'),
    ]
    
    for table_name, pk_column in tables_with_sequences:
        # setval устанавливает sequence на MAX(id) + 1
        await conn.execute(text(f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', '{pk_column}'),
                COALESCE((SELECT MAX({pk_column}) FROM {table_name}), 1),
                true
            )
        """))
    logger.debug(msg='sequence success reset')  