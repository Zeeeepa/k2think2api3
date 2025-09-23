FROM python:3.12-slim

# 安装curl用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 设置环境变量 - 强化编码支持
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV PYTHONLEGACYWINDOWSSTDIO=0
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY k2think_proxy.py .
COPY get_tokens.py .
COPY src/ ./src/

# 创建非root用户运行应用 (使用标准UID 1000)
RUN useradd -r -s /bin/false -u 1000 appuser

# 创建数据目录和默认文件
RUN mkdir -p /app/data && \
    touch /app/data/tokens.txt && \
    echo "# Token文件将由自动更新服务生成" > /app/data/tokens.txt && \
    touch /app/data/accounts.txt && \
    echo "# 请通过volume挂载实际的accounts.txt文件" > /app/data/accounts.txt

# 创建简单的启动脚本来处理权限
RUN echo '#!/bin/bash\n\
# 确保数据目录存在\n\
mkdir -p /app/data\n\
# 修复数据目录权限\n\
chown -R 1000:1000 /app/data 2>/dev/null || true\n\
# 切换到应用用户运行\n\
exec su-exec appuser "$@"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# 安装su-exec（轻量级的用户切换工具）
RUN apt-get update && apt-get install -y su-exec && rm -rf /var/lib/apt/lists/*

# 设置正确的所有权
RUN chown -R appuser:appuser /app

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# 设置entrypoint和默认命令
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "k2think_proxy.py"]