FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port
EXPOSE 9000

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "2", "--timeout", "30", "app:app"]