FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY tools.py .
COPY agent.py .
COPY main.py .

# Set environment variables (these should be overridden at runtime)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port (if you add a web interface later)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30m --timeout=10s --start-period=1m \
  CMD python -c "import logging; logging.info('Health check')" || exit 1

# Run the application
CMD ["python", "main.py"]