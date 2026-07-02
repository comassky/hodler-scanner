# ── Stage 1: build the Vue frontend ─────────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python API + static frontend ───────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend sources (api.py, script.py, db.py, i18n.py, locales/)
COPY backend/ .

# Copy the Vue build into /app/static
COPY --from=frontend-builder /app/dist ./static

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
