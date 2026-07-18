# ── Stage 1: build the Vue frontend ─────────────────────────────
FROM node:25-alpine AS frontend-builder
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
WORKDIR /app
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm run build

# ── Stage 2: Python API + static frontend ───────────────────────
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && find /usr/local/lib/python3.14/site-packages -type d -name tests -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.14/site-packages -type d -name '__pycache__' -prune -exec rm -rf {} + \
 && rm -rf /usr/local/lib/python3.14/site-packages/pip \
          /usr/local/lib/python3.14/site-packages/pip-*.dist-info \
          /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.14

# Backend sources (api.py + business-logic modules: analysis, charts,
# fundamentals, news, search, market_data, cache, serialization, script,
# db, i18n, locales/)
COPY backend/ .

# App version — single source of truth = frontend/package.json
COPY --from=frontend-builder /app/package.json /tmp/package.json
RUN python -c "import json; open('VERSION','w').write(json.load(open('/tmp/package.json'))['version'])" \
 && rm /tmp/package.json

# Copy the Vue build into /app/static
COPY --from=frontend-builder /app/dist ./static

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
