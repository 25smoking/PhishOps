# 配置文件说明

本目录用于存放 Gophish 云部署工具的配置文件。

## 快速开始

### 1. 创建配置文件

```bash
cd configs
cp .env.example .env
```

### 2. 编辑配置文件

使用你喜欢的编辑器打开 `.env` 文件:

```bash
vim .env
# 或
nano .env
```

### 3. 填写云服务商凭证

根据你要使用的云服务商,填写对应的 AccessKey/SecretKey。

---

## 配置项详解

### 阿里云 (Alibaba Cloud)

如果你选择部署到阿里云,需要填写以下配置:

```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=your_actual_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_actual_secret_key
```

**获取方式:**
1. 登录阿里云控制台
2. 访问 [RAM 访问控制](https://ram.console.aliyun.com/manage/ak)
3. 创建或查看 AccessKey

**权限要求:**
- ECS 实例管理权限
- VPC 网络管理权限
- 安全组管理权限

---

### 腾讯云 (Tencent Cloud)

如果你选择部署到腾讯云,需要填写以下配置:

```bash
TENCENT_CLOUD_SECRET_ID=your_actual_secret_id
TENCENT_CLOUD_SECRET_KEY=your_actual_secret_key
```

**获取方式:**
1. 登录腾讯云控制台
2. 访问 [API 密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 创建或查看密钥

**权限要求:**
- CVM 实例管理权限
- VPC 网络管理权限
- 安全组管理权限

---

### 华为云 (Huawei Cloud)

如果你选择部署到华为云,需要填写以下配置:

```bash
HUAWEI_CLOUD_ACCESS_KEY=your_actual_access_key
HUAWEI_CLOUD_SECRET_KEY=your_actual_secret_key
```

**获取方式:**
1. 登录华为云控制台
2. 访问 [我的凭证](https://console.huaweicloud.com/iam/#/mine/accessKey)
3. 创建或查看访问密钥

**权限要求:**
- ECS 实例管理权限
- VPC 网络管理权限
- 安全组管理权限

---

## SSH 密钥配置

### 默认配置

脚本会自动检测以下常见 SSH 密钥：

- `~/.ssh/id_ed25519`
- `~/.ssh/id_rsa`
- `~/.ssh/id_ecdsa`
- `~/.ssh/id_dsa`

如果你在 `.env` 中配置了 `SSH_KEY_PATH`，脚本会优先使用该路径。

### 生成 SSH 密钥 (如果没有)

```bash
ssh-keygen
# 一路回车即可，macOS / Linux 通常会默认生成 ~/.ssh/id_ed25519

# 如需兼容旧环境，也可以显式生成 RSA
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### 使用自定义路径

如果你的 SSH 密钥在其他位置,在 `.env` 文件中添加:

```bash
SSH_KEY_PATH=/path/to/your/private_key
```

---

## 高级配置

### 自定义 Git 仓库

如果你 fork 了项目并想使用自己的仓库:

```bash
GIT_REPO=https://github.com/your_username/YourRepo.git
GIT_BRANCH=dev  # 或其他分支
```

**注意:** 仓库必须是公开的,或者服务器有访问权限 (配置 SSH Key)。

### 实例名称前缀

```bash
INSTANCE_NAME_PREFIX=my-gophish
```

部署时会自动添加时间戳,例如: `my-gophish-20260109-143000`

---

## 安全建议

1. **不要提交 `.env` 文件到 Git**
   - `.gitignore` 已默认忽略 `.env` 文件
   - 只提交 `.env.example` 作为模板

2. **定期轮换密钥**
   - 建议每 90 天更换一次 AccessKey
   - 云服务商都支持创建多个密钥

3. **使用最小权限原则**
   - AccessKey 只授予部署所需的最小权限
   - 考虑使用子账号而非主账号

4. **保护 SSH 私钥**
   - 确保私钥文件权限为 600: `chmod 600 ~/.ssh/id_ed25519`
   - 不要在公共场合泄露私钥

---

## 故障排查

### 提示 "缺少阿里云 AccessKey ID"

**原因:** `.env` 文件未正确加载或凭证未填写

**解决:**
1. 确认 `.env` 文件在 `configs/` 目录
2. 确认文件名正确 (不是 `.env.txt` 或其他)
3. 检查配置项名称是否正确
4. 尝试在命令行手动导出: `export ALIBABA_CLOUD_ACCESS_KEY_ID=xxx`

### 提示 "未找到 SSH 公钥"

**原因:** SSH 密钥不存在或路径错误

**解决:**
1. 生成 SSH 密钥: `ssh-keygen`
2. 确认公钥存在: `ls -la ~/.ssh/id_ed25519.pub` 或 `ls -la ~/.ssh/id_rsa.pub`
3. 检查 `.env` 中的 `SSH_KEY_PATH` 是否正确

### Git Clone 失败

**原因:** 服务器无法访问 GitHub 或仓库是私有的

**解决:**
1. 确保仓库是公开的
2. 检查服务器出站网络是否正常
3. 如需使用私有仓库,需配置 Deploy Key (高级功能)

---

## 示例: 完整的阿里云配置

```bash
# 云凭证
ALIBABA_CLOUD_ACCESS_KEY_ID=LTAI5tAbCdEf123456789
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_32_char_secret_key_here

# SSH 密钥 (使用默认路径)
SSH_KEY_PATH=$HOME/.ssh/id_ed25519

# Git 仓库 (使用官方仓库)
# 不需要修改,使用默认值
```

完成配置后,运行部署:

```bash
./scripts/deploy.sh -p alibaba -r cn-shanghai
```

---

## 支持的区域代码

### 阿里云

- `cn-hangzhou` (杭州)
- `cn-shanghai` (上海)
- `cn-beijing` (北京)
- `cn-shenzhen` (深圳)
- `cn-hongkong` (香港)

### 腾讯云

- `ap-guangzhou` (广州)
- `ap-shanghai` (上海)
- `ap-beijing` (北京)
- `ap-chengdu` (成都)
- `ap-hongkong` (香港)

### 华为云

- `cn-north-1` (北京一)
- `cn-north-4` (北京四)
- `cn-east-2` (上海二)
- `cn-south-1` (广州)
- `ap-southeast-1` (香港)

---

如有问题,请查看 [主文档](../README.md) 或提交 Issue。
