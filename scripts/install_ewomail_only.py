#!/usr/bin/env python3
"""
仅安装 EwoMail 的独立脚本 (不含 Terraform 创建机器资源部分)
用于在已经准备好的 CentOS 7/8 服务器上快速部署 EwoMail。
"""

import os
import sys
import time
import argparse
import shlex
import subprocess
from pathlib import Path
from typing import Optional, Dict

from ssh_utils import list_ssh_key_candidates, read_public_key, resolve_ssh_key_path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[1;36m'
    NC = '\033[0m'

def log_info(msg: str): print(f"{Colors.GREEN}[信息]{Colors.NC} {msg}")
def log_warn(msg: str): print(f"{Colors.YELLOW}[警告]{Colors.NC} {msg}")
def log_error(msg: str): print(f"{Colors.RED}[错误]{Colors.NC} {msg}")

def run_command(cmd: list, cwd: Optional[Path] = None, check: bool = True, capture_output: bool = False, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    try:
        cmd_env = env if env is not None else None
        if capture_output:
            return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True, env=cmd_env)
        else:
            return subprocess.run(cmd, cwd=cwd, check=check, env=cmd_env)
    except subprocess.CalledProcessError as e:
        log_error(f"命令执行失败: {' '.join(cmd)}")
        if capture_output and e.stderr: log_error(f"错误信息: {e.stderr}")
        sys.exit(1)

def check_ssh_key(ssh_key_path: Optional[str] = None) -> tuple[Path, str]:
    resolved_key_path = resolve_ssh_key_path(ssh_key_path, log_warn=log_warn)
    if not resolved_key_path:
        log_error("未找到可用的 SSH 密钥")
        sys.exit(1)
    public_key = read_public_key(resolved_key_path)
    if not public_key:
        log_error(f"SSH 公钥内容为空: {resolved_key_path}.pub")
        sys.exit(1)
    log_info(f"✓ 使用 SSH 密钥: {resolved_key_path}")
    return resolved_key_path, public_key

def check_ssh_ready(server_ip: str, ssh_user: str, ssh_key: Path, timeout: int = 60):
    log_info(f"正在测试到 {server_ip} 的 SSH 连接...")
    start_time = time.time()
    last_error = ""
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ['ssh', '-v', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no', 
                 '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', f'{ssh_user}@{server_ip}', 'echo', 'ready'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log_info("✓ SSH 连接成功")
                return
            else:
                last_error = result.stderr.strip().split('\n')[-1] if result.stderr else "未知错误"
                sys.stdout.write(f"\r{Colors.YELLOW}[检测中]{Colors.NC} 尚不可用: {last_error[:50]}... 重试中...")
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"\r{Colors.YELLOW}[检测中]{Colors.NC} 异常: {str(e)[:50]}... 重试中...")
            sys.stdout.flush()
        time.sleep(3)
    print()
    log_error(f"测试连接失败，最后错误: {last_error}")
    sys.exit(1)

def install_ewomail(server_ip: str, ssh_user: str, ssh_key: Path, domain: str):
    safe_domain = shlex.quote(domain)
    log_info(f"🚀 开始在 {server_ip} 纯净部署 EwoMail, 绑定域名: {safe_domain} ...")
    
    install_script = f"""
set -e

echo ">> [1/4] 配置系统环境..."
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

echo ">> [2/4] 安装必要工具..."
if ! grep -q "assumeyes=1" /etc/yum.conf; then
    echo "assumeyes=1" >> /etc/yum.conf
fi
yum clean all || true
yum makecache || true
yum install -y epel-release wget git tar gzip curl

echo ">> [3/4] 拉取代码与安装 EwoMail..."
cd /root
rm -rf ewomail EwoMail
git clone https://gitee.com/laowu5/EwoMail.git ewomail
cd ewomail/install
echo ">> 执行安装脚本，域名: {safe_domain} (这需要10分钟左右)..."
sh ./start.sh {safe_domain}

echo ">> [4/4] EwoMail 部署完成！"
    """

    run_command(['ssh', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no',
                 '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=10',
                f'{ssh_user}@{server_ip}', install_script])

def main():
    parser = argparse.ArgumentParser(description='纯净 EwoMail 远程一键安装脚本 (仅装软件)')
    parser.add_argument('-i', '--ip', required=True, help='目标云服务器的公网 IP')
    parser.add_argument('-d', '--domain', required=True, help='邮箱主域名 (例如: ailinpay.com)')
    parser.add_argument('-u', '--user', default='root', help='SSH 登录用户名 (默认: root)')
    parser.add_argument('-k', '--key', help='SSH 私钥路径 (默认自动寻找 ~/.ssh/id_rsa)')
    args = parser.parse_args()

    ssh_key, _ = check_ssh_key(args.key)
    check_ssh_ready(args.ip, args.user, ssh_key)
    
    install_ewomail(args.ip, args.user, ssh_key, args.domain)
    
    print()
    log_info("✅ EwoMail 独立安装任务完成！")
    print(f"{Colors.YELLOW}📍 后台地址: {Colors.CYAN}http://{args.ip}:8010{Colors.NC}")
    print(f"{Colors.YELLOW}📍 WebMail:  {Colors.CYAN}http://{args.ip}:8000{Colors.NC}")
    print(f"管理员账号: {Colors.GREEN}admin{Colors.NC}  密码: {Colors.GREEN}ewomail123{Colors.NC}")
    print(f"SMTP发件端口 (用于 Gophish 对接): {Colors.GREEN}587{Colors.NC}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log_error("安装被用户手动中断。")
        sys.exit(1)
