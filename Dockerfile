FROM python:3.13-slim
WORKDIR /shop_project
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD sh -c "alembic revision --autogenerate -m 'initial' && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
