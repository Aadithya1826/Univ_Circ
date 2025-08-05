# Use slim Python base
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    gcc \
    g++ \
    libopenblas-dev \
    liblapack-dev \
    libjpeg-dev \
    libgl1 \
    git \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Environment
ENV PORT=8080

# Expose Flask port
EXPOSE 8080

# Run the app
CMD ["python", "app.py"]
