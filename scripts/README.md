# Python 脚本说明

本目录包含跨平台的 Python 部署脚本，支持 Windows、macOS 和 Linux。

## 📁 脚本列表

| 脚本文件 | 功能 | 说明 |
|---------|------|------|
| `deploy.py` | 部署 Gophish | 创建云服务器并自动部署 |
| `destroy.py` | 销毁资源 | 备份数据库并销毁云资源 |
| `check-resources.py` | 查看资源 | 列出所有已部署的实例 |
| `deploy.sh` | 部署(Bash) | Bash 版本的部署脚本 |
| `destroy.sh` | 销毁(Bash) | Bash 版本的销毁脚本 |
| `setup-server.sh` | 服务器初始化 | 自动在服务器上安装 Docker |

## 🚀 快速使用

### 部署

```bash
# Windows / macOS / Linux
python scripts/deploy.py -p alibaba -r cn-shanghai
```

### 销毁

```bash
# Windows / macOS / Linux
python scripts/destroy.py -p alibaba
```

### 查看资源

```bash
# Windows / macOS / Linux  
python scripts/check-resources.py
```

## 🔧 命令行参数

### deploy.py

```bash
python scripts/deploy.py [选项]

必需参数:
  -p, --provider {alibaba,tencent,huawei}
                        云服务商
  -r, --region REGION   部署区域 (如: cn-shanghai)

可选参数:
  -t, --type TYPE       实例规格 (默认: 2核4G)
  -g, --git URL         Git 仓库地址
  -b, --branch BRANCH   Git 分支 (默认: main)

示例:
  python scripts/deploy.py -p alibaba -r cn-shanghai
  python scripts/deploy.py -p tencent -r ap-guangzhou -b dev
```

### destroy.py

```bash
python scripts/destroy.py [选项]

必需参数:
  -p, --provider {alibaba,tencent,huawei}
                        云服务商

可选参数:
  -r, --region         部署地域（未提供时尝试自动推断）
  --no-backup          跳过数据库备份
  --force              强制销毁（不提示确认）

示例:
  python scripts/destroy.py -p alibaba
  python scripts/destroy.py -p tencent -r ap-hongkong
  python scripts/destroy.py -p tencent --no-backup
  python scripts/destroy.py -p huawei --force
```

## 💡 为什么选择 Python 脚本？

### ✅ 优势

1. **跨平台兼容**
   - Windows 用户无需安装 Git Bash
   - 直接在 PowerShell、CMD 或终端中运行
   - 代码逻辑统一，维护更简单

2. **更好的错误处理**
   - Python 异常处理更完善
   - 提供详细的错误信息和堆栈跟踪
   - 更容易调试和排查问题

3. **功能更丰富**
   - 支持彩色输出（所有平台）
   - 参数解析更灵活 (使用 argparse)
   - JSON 处理更方便

4. **可扩展性强**
   - 易于添加新功能
   - 可以轻松集成第三方库
   - 支持面向对象编程

### 🔄 Bash vs Python

| 特性 | Bash 脚本 | Python 脚本 |
|------|----------|------------|
| Windows 支持 | 需要 Git Bash | ✅ 原生支持 |
| 错误处理 | 基础 | ✅ 完善 |
| 可读性 | 中等 | ✅ 优秀 |
| 可维护性 | 中等 | ✅ 优秀 |
| 依赖 | bash + ssh | ✅ Python 3 (通常预装) |

## 🔍 工作流程

### 部署流程 (deploy.py)

1. **环境检查** - 验证 Terraform、SSH、Git 等工具
2. **加载配置** - 读取 `configs/.env` 中的云凭证
3. **SSH 密钥检查** - 确认密钥存在且格式正确
4. **Terraform 初始化** - 初始化云服务商的 Terraform 配置
5. **创建基础设施** - 创建 VPC、安全组、ECS 实例
6. **等待 SSH 就绪** - 轮询检查服务器 SSH 端口
7. **初始化服务器** - 安装 Docker 和 Docker Compose
8. **部署 Gophish** - 拉取代码、构建镜像、启动容器
9. **获取管理密码** - 从容器日志中提取初始密码
10. **保存部署信息** - 记录到 `.deployment-*.json` 文件

### 销毁流程 (destroy.py)

1. **查找部署记录** - 读取最新的部署信息
2. **用户确认** - 提示确认销毁操作（可用 --force 跳过）
3. **备份数据库** - 从服务器下载 gophish.db（可用 --no-backup 跳过）
4. **Terraform 销毁** - 删除所有云资源
5. **清理记录** - 删除本地部署信息文件

## 🛠️ 开发和调试

### 启用详细日志

修改脚本中的日志级别：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 手动测试单个函数

```python
# 示例: 测试环境检查函数
from deploy import check_dependencies
check_dependencies()
```

### 添加新功能

所有核心函数都有明确的类型注解和文档字符串，方便扩展：

```python
def your_new_function(param: str) -> bool:
    """
    功能描述
    
    Args:
        param: 参数说明
    
    Returns:
        返回值说明
    """
    # 实现代码
    pass
```

## 📦 依赖要求

Python 脚本只依赖 **Python 标准库**，无需安装额外包：

- `os` - 系统操作
- `sys` - 系统参数和函数
- `json` - JSON 处理
- `time` - 时间操作
- `argparse` - 命令行参数解析
- `subprocess` - 执行外部命令
- `pathlib` - 路径操作
- `datetime` - 日期时间处理
- `typing` - 类型注解

## 🐛 故障排查

### Python 命令不可用

**Windows:**
```powershell
# 检查 Python 是否安装
python --version

# 如果不可用，从 Microsoft Store 安装 Python 3
# 或访问 https://www.python.org/downloads/
```

**macOS:**
```bash
# macOS 预装 Python，但可能是 2.x 版本
python3 --version

# 使用 python3 替代 python
python3 scripts/deploy.py -p alibaba -r cn-shanghai
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install python3

# CentOS/RHEL
sudo yum install python3
```

### 权限错误

**Linux/macOS:**
```bash
# 给脚本添加执行权限
chmod +x scripts/*.py

# 直接用 python 执行（推荐）
python scripts/deploy.py
```

**Windows:**
```powershell
# Windows 通常不需要额外权限
# 如果遇到问题，以管理员身份运行 PowerShell
```

## 📚 相关文档

- [主部署文档](../README.md)
- [Windows 专用指南](../WINDOWS.md)
- [快速参考](../REFERENCE.md)
- [配置说明](../configs/README.md)

---

**提示:** Python 脚本完全兼容 Bash 脚本的功能，推荐优先使用 Python 版本！
