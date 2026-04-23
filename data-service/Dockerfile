# Campus Buzz - Data Service Dockerfile
# Flask + SQLite backend service

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create persistent data directory for SQLite
RUN mkdir -p /data

# Expose the service port
EXPOSE 5002

# Environment variables
ENV DATABASE_PATH=/data/campus_buzz.db
ENV FLASK_ENV=production

# Start the Flask application
CMD ["python", "app.py"]
