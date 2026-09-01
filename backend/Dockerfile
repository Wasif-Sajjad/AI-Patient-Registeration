FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by asyncpg and psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Convert start.sh to Unix line endings and make it executable
RUN dos2unix start.sh && chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]
