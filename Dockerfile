FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY k2think_proxy.py .
COPY src/ ./src/

# 暴露端口
EXPOSE 8001

# 启动应用
CMD ["python", "k2think_proxy.py"]