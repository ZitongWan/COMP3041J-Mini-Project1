# Campus Buzz - Presentation Service Dockerfile
# 展示服务：Flask + 静态文件
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY static/ static/

EXPOSE 5000

ENV FLASK_ENV=production

CMD ["python", "app.py"]
