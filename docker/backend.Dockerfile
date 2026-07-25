FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for RDKit
RUN apt-get update && apt-get install -y \
    libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Try to install RDKit (may fail on some platforms — app degrades gracefully)
RUN pip install rdkit 2>/dev/null || echo "RDKit install skipped - app will use fallback validation"

COPY backend/ ./backend/
COPY backend/.env .env

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
