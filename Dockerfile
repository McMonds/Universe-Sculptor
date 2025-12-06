FROM python:3.13-slim

# Install build tools for REBOUND and spiceypy
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY QUICKSTART.md .
COPY README.md .

# Create directories
RUN mkdir -p data/cache logs

# Expose ports for Flask (Web Viz) and Dashboard
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command: Run the optimizer
CMD ["python", "src/optimizer.py"]
