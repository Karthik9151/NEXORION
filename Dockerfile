# syntax=docker/dockerfile:1
# Build the Vite frontend, then serve its static output through the FastAPI app.
FROM node:20-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json ./package.json
# npm install is used until a verified npm lockfile is generated and committed.
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=10000
WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY backend/ ./backend/
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt
COPY --from=frontend-build /build/frontend/dist ./frontend/dist
WORKDIR /app/backend
EXPOSE 10000
CMD ["sh", "-c", "alembic upgrade head && python -m app.bootstrap_owner && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
