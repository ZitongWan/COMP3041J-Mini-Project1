# Campus Buzz - Presentation Service Dockerfile
# Flask service for rendering UI and serving static assets

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and static files
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Expose service port
EXPOSE 5000

# Environment configuration
ENV FLASK_ENV=production

# Start the service
CMD ["python", "app.py"]
