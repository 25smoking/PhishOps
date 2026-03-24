#!/usr/bin/env python3
"""
EwoMail 云自动化部署脚本 (Python 跨平台版本)
支持: Windows, macOS, Linux
云服务商: 阿里云, 腾讯云, 华为云
"""

import os
import sys
import json
import time
import argparse
import shlex
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

from ssh_utils import list_ssh_key_candidates, read_public_key, resolve_ssh_key_path

# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[1;36m'
    NC = '\033[0m'  # No Color

def log_info(msg: str):
    print(f"{Colors.GREEN}[信息]{Colors.NC} {msg}")

def log_warn(msg: str):
    print(f"{Colors.YELLOW}[警告]{Colors.NC} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[错误]{Colors.NC} {msg}")

def run_command(cmd: list, cwd: Optional[Path] = None, check: bool = True, capture_output: bool = False, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    """执行系统命令"""
    try:
        cmd_env = env if env is not None else None
        
        if capture_output:
            result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True, env=cmd_env)
        else:
            result = subprocess.run(cmd, cwd=cwd, check=check, env=cmd_env)
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"命令执行失败: {' '.join(cmd)}")
        if capture_output and e.stderr:
            log_error(f"错误信息: {e.stderr}")
        sys.exit(1)

def check_dependencies():
    """检查必要的依赖工具"""
    log_info("正在检查环境依赖...")
    required_tools = ['terraform', 'ssh', 'scp']
    
    import platform
    import shutil
    os_type = platform.system()
    
    for tool in required_tools:
        tool_cmd = tool
        if os_type == 'Windows':
            tool_cmd = tool + '.exe'
        
        found = shutil.which(tool) or shutil.which(tool_cmd)
        
        if not found:
            log_error(f"缺少必要工具: {tool}")
            sys.exit(1)
    
    log_info("✓ 依赖检查通过")

def load_env(config_dir: Path) -> Dict[str, str]:
    """加载环境变量"""
    env_file = config_dir / '.env'
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    expanded_value = os.path.expandvars(value.strip())
                    if '$HOME' in expanded_value and 'HOME' not in os.environ:
                        expanded_value = expanded_value.replace('$HOME', str(Path.home()))
                    env_vars[key.strip()] = expanded_value
        return env_vars
    else:
        log_warn(f"未找到配置文件: {env_file}，将使用系统环境变量")
        return {}

def check_ssh_key(ssh_key_path: Optional[str] = None) -> tuple[Path, str]:
    """检查 SSH 密钥"""
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

def setup_credentials(provider: str, env_vars: Dict[str, str]) -> Dict[str, str]:
    """设置云凭证环境变量"""
    tf_vars = {}
    
    if provider == 'alibaba':
        access_key = env_vars.get('ALIBABA_CLOUD_ACCESS_KEY_ID') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
        secret_key = env_vars.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        if not access_key:
            log_error("缺少阿里云 AccessKey ID")
            sys.exit(1)
        tf_vars['TF_VAR_access_key'] = access_key
        tf_vars['TF_VAR_secret_key'] = secret_key
    
    elif provider == 'tencent':
        secret_id = env_vars.get('TENCENT_CLOUD_SECRET_ID') or os.getenv('TENCENT_CLOUD_SECRET_ID')
        secret_key = env_vars.get('TENCENT_CLOUD_SECRET_KEY') or os.getenv('TENCENT_CLOUD_SECRET_KEY')
        if not secret_id:
            log_error("缺少腾讯云 Secret ID")
            sys.exit(1)
        tf_vars['TF_VAR_secret_id'] = secret_id
        tf_vars['TF_VAR_secret_key'] = secret_key
        az = env_vars.get('TENCENT_CLOUD_AVAILABILITY_ZONE') or os.getenv('TENCENT_CLOUD_AVAILABILITY_ZONE')
        if az:
            tf_vars['TF_VAR_availability_zone'] = az
    
    elif provider == 'huawei':
        access_key = env_vars.get('HUAWEI_CLOUD_ACCESS_KEY') or os.getenv('HUAWEI_CLOUD_ACCESS_KEY')
        secret_key = env_vars.get('HUAWEI_CLOUD_SECRET_KEY') or os.getenv('HUAWEI_CLOUD_SECRET_KEY')
        if not access_key:
            log_error("缺少华为云 Access Key")
            sys.exit(1)
        tf_vars['TF_VAR_access_key'] = access_key
        tf_vars['TF_VAR_secret_key'] = secret_key
    
    else:
        log_error(f"不支持的服务商: {provider}")
        sys.exit(1)
    
    return tf_vars

