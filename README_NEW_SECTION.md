## 快速开始 (Quick Start)

### 🚀 一键部署 (推荐)

最简单的方式！使用 `csds.sh` 脚本自动完成克隆、设置、部署和测试：

```bash
# 下载脚本
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh -o csds.sh

# 运行（默认使用 main 分支）
bash csds.sh

# 或指定特定分支
bash csds.sh your-branch-name
```

**✨ 特性：**
- ✅ 自动创建 Python 虚拟环境（解决系统管理的 Python 环境问题）
- ✅ 自动安装所有依赖
- ✅ 自动配置服务器
- ✅ 自动启动并测试 API
- ✅ 支持指定分支部署

**使用方式：**
- `bash csds.sh` - 使用 main 分支部署
- `bash csds.sh <branch-name>` - 使用指定分支部署

**💡 注意事项：**
- 脚本会自动处理 `externally-managed-environment` 错误
- 所有依赖都安装在独立的虚拟环境中 (venv/)
- 不需要 root 权限或 `--break-system-packages`
