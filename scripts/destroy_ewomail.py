#!/usr/bin/env python3
"""
EwoMail 云自动化销毁脚本 (Python 跨平台版本)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Dict

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[1;36m'
    NC = '\033[0m'

def log_info(msg: str): print(f"{Colors.GREEN}[信息]{Colors.NC} {msg}")
def log_error(msg: str): print(f"{Colors.RED}[错误]{Colors.NC} {msg}")

def load_env(config_dir: Path) -> Dict[str, str]:
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

def setup_credentials(provider: str, env_vars: Dict[str, str]) -> Dict[str, str]:
    tf_vars = {}
    if provider == 'alibaba':
        tf_vars['TF_VAR_access_key'] = env_vars.get('ALIBABA_CLOUD_ACCESS_KEY_ID') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID', '')
        tf_vars['TF_VAR_secret_key'] = env_vars.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET', '')
    elif provider == 'tencent':
        tf_vars['TF_VAR_secret_id'] = env_vars.get('TENCENT_CLOUD_SECRET_ID') or os.getenv('TENCENT_CLOUD_SECRET_ID', '')
        tf_vars['TF_VAR_secret_key'] = env_vars.get('TENCENT_CLOUD_SECRET_KEY') or os.getenv('TENCENT_CLOUD_SECRET_KEY', '')
        az = env_vars.get('TENCENT_CLOUD_AVAILABILITY_ZONE') or os.getenv('TENCENT_CLOUD_AVAILABILITY_ZONE')
        if az: tf_vars['TF_VAR_availability_zone'] = az
    elif provider == 'huawei':
        tf_vars['TF_VAR_access_key'] = env_vars.get('HUAWEI_CLOUD_ACCESS_KEY') or os.getenv('HUAWEI_CLOUD_ACCESS_KEY', '')
        tf_vars['TF_VAR_secret_key'] = env_vars.get('HUAWEI_CLOUD_SECRET_KEY') or os.getenv('HUAWEI_CLOUD_SECRET_KEY', '')
    return tf_vars

def main():
    parser = argparse.ArgumentParser(description='EwoMail 一键销毁云服务器资源工具')
    parser.add_argument('-p', '--provider', required=True, choices=['alibaba', 'tencent', 'huawei'], help='云服务商')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    auto_root = script_dir.parent
    provider_dir = auto_root / 'terraform' / f'ewomail_{args.provider}'
    config_dir = auto_root / 'configs'

    if not provider_dir.exists():
        log_error(f"未找到 Terraform 目录: {provider_dir}")
        sys.exit(1)

    env_vars = load_env(config_dir)
    tf_vars = setup_credentials(args.provider, env_vars)

    # 填充必要的基础变量以通过校验（无论地域和SSH都可以随便塞一个默认防卡死）
    env = os.environ.copy()
    env.update(tf_vars)
    env['TF_VAR_region'] = "ap-hongkong"
    env['TF_VAR_instance_name'] = "ewomail_destroying"
    env['TF_VAR_ssh_public_key'] = "ssh-rsa AAAA_destroy"
    
    log_info(f"💣 正在为您一键全自动释放 {args.provider} 的 EwoMail 云资产...")
    try:
        subprocess.run(['terraform', 'destroy', '-auto-approve'], cwd=provider_dir, check=True, env=env)
        log_info("✅ EwoMail 云内资源清除完毕，不会再产生任何扣费！")
    except subprocess.CalledProcessError:
        log_error("销毁过程中出现问题，请检查！")

if __name__ == '__main__':
    main()
