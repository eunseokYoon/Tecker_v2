# --- build stage ---
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
# 프로덕션 의존성만 /install 에 격리하여 설치 (dev 의존성 제외)
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
    libmariadb3 curl && rm -rf /var/lib/apt/lists/* && \
    useradd -m app
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=app:app . .
USER app
HEALTHCHECK --interval=15s --timeout=3s --start-period=15s \
  CMD curl -fsS http://localhost:8000/healthz || exit 1
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "5", "--threads", "4", "--worker-class", "gthread", \
     "--timeout", "60", "--max-requests", "1000", "--max-requests-jitter", "100", \
     "--access-logfile", "-", "--error-logfile", "-"]
