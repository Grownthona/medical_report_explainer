FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Add app subdirectory to Python path so 'services' module is found
ENV PYTHONPATH=/app/app

# Expose backend port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
  CMD curl -f http://0.0.0.0:8000/ || exit 1