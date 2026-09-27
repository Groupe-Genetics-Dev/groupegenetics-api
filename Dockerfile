# ---------- Étape 1 : compilation des dépendances ----------
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1

# psycopg2 (non-binaire) doit être compilé : il faut gcc + headers libpq
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# ---------- Étape 2 : image d'exécution ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

WORKDIR /app

# Seule la librairie cliente PostgreSQL est nécessaire à l'exécution
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

COPY . .
RUN chmod +x docker-entrypoint.sh && mkdir -p reports

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
