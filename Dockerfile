# Use official Python slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        gcc \
        g++ \
        libopenblas-dev \
        liblapack-dev \
        libjpeg-dev \
        libgl1 \
        git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port for Cloud Run
ENV PORT 8080

# Run Flask app
CMD ["python", "app.py"]
