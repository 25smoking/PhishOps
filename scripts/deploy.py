#!/usr/bin/env python3
"""
Gophish 云自动化部署脚本 (Python 跨平台版本)
支持: Windows, macOS, Linux
云服务商: 阿里云, 腾讯云, 华为云
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

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
        # 如果提供了env，使用它；否则使用系统环境
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
    
    # 检测操作系统
    import platform
    import shutil
    os_type = platform.system()
    
    for tool in required_tools:
        # 在 Windows 上尝试 .exe 扩展名
        tool_cmd = tool
        if os_type == 'Windows':
            tool_cmd = tool + '.exe'
        
        # 使用 shutil.which 查找命令
        found = shutil.which(tool) or shutil.which(tool_cmd)
        
        if not found:
            log_error(f"缺少必要工具: {tool}")
            print()
            
            # 提供针对性的安装指导
            if tool in ['ssh', 'scp']:
                log_info(f"{tool} 是 OpenSSH 的一部分，请按以下方式安装：")
                print()
                if os_type == 'Windows':
                    print(f"{Colors.CYAN}Windows 安装方法（三选一）:{Colors.NC}")
                    print()
                    print("【方法一】使用 Chocolatey (推荐):")
                    print("  choco install openssh -y")
                    print()
                    print("【方法二】使用 Scoop:")
                    print("  scoop install openssh")
                    print("  然后关闭并重新打开 PowerShell")
                    print()
                    print("【方法三】使用 Windows 设置:")
                    print("  设置 → 应用 → 可选功能 → 添加功能 → OpenSSH 客户端")
                    print()
                    print("【方法四】使用 PowerShell (管理员):")
                    print("  Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0")
                elif os_type == 'Darwin':  # macOS
                    print(f"{Colors.CYAN}macOS:{Colors.NC} OpenSSH 已预装，如果缺失请运行:")
                    print("  brew install openssh")
                else:  # Linux
                    print(f"{Colors.CYAN}Linux 安装方法:{Colors.NC}")
                    print("  # Ubuntu/Debian")
                    print("  sudo apt install openssh-client")
                    print()
                    print("  # CentOS/RHEL")
                    print("  sudo yum install openssh-clients")
            elif tool == 'terraform':
                log_info("请安装 Terraform:")
                print()
                if os_type == 'Windows':
                    print(f"{Colors.CYAN}Windows:{Colors.NC}")
                    print("  choco install terraform -y")
                    print("  或")
                    print("  scoop install terraform")
                elif os_type == 'Darwin':
                    print(f"{Colors.CYAN}macOS:{Colors.NC}")
                    print("  brew install terraform")
                else:
                    print(f"{Colors.CYAN}Linux:{Colors.NC}")
                    print("  参考: https://www.terraform.io/downloads.html")
            
            print()
            log_error(f"请安装 {tool} 后重新运行脚本")
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
                    # 展开环境变量（如 $HOME）
                    expanded_value = os.path.expandvars(value.strip())
                    # 对于Windows，也尝试展开PowerShell风格的变量
                    if '$HOME' in expanded_value and 'HOME' not in os.environ:
                        # Windows没有HOME环境变量，使用USERPROFILE
                        expanded_value = expanded_value.replace('$HOME', str(Path.home()))
                    env_vars[key.strip()] = expanded_value
        return env_vars
    else:
        log_warn(f"未找到配置文件: {env_file}，将使用系统环境变量")
        return {}

def check_ssh_key(ssh_key_path: Optional[str] = None) -> tuple[Path, str]:
    """检查 SSH 密钥"""
    if not ssh_key_path:
        ssh_key_path = Path.home() / '.ssh' / 'id_rsa'
    else:
        ssh_key_path = Path(ssh_key_path)
    
    pub_key_path = Path(str(ssh_key_path) + '.pub')
    
    if not pub_key_path.exists():
        log_error(f"未找到 SSH 公钥: {pub_key_path.absolute()}")
        log_error("请先生成 SSH 密钥: ssh-keygen -t rsa -b 4096")
        print()
        print(f"提示: 生成密钥时，连续按3次回车即可（全部使用默认值）")
        sys.exit(1)
    
    with open(pub_key_path, 'r') as f:
        public_key = f.read().strip()
    
    return ssh_key_path, public_key

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
        # 可选：可用区
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
    provider_dir = terraform_dir / provider
    
    log_info("正在初始化 Terraform...")
    
    # 设置环境变量
    env = os.environ.copy()
    env.update(tf_vars)
    env['TF_VAR_region'] = region
    env['TF_VAR_instance_name'] = instance_name
    env['TF_VAR_ssh_public_key'] = ssh_public_key
    if instance_type:
        env['TF_VAR_instance_type'] = instance_type
    
    # 传递可用区变量 (如果存在)
    if 'TF_VAR_availability_zone' in tf_vars:
        env['TF_VAR_availability_zone'] = tf_vars['TF_VAR_availability_zone']
    
    # Terraform init
    run_command(['terraform', 'init', '-upgrade'], cwd=provider_dir, check=True, env=env)
    
    log_info("正在创建云服务器 (这可能需要几分钟)...")
    
    # Terraform apply
    run_command(['terraform', 'apply', '-auto-approve'], cwd=provider_dir, check=True, env=env)
    
    # 获取输出
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
    log_info("正在等待服务器 SSH 就绪...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ['ssh', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no', 
                 '-o', 'ConnectTimeout=5', f'{ssh_user}@{server_ip}', 'echo ready'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
            )
            if result.returncode == 0:
                log_info("✓ SSH 连接成功")
                return
        except subprocess.TimeoutExpired:
            pass
        time.sleep(10)
    
    log_error("无法连接到服务器 SSH")
    sys.exit(1)

def configure_server(server_ip: str, ssh_user: str, ssh_key: Path, script_dir: Path):
    """配置服务器环境"""
    log_info("正在初始化服务器环境 (安装 Docker 等)...")
    
    setup_script = script_dir / 'setup-server.sh'
    
    # 上传脚本
    run_command(['scp', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no',
                str(setup_script), f'{ssh_user}@{server_ip}:/tmp/'])
    
    # 执行脚本
    run_command(['ssh', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no',
                f'{ssh_user}@{server_ip}', 
                'chmod +x /tmp/setup-server.sh && sudo /tmp/setup-server.sh'])

def deploy_gophish(server_ip: str, ssh_user: str, ssh_key: Path, 
                   auto_root: Path, git_repo: str, git_branch: str) -> Optional[str]:
    """部署 Gophish 应用 (服务器原生编译模式)"""
    log_info("🚀 开始部署流程 (服务器原生编译模式)...")
    
    # 构建服务器端执行的脚本
    # 使用官方源下载
    go_version = "1.22.0"
    go_url = f"https://go.dev/dl/go{go_version}.linux-amd64.tar.gz"
    repo_mirror_url = git_repo.replace("github.com", "mirror.ghproxy.com/github.com")
    
    install_script = f"""
    set -e
    
    # 0. 清理旧环境
    echo ">> [1/5] 清理环境..."
    systemctl stop gophish || true
    rm -rf /opt/gophish
    mkdir -p /opt/gophish
    
    # 1. 安装基础依赖 (根据系统自动检测)
    echo ">> [2/5] 安装系统依赖..."
    if command -v apt-get &> /dev/null; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update && apt-get install -y curl git tar gzip gcc
    elif command -v yum &> /dev/null; then
        yum install -y curl git tar gzip gcc
    fi
    
    # 2. 安装 Go 环境
    if ! command -v go &> /dev/null; then
        echo ">> [3/5] 安装 Go {go_version}..."
        curl -L -o /tmp/go.tar.gz {go_url}
        rm -rf /usr/local/go && tar -C /usr/local -xzf /tmp/go.tar.gz
        rm /tmp/go.tar.gz
        ln -sf /usr/local/go/bin/go /usr/bin/go
    else
        echo ">> [3/5] Go 已安装: $(go version)"
    fi
    
    # 设置 Go 环境变量
    export PATH=$PATH:/usr/local/go/bin
    export GOPROXY=https://goproxy.cn,direct
    
    # 3. 拉取代码 & 编译
    echo ">> [4/5] 拉取代码并编译..."
    cd /opt/gophish
    
    # 尝试使用镜像克隆，如果失败退回原地址
    echo "Cloning from {repo_mirror_url}..."
    if ! git clone -b {git_branch} --depth 1 {repo_mirror_url} .; then
        echo "Mirror clone failed, trying original..."
        git clone -b {git_branch} --depth 1 {git_repo} .
    fi
    
    echo "Compiling Gophish..."
    # 禁用 CGO 以避免依赖问题，或者确保 gcc 已安装
    export CGO_ENABLED=1 
    go build -v -o gophish .
    
    # 4. 配置服务
    echo ">> [5/5] 配置系统服务..."
    chmod +x gophish
    
    cat > /etc/systemd/system/gophish.service <<EOF
