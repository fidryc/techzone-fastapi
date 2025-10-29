from app.config import settings

if settings.MODE == 'DEV':
    ELASTICSEARCH_URL = f"http://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}"
elif settings.MODE == 'PROD':
    ELASTICSEARCH_URL = f"http://{settings.ELASTIC_HOST_PROD}:{settings.ELASTIC_PORT}"
elif settings.MODE == 'TEST':
    ELASTICSEARCH_URL = f"http://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}"