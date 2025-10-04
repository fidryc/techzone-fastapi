import functools
from fastapi import APIRouter, Depends, Query, Request, Response
from app.elasticsearch.depends import ElasticsearchServiceDep
from app.products.depends import ProductDaoDep, ProductServiceDep
from app.products.schema import ProductSchema

from app.database import SessionDep, get_session
from app.products.services import ProductService
from app.users.depends import CurrentUserDep
from app.users.services import UserService

from fastapi_cache.decorator import cache

router = APIRouter(
    prefix='/products',
    tags=['Работа с товарами']
)


@router.get('/search/{query_text}', summary='Поиск товаров')
@cache(expire=180)
async def get_products(query_text: str, el_service: ElasticsearchServiceDep):
    """
    Поиск товаров по текстовому запросу
    
    Осуществляет поиск товаров в системе по переданному текстовому запросу
    
    Args:
        query_text: текст для поиска товаров
    
    Returns:
        Список найденных товаров
    """
    return await el_service.search_products(query_text)


@router.get('/catalog/{category}/', summary='Получение товаров по категории с фильтрами')
@cache(expire=180)
async def get_products(
    request: Request,
    product_dao: ProductDaoDep,
    category: str,
    price: str = Query(None),
    rating: float = Query(None),
    months_warranty: int = Query(None),
    country_origin: str = Query(None),
    ):
    """
    Получение товаров по категории с применением фильтров
    
    Возвращает список товаров указанной категории с возможностью фильтрации
    по цене, рейтингу, гарантии, стране производства и дополнительным характеристикам
    
    Args:
        category: категория товаров
        price: фильтр по цене
        rating: фильтр по рейтингу
        months_warranty: фильтр по сроку гарантии
        country_origin: фильтр по стране производства
        **specification_filters: фильтр по характеристиками товара (могут быть любыми, не заданы жестко)
    
    Returns:
        Список товаров соответствующих фильтрам
    """
    def_par = {'category', 'price', 'rating', 'months_warranty', 'country_origin'}
    specification_filters = {k: el for k, el in request.query_params.items() if k not in def_par}
    return await product_dao.get_with_filters(category = category,
                                      price = price,
                                      rating = rating,
                                      months_warranty = months_warranty,
                                      country_origin = country_origin,
                                      specification_filters=specification_filters)
    
    
@router.post('/add_product', summary='Добавление нового товара')
async def add_product(product: ProductSchema, session: SessionDep, user: CurrentUserDep, product_service: ProductServiceDep):
    """
    Добавление нового товара в систему
    
    Позволяет добавить новый товар с отправкой уведомлений
    
    Args:
        product: данные товара для добавления
    
    Returns:
        200: Товар успешно добавлен
    """
    await product_service.add_product(product, user, flag_notification=True)
    await session.commit()
    
        
@router.get('/recomendation', summary='Получение рекомендаций', response_model=list[ProductSchema])
@cache(expire=30)
async def recomendation(user: CurrentUserDep, product_service: ProductServiceDep):
    """
    Получение персональных рекомендаций товаров
    
    Возвращает список товаров, рекомендованных для текущего пользователя
    на основе его предпочтений и истории просмотров
    
    Args:
        user: текущий пользователь
    
    Returns:
        Список рекомендованных товаров
    """
    return await product_service.recomendation(user.user_id)


@router.get('/all', summary='Получение всех товаров')
async def all(product_dao: ProductDaoDep):
    """
    Получение полного списка всех товаров
    
    Возвращает все товары, доступные в системе
    
    Returns:
        Список всех товаров
    """
    return await product_dao.all()

    
@router.post('/find_by_id', summary='Поиск товара по ID')
async def add_product(product_service: ProductServiceDep, product_id: int):
    """
    Поиск товара по идентификатору
    
    Находит и возвращает товар по указанному ID
    
    Args:
        product_id: идентификатор товара
    
    Returns:
        Данные найденного товара
    """
    return await product_service.get_product_by_id(product_id)