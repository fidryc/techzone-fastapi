from fastapi import HTTPException
import pytest
from app.stores.dao import StoreDao

@pytest.fixture(scope='function')
def store_dao(session):
    return StoreDao(session)


@pytest.mark.dao
@pytest.mark.parametrize(
    'store_id, title',
    [
        (1, 'Магазин на Арбате'),
        (2, 'Магазин в ТРЦ МегаМолл')
    ]
)
async def test_dao_find(store_dao: StoreDao, store_id, title):
    assert ((await store_dao.find_by_filter_one(store_id=store_id)).title) == title
    
@pytest.mark.dao
@pytest.mark.parametrize(
    'title, opening_hours',
    [
        ('sda', 'Магазин на Арбате'),
        ('shop_test', 'Магазин в ТРЦ МегаМолл')
    ]
)
async def test_dao_add(store_dao: StoreDao, title, opening_hours):
    await store_dao.add(title=title, opening_hours=opening_hours)
    stores = await store_dao.find_by_filter(title=title, opening_hours=opening_hours)
    assert len(stores) == 1
    assert stores[0].title == title and stores[0].opening_hours == opening_hours


@pytest.mark.dao
@pytest.mark.parametrize(
    'title, opening_hours',
    [
        (1, 'Магазин на Арбате'),
        ('shop_test', 2),
        (2, 3),
    ]
)
async def test_dao_add_exc(store_dao: StoreDao, title, opening_hours):
    with pytest.raises(HTTPException):
        await store_dao.add(title=title, opening_hours=opening_hours)
        