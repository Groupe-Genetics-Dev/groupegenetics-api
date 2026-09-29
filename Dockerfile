FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg

WORKDIR /app

# Aucun paquet système (apt-get) n'est nécessaire : psycopg2 est remplacé par
# psycopg2-binary (même module, libpq incluse), toutes les dépendances
# s'installent en wheels précompilées via HTTPS.
COPY requirements.txt .
RUN sed 's/^psycopg2==/psycopg2-binary==/' requirements.txt > /tmp/requirements.txt \
    && pip install --only-binary=:all: -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh && mkdir -p reports

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
