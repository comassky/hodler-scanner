# ── Stage 1: build the Vue frontend ─────────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python API + static frontend ───────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && find /usr/local/lib/python3.13/site-packages -type d -name tests -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.13/site-packages -type d -name '__pycache__' -prune -exec rm -rf {} + \
 && rm -rf /usr/local/lib/python3.13/site-packages/pip \
          /usr/local/lib/python3.13/site-packages/pip-*.dist-info \
          /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13

# Backend sources (api.py, script.py, db.py, i18n.py, locales/)
COPY backend/ .

# Copy the Vue build into /app/static
COPY --from=frontend-builder /app/dist ./static

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
