# === Dockerfile ===
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
        tesseract-ocr \
        poppler-utils \
        gsutil \
        curl \
        gnupg \
        && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK for gsutil
RUN curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    echo "deb https://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && apt-get install -y google-cloud-sdk

# Set working directory
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all application files
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY uploads/ ./uploads/
COPY . .

# Set env port
ENV PORT 8080

# Run the application
CMD ["python", "app.py"]


