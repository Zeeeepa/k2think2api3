# Docker 部署指南

## 问题分析

### 原配置存在的问题

1. **文件挂载导致的锁定问题**
   ```yaml
   - ./tokens.txt:/app/tokens.txt  # ❌ 直接文件挂载可能导致锁定
   ```
   - 当token自动更新服务尝试删除/重命名`tokens.txt`时会失败
   - Windows系统下文件挂载容易出现权限问题

2. **accounts.txt权限问题**
   ```yaml
   - ./accounts.txt:/app/accounts.txt:ro  # ❌ 只读挂载
   ```

3. **缺少编码环境变量**
   - 容器内可能出现中文编码问题

## 解决方案

### 方案1：目录挂载（推荐用于开发环境）

```yaml
volumes:
  - ./data:/app/data  # ✅ 挂载整个目录，避免文件锁定
```

**优点：**
- 避免单文件挂载的锁定问题
- 容器内可以自由创建、删除、重命名文件
- 便于开发和调试

**使用方法：**
```bash
# 1. 创建data目录
mkdir data

# 2. 复制配置文件到data目录
cp tokens.txt data/
cp accounts.txt data/

# 3. 使用新的docker-compose配置
docker-compose -f docker-compose.new.yml up -d
```

### 方案2：命名卷（推荐用于生产环境）

```yaml
volumes:
  - k2think_data:/app/data  # ✅ 使用Docker管理的命名卷
```

**优点：**
- Docker完全管理存储
- 更好的性能和可靠性
- 支持备份和迁移

**使用方法：**
```bash
# 使用生产环境配置
docker-compose -f docker-compose.production.yml up -d

# 初始化数据（首次部署）
docker-compose -f docker-compose.production.yml exec k2think-api bash
# 在容器内编辑 /app/data/accounts.txt
```

## 配置文件更新

### 环境变量配置 (.env)

```bash
# 基本配置
VALID_API_KEY=sk-k2think
HOST=0.0.0.0
PORT=8001

# Token自动更新配置
ENABLE_TOKEN_AUTO_UPDATE=true
TOKEN_UPDATE_INTERVAL=129600
TOKENS_FILE=/app/data/tokens.txt
ACCOUNTS_FILE=/app/data/accounts.txt
GET_TOKENS_SCRIPT=get_tokens.py

# 编码配置（容器内自动设置）
PYTHONIOENCODING=utf-8
PYTHONLEGACYWINDOWSSTDIO=0
```

### Dockerfile改进

```dockerfile
# 添加编码环境变量
ENV PYTHONIOENCODING=utf-8
ENV PYTHONLEGACYWINDOWSSTDIO=0
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# 创建专用数据目录
RUN mkdir -p /app/data
```

## 部署步骤

### 开发环境部署

```bash
# 1. 创建数据目录
mkdir -p data

# 2. 准备配置文件
cp tokens.txt data/ 2>/dev/null || echo "# Token文件将由自动更新服务生成" > data/tokens.txt
cp accounts.txt data/ 2>/dev/null || echo "# 请添加账户信息" > data/accounts.txt

# 3. 更新环境变量
cat >> .env << EOF
TOKENS_FILE=/app/data/tokens.txt
ACCOUNTS_FILE=/app/data/accounts.txt
EOF

# 4. 启动服务
docker-compose -f docker-compose.new.yml up -d

# 5. 查看日志
docker-compose -f docker-compose.new.yml logs -f
```

### 生产环境部署

```bash
# 1. 使用生产配置启动
docker-compose -f docker-compose.production.yml up -d

# 2. 初始化accounts.txt（如果启用自动更新）
docker-compose -f docker-compose.production.yml exec k2think-api bash -c "
cat > /app/data/accounts.txt << 'EOF'
{\"username\": \"your_username\", \"email\": \"your_email@example.com\", \"k2_password\": \"your_password\"}
EOF
"

# 3. 触发首次token更新（如果启用自动更新）
docker-compose -f docker-compose.production.yml exec k2think-api python get_tokens.py /app/data/accounts.txt /app/data/tokens.txt

# 4. 验证服务状态
curl http://localhost:8001/health
```

## 故障排除

### 1. 文件权限问题
```bash
# 检查文件权限
docker-compose exec k2think-api ls -la /app/data/

# 修复权限
docker-compose exec k2think-api chown -R appuser:appuser /app/data/
```

### 2. Token更新失败
```bash
# 查看更新器状态
curl http://localhost:8001/admin/tokens/updater/status

# 手动触发更新
curl -X POST http://localhost:8001/admin/tokens/updater/force-update

# 查看日志
docker-compose logs k2think-api | grep -i token
```

### 3. 编码问题
```bash
# 检查容器内编码设置
docker-compose exec k2think-api env | grep -E "(LANG|LC_|PYTHON)"

# 验证中文处理
docker-compose exec k2think-api python -c "print('中文测试')"
```

## 迁移指南

### 从文件挂载迁移到目录挂载

```bash
# 1. 停止现有服务
docker-compose down

# 2. 创建数据目录并迁移文件
mkdir -p data
cp tokens.txt data/ 2>/dev/null || true
cp accounts.txt data/ 2>/dev/null || true

# 3. 更新配置
cp docker-compose.yml docker-compose.yml.backup
cp docker-compose.new.yml docker-compose.yml

# 4. 更新环境变量
echo "TOKENS_FILE=/app/data/tokens.txt" >> .env
echo "ACCOUNTS_FILE=/app/data/accounts.txt" >> .env

# 5. 重新启动
docker-compose up -d
```

## 监控和维护

### 健康检查
```bash
# 检查服务健康状态
docker-compose ps

# 详细健康检查
curl http://localhost:8001/health | jq
```

### 备份数据
```bash
# 备份命名卷数据
docker run --rm -v k2think_data:/data -v $(pwd):/backup alpine tar czf /backup/k2think_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# 恢复数据
docker run --rm -v k2think_data:/data -v $(pwd):/backup alpine tar xzf /backup/k2think_backup_YYYYMMDD_HHMMSS.tar.gz -C /data
```