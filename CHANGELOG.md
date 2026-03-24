# 变更日志

本文档记录 `PhishOps` 的重要版本发布说明。

## v2026.03.24

发布日期：2026-03-24

### 亮点

- 新增 EwoMail 自动化能力，支持阿里云、腾讯云、华为云的云端部署模板。
- 新增 EwoMail 独立安装与销毁脚本，便于在已有服务器中复用邮件系统能力。
- 优化 SSH 密钥处理逻辑，支持自动检测常见私钥路径并复用部署记录中的密钥信息。
- 优化资源销毁流程，支持从部署记录、环境变量或 Terraform 状态中自动推断地域。
- 更新项目文档，补充 EwoMail 用法、销毁说明和最新项目结构。

### 新增内容

- 新增 [scripts/deploy_ewomail.py](scripts/deploy_ewomail.py)，用于一键创建云主机并部署 EwoMail。
- 新增 [scripts/destroy_ewomail.py](scripts/destroy_ewomail.py)，用于回收 EwoMail 专用云资源。
- 新增 [scripts/install_ewomail_only.py](scripts/install_ewomail_only.py) 和 [scripts/install_ewomail.sh](scripts/install_ewomail.sh)，支持在已有服务器中安装 EwoMail。
- 新增 [scripts/ssh_utils.py](scripts/ssh_utils.py)，统一处理 SSH 密钥定位与公钥读取。
- 新增 EwoMail Terraform 模块：
  - [terraform/ewomail_alibaba/main.tf](terraform/ewomail_alibaba/main.tf)
  - [terraform/ewomail_huawei/main.tf](terraform/ewomail_huawei/main.tf)
  - [terraform/ewomail_tencent/main.tf](terraform/ewomail_tencent/main.tf)

### 优化内容

- 更新 [scripts/deploy.py](scripts/deploy.py)，增强 SSH 密钥自动检测和部署记录保存。
- 更新 [scripts/destroy.py](scripts/destroy.py)，增强地域解析、备份密钥选择和多云销毁体验。
- 更新 [README.md](README.md)、[configs/README.md](configs/README.md)、[scripts/README.md](scripts/README.md)，完善使用说明。

### 验证

- 已执行 `python3 -m py_compile scripts/*.py`，当前脚本语法检查通过。
