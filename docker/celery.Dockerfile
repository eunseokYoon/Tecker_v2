# --- build stage ---
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install uv setuptools && \
    uv pip install --prefix=/install --no-build-isolation \
    django djangorestframework djangorestframework-simplejwt \
    "dj-rest-auth[with_social]" django-allauth django-cors-headers \
    django-prometheus django-redis "celery[redis]" gunicorn mysqlclient \
    boto3 Pillow qrcode tenacity python-dotenv drf-spectacular

# --- runtime stage ---
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 && rm -rf /var/lib/apt/lists/* && \
    useradd -m app
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=app:app . .
USER app
CMD ["celery", "-A", "config", "worker", "--loglevel=info"]
