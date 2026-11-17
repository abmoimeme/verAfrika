# VeraAfrika API + pilot UI (staging). One process serves both.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VERAFRIKA_ENV=staging \
    VERAFRIKA_AUTO_MIGRATE=1 \
    VERAFRIKA_TRUST_PROXY=1 \
    PORT=8000

WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY web ./web
COPY connectors ./connectors
COPY reference ./reference

RUN useradd --system --uid 10001 verafrika && chown -R verafrika /srv
USER verafrika

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