def deploy_infrastructure(terraform_dir: Path, provider: str, region: str, 
                         instance_name: str, instance_type: Optional[str],
                         ssh_public_key: str, tf_vars: Dict[str, str]) -> tuple[str, str]:
    """部署基础设施"""
    provider_dir = terraform_dir / f"ewomail_{provider}"
    
    if not provider_dir.exists():
        log_error(f"未找到对应的 Terraform 模板目录: {provider_dir}")
        sys.exit(1)

    log_info(f"正在 {provider_dir} 初始化 Terraform...")
    
    env = os.environ.copy()
    env.update(tf_vars)
    env['TF_VAR_region'] = region
    env['TF_VAR_instance_name'] = instance_name
    env['TF_VAR_ssh_public_key'] = ssh_public_key
    if instance_type:
        env['TF_VAR_instance_type'] = instance_type
    
    if 'TF_VAR_availability_zone' in tf_vars:
        env['TF_VAR_availability_zone'] = tf_vars['TF_VAR_availability_zone']
    
    run_command(['terraform', 'init', '-upgrade'], cwd=provider_dir, check=True, env=env)
    
    log_info("正在创建云服务器 (这可能需要几分钟)...")
    
    run_command(['terraform', 'apply', '-auto-approve'], cwd=provider_dir, check=True, env=env)
    
    result = run_command(['terraform', 'output', '-raw', 'public_ip'], 
                        cwd=provider_dir, check=True, capture_output=True, env=env)
    server_ip = result.stdout.strip()
    
    result = run_command(['terraform', 'output', '-raw', 'instance_id'], 
                        cwd=provider_dir, check=True, capture_output=True, env=env)
    instance_id = result.stdout.strip()
    
    log_info(f"✓ 服务器创建成功: {server_ip} ({instance_id})")
    
    return server_ip, instance_id

def wait_for_ssh(server_ip: str, ssh_user: str, ssh_key: Path, timeout: int = 300):
    """等待 SSH 连接就绪"""
    log_info("正在等待服务器 SSH 就绪 (这可能需要 1~3 分钟)...")
    
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
        except subprocess.TimeoutExpired:
            sys.stdout.write(f"\r{Colors.YELLOW}[检测中]{Colors.NC} 探测超时，继续重试...")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"\r{Colors.YELLOW}[检测中]{Colors.NC} 异常: {str(e)[:50]}... 重试中...")
            sys.stdout.flush()
        time.sleep(10)
    
    print()
    log_error(f"无法连接到服务器 SSH，最后错误: {last_error}")
    sys.exit(1)

