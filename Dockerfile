FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for compiling C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set default production environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV LOG_LEVEL=WARNING
ENV TOKENIZERS_PARALLELISM=false

EXPOSE 8000

CMD ["uvicorn", "backend.app.app:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
