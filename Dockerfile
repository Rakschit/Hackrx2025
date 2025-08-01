FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run with uvicorn (production ready)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
