FROM python:3.11-slim

# Install system dependencies 
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    libnl-3-dev \
    libnl-route-3-dev \
    libprotobuf-dev \
    protobuf-compiler \
    bison \
    flex \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone and build 
WORKDIR /tmp
RUN git clone https://github.com/google/nsjail.git \
    && cd nsjail \
    && make \
    && cp nsjail /usr/local/bin/ \
    && cd .. \
    && rm -rf nsjail

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/app.py .

# Create a non-root user for running the app 
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "app.py"] 