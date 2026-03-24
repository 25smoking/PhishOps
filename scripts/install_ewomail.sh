#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "========================================="
    echo "错误：缺少域名参数！"
    echo "使用方法: bash install_ewomail.sh <域名>"
    echo "示例: bash install_ewomail.sh ailinpay.com"
    echo "========================================="
    exit 1
fi

DOMAIN=$1

echo "🚀 开始在当前服务器安装 EwoMail, 绑定域名: $DOMAIN ..."
echo ">> [1/4] 配置系统环境 (关闭 SELinux 与配置域名解析)..."
# 强行保障本地域名正常解析，防止 EwoMail 灌库失败导致“域不允许”、“密码错误”
HOSTNAME="mail.$DOMAIN"
hostnamectl set-hostname $HOSTNAME
sed -i '/127.0.0.1/d' /etc/hosts
echo "127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4 $HOSTNAME $DOMAIN smtp.$DOMAIN imap.$DOMAIN" >> /etc/hosts

if [ -f /etc/sysconfig/selinux ]; then
    sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
    setenforce 0 || true
fi

if ! swapon --show | grep -q 'swapfile'; then
    if ! grep -q "swap" /etc/fstab; then
        echo ">> 创建 Swap 分区 (2GB)..."
        fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048 oflag=direct
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
fi

echo ">> [2/4] 安装必要工具与规避 yum 卡死..."
if ! grep -q "assumeyes=1" /etc/yum.conf; then
    echo "assumeyes=1" >> /etc/yum.conf
fi
yum clean all || true
yum makecache || true
yum install -y epel-release wget git tar gzip curl

echo ">> [3/4] 拉取稳定版代码与编译 EwoMail..."
cd /root
rm -rf ewomail EwoMail
git clone https://gitee.com/laowu5/EwoMail.git ewomail
cd ewomail/install
echo ">> 执行最终架构脚本（此步骤预计耗时 10 到 15 分钟，请不要关闭终端窗口！！！）..."
sh ./start.sh "$DOMAIN"

echo "================================================="
echo ">> [4/4] 🎉 EwoMail 本地独立安装部署完成！"
echo "================================================="
# 尝试获取外网IP方便展示
PUBLIC_IP=$(curl -s ifconfig.me || echo "你的公网IP")
echo "📍 WebMail 访问:  http://$PUBLIC_IP:8000"
echo "📍 管理后台 访问:  http://$PUBLIC_IP:8010"
echo "🔑 操作帐号: admin  默认密码: ewomail123"
echo "🔑 发件服务 SMTP 端口: 587（供 Gophish 配置使用）"
echo "================================================="
