# Campus Buzz - Data Service Dockerfile
# 数据服务：Flask + SQLite
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# 创建数据持久化目录
RUN mkdir -p /data

# 暴露端口
EXPOSE 5002

# 设置环境变量
ENV DATABASE_PATH=/data/campus_buzz.db
ENV FLASK_ENV=production

# 启动应用
CMD ["python", "app.py"]