[Unit]
Description=Gophish Open-Source Phishing Toolkit
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/gophish
ExecStart=/opt/gophish/gophish
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable gophish
    
    # 修改监听地址为 0.0.0.0 (允许外网访问)
    echo ">> [6/5] 配置监听地址..."
    sed -i 's/127.0.0.1:3333/0.0.0.0:3333/g' /opt/gophish/config.json
    
    systemctl restart gophish
    
    echo ">> 部署完成！"
    """

    # 执行远程脚本
    run_command(['ssh', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no',
                f'{ssh_user}@{server_ip}', install_script])
    
    # 5. 获取密码
    log_info(">> 正在获取初始管理员密码...")
    time.sleep(5) # 等待日志生成
    
    try:
        # 从 systemd 日志获取密码 (尝试多次)
        for _ in range(3):
            result = run_command(['ssh', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no',
                                f'{ssh_user}@{server_ip}', 
                                "journalctl -u gophish -n 100 --no-pager | grep -i 'password' | tail -n1"],
                                capture_output=True, check=False)
            
            output = result.stdout.strip()
            if 'password' in output.lower():
                parts = output.split()
                for i, part in enumerate(parts):
                    if 'password' in part.lower() and i + 1 < len(parts):
                        password = parts[i + 1].strip(':').strip().strip('"')
                        return password
            time.sleep(2)
        return None
    except:
        return None

def save_deployment_info(auto_root: Path, deployment_name: str, provider: str,
                        server_ip: str, instance_id: str, password: Optional[str]):
    """保存部署信息"""
    deploy_info = {
        'name': deployment_name,
        'provider': provider,
        'ip': server_ip,
        'id': instance_id,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if password:
        deploy_info['password'] = password
    
    deploy_file = auto_root / f'.deployment-{deployment_name}.json'
    with open(deploy_file, 'w') as f:
        json.dump(deploy_info, f, indent=2)

def print_success_message(server_ip: str, ssh_user: str, ssh_key: Path, password: Optional[str]):
    """打印部署成功信息"""
    log_info("✅ 部署完成！")
    print()
    print("=" * 56)
    print(f"{Colors.GREEN}🎉 Gophish 部署成功！{Colors.NC}")
    print("=" * 56)
    print()
    print(f"{Colors.YELLOW}📍 访问信息:{Colors.NC}")
    print(f"   管理后台: {Colors.CYAN}https://{server_ip}:3333{Colors.NC}")
    print(f"   钓鱼页面: {Colors.CYAN}http://{server_ip}{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}🔑 管理员登录:{Colors.NC}")
    print(f"   用户名: {Colors.GREEN}admin{Colors.NC}")
    if password:
        print(f"   密码:   {Colors.GREEN}{password}{Colors.NC}")
    else:
        print(f"   密码:   {Colors.RED}(自动获取失败，请手动查看下方命令){Colors.NC}")
    print()
    print(f"{Colors.YELLOW}🖥️  SSH 登录:{Colors.NC}")
    print(f"   IP地址:   {server_ip}")
    print(f"   用户名:   {ssh_user}")
    print(f"   认证方式: SSH密钥 (无需密码)")
    print(f"   登录命令: {Colors.CYAN}ssh -i {ssh_key} {ssh_user}@{server_ip}{Colors.NC}")
    print()
    if not password:
        print(f"{Colors.YELLOW}⚠️  获取密码命令 (登录SSH后执行):{Colors.NC}")
        print(f"   {Colors.CYAN}journalctl -u gophish -n 50 --no-pager | grep password{Colors.NC}")
        print()
    print(f"{Colors.YELLOW}💡 提示:{Colors.NC}")
    print("   - 首次登录管理后台会要求修改密码")
    print("   - 密码已保存到部署信息文件中")
    print("   - 使用 python scripts/destroy.py 可销毁资源")
    print("=" * 56)

def main():
    parser = argparse.ArgumentParser(
        description='Gophish 云自动化部署工具 (Python 跨平台版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/deploy.py -p alibaba -r cn-shanghai
  python scripts/deploy.py -p tencent -r ap-guangzhou -b dev
        """
    )
    
    parser.add_argument('-p', '--provider', required=True,
                       choices=['alibaba', 'tencent', 'huawei'],
                       help='云服务商')
    parser.add_argument('-r', '--region', required=True,
                       help='部署区域 (例如: cn-shanghai)')
    parser.add_argument('-t', '--type', dest='instance_type',
                       help='实例规格 (默认: 2核4G)')
    parser.add_argument('-g', '--git', dest='git_repo',
                       default='https://github.com/25smoking/GophisModified.git',
                       help='Git 仓库地址')
    parser.add_argument('-b', '--branch', dest='git_branch',
                       default='master',
                       help='Git 分支 (默认: master)')
    
    args = parser.parse_args()
    
    # 目录设置
    script_dir = Path(__file__).parent
    auto_root = script_dir.parent
    terraform_dir = auto_root / 'terraform'
    config_dir = auto_root / 'configs'
    
    # 部署名称 - 使用更短的格式以符合云服务商限制（如腾讯云key_name最大25字符）
    # 格式: gophish_MMDDHHMMSS (15字符)
    deployment_name = f"gophish{datetime.now().strftime('%m%d%H%M%S')}"
    
    # 检查依赖
    check_dependencies()
    
    # 加载环境变量
    env_vars = load_env(config_dir)
    
    # 检查 SSH 密钥
    ssh_key_path_str = env_vars.get('SSH_KEY_PATH')
    ssh_key, ssh_public_key = check_ssh_key(ssh_key_path_str)
    
    # 设置云凭证
    tf_vars = setup_credentials(args.provider, env_vars)
    
    # 部署基础设施
    server_ip, instance_id = deploy_infrastructure(
        terraform_dir, args.provider, args.region,
        deployment_name, args.instance_type, ssh_public_key, tf_vars
    )
    
    # 确定 SSH 用户
    ssh_user = 'root'
    
    # 等待 SSH 就绪
    wait_for_ssh(server_ip, ssh_user, ssh_key)
    
    # 配置服务器 (已包含在 deploy_gophish 中)
    # configure_server(server_ip, ssh_user, ssh_key, script_dir)
    
    # 部署 Gophish
    password = deploy_gophish(server_ip, ssh_user, ssh_key, auto_root,
                             args.git_repo, args.git_branch)
    
    # 保存部署信息
    save_deployment_info(auto_root, deployment_name, args.provider,
                        server_ip, instance_id, password)
    
    # 打印成功信息
    print_success_message(server_ip, ssh_user, ssh_key, password)

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
