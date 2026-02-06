FROM public.ecr.aws/docker/library/python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y \
    build-essential \
    libhdf5-dev \
    ca-certificates \
    curl \
    git \
    gzip \
    pkg-config \
    procps \
    tar \
    unzip \
    wget \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/task

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN pip install awslambdaric

# Copy application code and lambda handler.
COPY app/ ./app/
COPY lambda_handler.py .

# Use Magnum
CMD ["python", "-m", "awslambdaric", "lambda_handler.handler"]