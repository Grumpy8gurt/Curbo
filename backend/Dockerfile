FROM python:3.13.7-slim-bookworm@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY backend/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r ./requirements.lock

RUN groupadd --gid 10001 curbo \
    && useradd --uid 10001 --gid curbo --no-create-home --shell /usr/sbin/nologin curbo \
    && mkdir -p /app/data/runtime /app/generated_reports \
    && chown -R curbo:curbo /app

COPY --chown=curbo:curbo backend/app ./app
COPY --chown=curbo:curbo backend/alembic.ini ./alembic.ini
COPY --chown=curbo:curbo backend/migrations ./migrations
COPY --chown=curbo:curbo backend/README.md ./README.md
COPY --chown=curbo:curbo data ./data

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/ready', timeout=3)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
