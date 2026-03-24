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
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from ssh_utils import resolve_ssh_key_path

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

def setup_credentials(provider: str, env_vars: dict, region: Optional[str] = None) -> dict:
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
    
    if region:
        tf_vars['TF_VAR_region'] = region

    return tf_vars

def find_latest_deployment(auto_root: Path, provider: str) -> Optional[dict]:
    """查找指定云厂商最新的部署信息"""
    deployment_files = list(auto_root.glob('.deployment-*.json'))
    
    if not deployment_files:
        return None

    matched_deployments = []
    for deployment_file in deployment_files:
        try:
            with open(deployment_file, 'r', encoding='utf-8') as f:
                deployment_info = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            log_warn(f"跳过无法读取的部署记录 {deployment_file.name}: {exc}")
            continue

        if deployment_info.get('provider') != provider:
            continue

        deployment_info['file'] = deployment_file
        matched_deployments.append(deployment_info)

    if not matched_deployments:
        return None

    return max(matched_deployments, key=lambda item: item['file'].stat().st_mtime)

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

def load_terraform_state(provider_dir: Path) -> Optional[dict]:
    """读取 Terraform 状态文件。"""
    state_file = provider_dir / 'terraform.tfstate'
    if not state_file.exists():
        return None

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        log_warn(f"读取 Terraform 状态文件失败: {exc}")
        return None

def infer_region_from_zone(provider: str, zone: Optional[str]) -> Optional[str]:
    """根据可用区推断地域。"""
    if not zone:
        return None

    if provider == 'tencent':
        match = re.match(r'^(.*)-\d+$', zone)
        return match.group(1) if match else None

    if provider == 'alibaba':
        match = re.match(r'^(.*)-[a-z]$', zone)
        return match.group(1) if match else None

    if provider == 'huawei':
        match = re.match(r'^(.*\d)[a-z]$', zone)
        return match.group(1) if match else None

    return None

def infer_region_from_state(provider: str, provider_dir: Path) -> Optional[str]:
    """从 Terraform 状态文件中推断地域。"""
    state = load_terraform_state(provider_dir)
    if not state:
        return None

    resource_type_map = {
        'tencent': 'tencentcloud_instance',
        'alibaba': 'alicloud_instance',
        'huawei': 'huaweicloud_compute_instance',
    }
    resource_type = resource_type_map.get(provider)
    if not resource_type:
        return None

    for resource in state.get('resources', []):
        if resource.get('type') != resource_type:
            continue

        for instance in resource.get('instances', []):
            attributes = instance.get('attributes', {})
            zone = (
                attributes.get('availability_zone')
                or attributes.get('zone')
                or attributes.get('availability_zone_name')
            )
            region = infer_region_from_zone(provider, zone)
            if region:
                return region

    return None

def resolve_destroy_region(provider: str, deployment: Optional[dict],
                          env_vars: dict, provider_dir: Path,
                          cli_region: Optional[str] = None) -> Optional[str]:
    """解析销毁时使用的地域。"""
    if cli_region:
        return cli_region

    if deployment and deployment.get('region'):
        return deployment['region']

    region_env_map = {
        'alibaba': 'ALIBABA_CLOUD_REGION',
        'tencent': 'TENCENT_CLOUD_REGION',
        'huawei': 'HUAWEI_CLOUD_REGION',
    }
    env_region_key = region_env_map.get(provider)
    if env_region_key:
        env_region = env_vars.get(env_region_key) or os.getenv(env_region_key)
        if env_region:
            return env_region

    if provider == 'tencent':
        zone = env_vars.get('TENCENT_CLOUD_AVAILABILITY_ZONE') or os.getenv('TENCENT_CLOUD_AVAILABILITY_ZONE')
        region = infer_region_from_zone(provider, zone)
        if region:
            return region

    return infer_region_from_state(provider, provider_dir)

def get_backup_ssh_key(deployment: Optional[dict], env_vars: dict) -> Optional[Path]:
    """获取备份数据库时使用的 SSH 私钥。"""
    preferred_key_path = None

    if deployment:
        preferred_key_path = deployment.get('ssh_key_path')

    if not preferred_key_path:
        preferred_key_path = env_vars.get('SSH_KEY_PATH')

    ssh_key_path = resolve_ssh_key_path(preferred_key_path, log_warn=log_warn)
    if ssh_key_path:
        log_info(f"✓ 使用 SSH 密钥: {ssh_key_path}")
    return ssh_key_path

def get_backup_ssh_user(provider: str, deployment: Optional[dict]) -> str:
    """获取备份数据库时使用的 SSH 用户。"""
    if deployment and deployment.get('ssh_user'):
        return deployment['ssh_user']

    if provider == 'tencent':
        return 'root'

    return 'root'

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
    parser.add_argument('-r', '--region',
                       help='部署地域（未提供时尝试从部署记录或 Terraform 状态推断）')
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
    provider_dir = terraform_dir / args.provider
    
    # 加载环境变量
    env_vars = load_env(config_dir)
    
    # 查找最新部署
    deployment = find_latest_deployment(auto_root, args.provider)
    
    if not deployment:
        log_warn(f"未找到云厂商 {args.provider} 的部署记录")
        log_info("将尝试基于 Terraform 状态推断销毁参数...")
    else:
        log_info(f"找到部署记录: {deployment['name']}")
        log_info(f"  服务器IP: {deployment['ip']}")
        log_info(f"  部署时间: {deployment['time']}")

    destroy_region = resolve_destroy_region(
        args.provider, deployment, env_vars, provider_dir, args.region
    )
    if not destroy_region:
        log_error("无法确定销毁所需的地域，请使用 -r/--region 手动指定")
        sys.exit(1)

    log_info(f"销毁地域: {destroy_region}")

    # 设置云凭证
    tf_vars = setup_credentials(args.provider, env_vars, destroy_region)
    
    # 确认销毁
    if not args.force:
        print()
        print(f"{Colors.YELLOW}⚠️  警告: 即将销毁以下资源:{Colors.NC}")
        print(f"   - 云服务商: {args.provider}")
        print(f"   - 地域: {destroy_region}")
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
        ssh_user = get_backup_ssh_user(args.provider, deployment)
        
        # 检查 SSH 密钥
        ssh_key_path = get_backup_ssh_key(deployment, env_vars)
        if ssh_key_path:
            backup_database(server_ip, ssh_user, ssh_key_path, backup_dir)
        else:
            log_warn("未找到可用的 SSH 密钥，跳过数据库备份")
    
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
