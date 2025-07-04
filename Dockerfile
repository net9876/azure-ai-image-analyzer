# Use Python 3.12.6 to match your local environment
FROM python:3.12.6-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CREDENTIAL_METHOD=keyvault
ENV KEY_VAULT_URL=""

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code and configuration
COPY azure_ai_image_analyzer.py .
COPY config.json .

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (if you add a web interface later)
EXPOSE 8000

# Set the default command to use the new generalized file
CMD ["python", "azure_ai_image_analyzer.py"]