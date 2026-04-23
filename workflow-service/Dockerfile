# Campus Buzz - Workflow Service Dockerfile
# Flask service responsible for coordinating the workflow

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose service port
EXPOSE 5001

# Environment configuration
ENV FLASK_ENV=production

# Start the service
CMD ["python", "app.py"]