def deploy_ewomail(server_ip: str, ssh_user: str, ssh_key: Path, 
                   auto_root: Path, domain: str) -> Optional[str]:
    """部署 EwoMail 应用"""
    safe_domain = shlex.quote(domain)
    log_info(f"🚀 开始部署 EwoMail, 域名为: {safe_domain} ...")
    
    install_script = f"""
set -e

echo ">> [1/4] 配置系统环境..."
# 关闭 SELinux
if [ -f /etc/sysconfig/selinux ]; then
    sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
    setenforce 0 || true
fi

# 配置 Swap (如果不存在则创建一个 2GB 的 swapfile)
if ! swapon --show | grep -q 'swapfile'; then
    if ! grep -q "swap" /etc/fstab; then
        echo ">> 创建 Swap 分区..."
        fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048 oflag=direct
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
fi

echo ">> [2/4] 安装必要工具..."
# 确保后续所有 start.sh 中漏掉 -y 的 yum 命令全部自动确认
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
    
    return "ewomail123"

def save_deployment_info(auto_root: Path, deployment_name: str, provider: str,
                        region: str, server_ip: str, instance_id: str,
                        ssh_user: str, password: Optional[str], ssh_key_path: Path):
    """保存部署信息"""
    deploy_info = {
        'name': deployment_name,
        'provider': provider,
        'region': region,
        'ip': server_ip,
        'id': instance_id,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ssh_user': ssh_user,
        'ssh_key_path': str(ssh_key_path)
    }
    
    if password:
        deploy_info['password'] = password
    
    deploy_file = auto_root / f'.deployment-ewomail-{deployment_name}.json'
    with open(deploy_file, 'w', encoding='utf-8') as f:
        json.dump(deploy_info, f, ensure_ascii=False, indent=2)

def print_success_message(server_ip: str, ssh_user: str, ssh_key: Path, password: Optional[str], domain: str):
    """打印部署成功信息"""
    log_info("✅ 部署完成！")
    print()
    print("=" * 56)
    print(f"{Colors.GREEN}🎉 EwoMail 部署成功！{Colors.NC}")
    print("=" * 56)
    print()
    print(f"{Colors.YELLOW}📍 访问信息:{Colors.NC}")
    print(f"   WebMail邮箱界面: {Colors.CYAN}http://{server_ip}:8000{Colors.NC}")
    print(f"   EwoMail管理后台: {Colors.CYAN}http://{server_ip}:8010{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}🔑 默认登录信息:{Colors.NC}")
    print(f"  后台管理登录:")
    print(f"   用户名: {Colors.GREEN}admin{Colors.NC}")
    print(f"   密码:   {Colors.GREEN}{password}{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}🖥️  SSH 登录:{Colors.NC}")
    print(f"   IP地址:   {server_ip}")
    print(f"   用户名:   {ssh_user}")
    print(f"   登录命令: {Colors.CYAN}ssh -i {ssh_key} {ssh_user}@{server_ip}{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}💡 提示:{Colors.NC}")
    print(f"   - 请确保将您的域名 {domain} 解析 (A记录) 指向 {server_ip}")
    print("   - 初始密码仅限第一次登录有效，登录后请立即修改。")
    print("=" * 56)

def main():
    parser = argparse.ArgumentParser(
        description='EwoMail 云自动化部署工具 (Python 跨平台版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/deploy_ewomail.py -p alibaba -r cn-shanghai -d mail.example.com
  python scripts/deploy_ewomail.py -p tencent -r ap-guangzhou -d email.example.com
        """
    )
    
    parser.add_argument('-p', '--provider', required=True,
                       choices=['alibaba', 'tencent', 'huawei'],
                       help='云服务商')
    parser.add_argument('-r', '--region', required=True,
                       help='部署区域 (例如: cn-shanghai)')
    parser.add_argument('-d', '--domain', required=True,
                       help='邮箱主域名 (例如: mail.example.com)')
    parser.add_argument('-t', '--type', dest='instance_type',
                       help='实例规格 (默认: 2核4G)')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    auto_root = script_dir.parent
    terraform_dir = auto_root / 'terraform'
    config_dir = auto_root / 'configs'
    
    deployment_name = f"ewomail{datetime.now().strftime('%m%d%H%M%S')}"
    
    check_dependencies()
    
    env_vars = load_env(config_dir)
    
    ssh_key_path_str = env_vars.get('SSH_KEY_PATH')
    ssh_key, ssh_public_key = check_ssh_key(ssh_key_path_str)
    
    tf_vars = setup_credentials(args.provider, env_vars)
    
    server_ip, instance_id = deploy_infrastructure(
        terraform_dir, args.provider, args.region,
        deployment_name, args.instance_type, ssh_public_key, tf_vars
    )
    
    ssh_user = 'root'
    
    wait_for_ssh(server_ip, ssh_user, ssh_key)
    
    password = deploy_ewomail(server_ip, ssh_user, ssh_key, auto_root, args.domain)
    
    save_deployment_info(auto_root, deployment_name, args.provider,
                        args.region, server_ip, instance_id,
                        ssh_user, password, ssh_key)
    
    print_success_message(server_ip, ssh_user, ssh_key, password, args.domain)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log_error("\n部署被用户中断")
        sys.exit(1)
    except Exception as e:
        log_error(f"部署过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
