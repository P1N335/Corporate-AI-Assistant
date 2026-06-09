# Образ backend. Тот же образ используется и для worker'а — отличается только
# команда запуска (см. docker-compose: сервис worker переопределяет command).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Сначала зависимости — слой кешируется, пока requirements.txt не меняется.
COPY requirements.txt .

# Версия chromadb-клиента должна совпадать с тегом образа chroma-сервера.
# Передаётся из compose как build-arg → единый источник правды (CHROMA_VERSION).
ARG CHROMA_VERSION=0.5.23
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "chromadb==${CHROMA_VERSION}"

# Код приложения и worker'а
COPY app ./app
COPY workers ./workers

EXPOSE 8000

# По умолчанию — API. Worker переопределит команду в compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
