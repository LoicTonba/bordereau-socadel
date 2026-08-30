# API FastAPI du bordereau SOCADEL.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Les dépendances sont copiées seules d'abord : le cache de couche survit à
# chaque modification du code applicatif.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts ./scripts
COPY alembic.ini ./

ENV PYTHONPATH=/app/src

# L'application ne tourne pas en root.
RUN useradd --create-home --uid 1001 socadel && chown -R socadel:socadel /app
USER socadel

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/sante')"

CMD ["uvicorn", "bordereau.main:app", "--host", "0.0.0.0", "--port", "8000"]
