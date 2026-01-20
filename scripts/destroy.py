#!/usr/bin/env python3
"""
Gophish 云资源销毁脚本 (Python 跨平台版本)
支持: Windows, macOS, Linux
功能: 自动备份数据库并销毁云资源
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

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

def run_command(cmd: list, cwd: Optional[Path] = None, check: bool = True, capture_output: bool = False, env: Optional[dict] = None) -> subprocess.CompletedProcess:
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
        if check:
            sys.exit(1)
        return e

def load_env(config_dir: Path) -> dict:
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

def setup_credentials(provider: str, env_vars: dict) -> dict:
    """设置云凭证环境变量"""
    tf_vars = {}
    
    if provider == 'alibaba':
        access_key = env_vars.get('ALIBABA_CLOUD_ACCESS_KEY_ID') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
        secret_key = env_vars.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        if access_key:
            tf_vars['TF_VAR_access_key'] = access_key
            tf_vars['TF_VAR_secret_key'] = secret_key
    elif provider == 'tencent':
        secret_id = env_vars.get('TENCENT_CLOUD_SECRET_ID') or os.getenv('TENCENT_CLOUD_SECRET_ID')
        secret_key = env_vars.get('TENCENT_CLOUD_SECRET_KEY') or os.getenv('TENCENT_CLOUD_SECRET_KEY')
        if secret_id:
            tf_vars['TF_VAR_secret_id'] = secret_id
            tf_vars['TF_VAR_secret_key'] = secret_key
    elif provider == 'huawei':
        access_key = env_vars.get('HUAWEI_CLOUD_ACCESS_KEY') or os.getenv('HUAWEI_CLOUD_ACCESS_KEY')
        secret_key = env_vars.get('HUAWEI_CLOUD_SECRET_KEY') or os.getenv('HUAWEI_CLOUD_SECRET_KEY')
        if access_key:
            tf_vars['TF_VAR_access_key'] = access_key
            tf_vars['TF_VAR_secret_key'] = secret_key
    
    return tf_vars

def find_latest_deployment(auto_root: Path) -> Optional[dict]:
    """查找最新的部署信息"""
    deployment_files = list(auto_root.glob('.deployment-*.json'))
    
    if not deployment_files:
        return None
    
    # 按修改时间排序
    latest_file = max(deployment_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        deployment_info = json.load(f)
    
    deployment_info['file'] = latest_file
    return deployment_info

def backup_database(server_ip: str, ssh_user: str, ssh_key: Path, backup_dir: Path):
    """备份数据库"""
    log_info("正在备份 Gophish 数据库...")
    
    # 确保备份目录存在
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_file = backup_dir / f'gophish-{timestamp}.db'
    
    try:
        # 从服务器下载数据库
        result = run_command(
            ['scp', '-i', str(ssh_key), '-o', 'StrictHostKeyChecking=no',
             f'{ssh_user}@{server_ip}:/opt/gophish/gophish.db',
             str(backup_file)],
            check=False, capture_output=True
        )
        
        if result.returncode == 0:
            log_info(f"✓ 数据库已备份到: {backup_file}")
            return True
        else:
            log_warn("数据库备份失败（可能不存在或服务器已关闭）")
            return False
    except Exception as e:
        log_warn(f"数据库备份失败: {str(e)}")
        return False

def destroy_infrastructure(terraform_dir: Path, provider: str, tf_vars: dict):
    """销毁基础设施"""
    provider_dir = terraform_dir / provider
    
    log_info("正在销毁云资源...")
    
    # 设置环境变量
    env = os.environ.copy()
    env.update(tf_vars)
    
    # Terraform destroy
    run_command(['terraform', 'destroy', '-auto-approve', '-lock=false'], cwd=provider_dir, env=env)
    
    log_info("✓ 云资源已销毁")

def cleanup_deployment_file(deployment_file: Path):
    """清理部署信息文件"""
    try:
        deployment_file.unlink()
        log_info(f"✓ 清理部署记录: {deployment_file.name}")
    except Exception as e:
        log_warn(f"清理部署记录失败: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='Gophish 云资源销毁工具 (Python 跨平台版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/destroy.py -p alibaba
  python scripts/destroy.py -p tencent --no-backup
        """
    )
    
    parser.add_argument('-p', '--provider', required=True,
                       choices=['alibaba', 'tencent', 'huawei'],
                       help='云服务商')
    parser.add_argument('--no-backup', action='store_true',
                       help='跳过数据库备份')
    parser.add_argument('--force', action='store_true',
                       help='强制销毁（不提示确认）')
    
    args = parser.parse_args()
    
    # 目录设置
    script_dir = Path(__file__).parent
    auto_root = script_dir.parent
    terraform_dir = auto_root / 'terraform'
    backup_dir = auto_root / 'backups'
    config_dir = auto_root / 'configs'
    
    # 加载环境变量和设置凭证
    env_vars = load_env(config_dir)
    tf_vars = setup_credentials(args.provider, env_vars)
    
    # 查找最新部署
    deployment = find_latest_deployment(auto_root)
    
    if not deployment:
        log_warn("未找到部署记录")
        log_info("将尝试销毁 Terraform 管理的资源...")
    else:
        log_info(f"找到部署记录: {deployment['name']}")
        log_info(f"  服务器IP: {deployment['ip']}")
        log_info(f"  部署时间: {deployment['time']}")
    
    # 确认销毁
    if not args.force:
        print()
        print(f"{Colors.YELLOW}⚠️  警告: 即将销毁以下资源:{Colors.NC}")
        print(f"   - 云服务商: {args.provider}")
        if deployment:
            print(f"   - 服务器IP: {deployment['ip']}")
            print(f"   - 实例ID: {deployment.get('id', 'N/A')}")
        print()
        response = input(f"{Colors.RED}确定要继续吗? (yes/no): {Colors.NC}").strip().lower()
        if response not in ['yes', 'y']:
            log_info("销毁操作已取消")
            sys.exit(0)
    
    # 备份数据库
    if not args.no_backup and deployment:
        server_ip = deployment['ip']
        ssh_user = 'ubuntu' if args.provider == 'tencent' else 'root'
        
        # 检查 SSH 密钥
        ssh_key_path = Path.home() / '.ssh' / 'id_rsa'
        if ssh_key_path.exists():
            backup_database(server_ip, ssh_user, ssh_key_path, backup_dir)
        else:
            log_warn("未找到 SSH 密钥，跳过数据库备份")
    
    # 销毁基础设施
    destroy_infrastructure(terraform_dir, args.provider, tf_vars)
    
    # 清理部署记录
    if deployment and 'file' in deployment:
        cleanup_deployment_file(deployment['file'])
    
    # 打印完成信息
    print()
    print("=" * 56)
    print(f"{Colors.GREEN}✅ 资源销毁完成！{Colors.NC}")
    print("=" * 56)
    print()
    if not args.no_backup:
        print(f"{Colors.YELLOW}📦 数据备份位置:{Colors.NC}")
        print(f"   {backup_dir}")
        print()
    print(f"{Colors.YELLOW}💡 提示:{Colors.NC}")
    print("   - 所有云资源已释放，不再产生费用")
    print("   - 备份文件已保存在本地")
    print("   - 如需重新部署，运行: python scripts/deploy.py")
    print("=" * 56)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log_error("\n销毁操作被用户中断")
        sys.exit(1)
    except Exception as e:
        log_error(f"销毁过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
