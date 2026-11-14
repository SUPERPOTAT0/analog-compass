# Analog Compass API — portable container (deployable on Vercel containers or any OCI host).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY api/ ./api/
COPY asgi.py ./

ENV DATA_MODE=synthetic DATA_BUNDLE_URI=data/synthetic DATA_VERSION=synthetic-0.1.0
EXPOSE 8000
CMD ["uvicorn", "asgi:app", "--host", "0.0.0.0", "--port", "8000"]
