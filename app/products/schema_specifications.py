"""
Файл с моделями pydantic, валидация которых используется при добавлении товара.
через specification_schemas_dict возвращается нужная схема, по которой проходит валидация
поля specification продукта
"""

from typing import Literal
from pydantic import BaseModel, Field

from app.products.models import Product


class TvSchema(BaseModel):
    screen_size: int = Field(ge=10, le=100)
    resolution: Literal['4K', 'Full HD', '8К', 'HD']
    smart_tv: bool
    hdmi_ports: int = Field(ge=0)
    refresh_rate: int = Field(ge=0)
    panel_type: Literal['IPS', 'VA', 'OLED', 'QLED']
    has_hdr: bool
    year: int = Field(ge=1950)
    
    class Settings:
        example = { 
            'screen_size': 'int >=10 and <= 100',
            'resolution': 'string[4K, Full HD, 8К, HD ]',
            'smart_tv':  '0 or 1',
            'hdmi_ports': 'int >= 0',
            'refresh_rate': 'int >= 0',
            'panel_type': 'IPS, VA, OLED, QLED',
            'has_hdr': '0 or 1',
            'year': 'int >= 1950',
        }
      
specification_schemas_dict = {
    TvSchema.__name__: TvSchema,
}
