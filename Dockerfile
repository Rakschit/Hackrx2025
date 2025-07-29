FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install CPU-only torch explicitly
RUN pip install --no-cache-dir torch==2.2.2+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install other requirements except sentence-transformers
RUN grep -v "sentence-transformers" requirements.txt > requirements_no_st.txt \
    && pip install --no-cache-dir -r requirements_no_st.txt

# Install sentence-transformers WITHOUT upgrading torch
RUN pip install --no-cache-dir --no-deps sentence-transformers==2.7.0

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
