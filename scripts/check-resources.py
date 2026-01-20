#!/usr/bin/env python3
"""
Gophish 云资源检查脚本 (Python 跨平台版本)
功能: 查看当前部署的资源状态
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[1;36m'
    NC = '\033[0m'  # No Color

def main():
    script_dir = Path(__file__).parent
    auto_root = script_dir.parent
    
    # 查找所有部署文件
    deployment_files = sorted(auto_root.glob('.deployment-*.json'), 
                             key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not deployment_files:
        print(f"{Colors.YELLOW}未找到任何部署记录{Colors.NC}")
        print()
        print("如需部署，请运行:")
        print(f"  {Colors.CYAN}python scripts/deploy.py -p alibaba -r cn-shanghai{Colors.NC}")
        sys.exit(0)
    
    print()
    print("=" * 70)
    print(f"{Colors.GREEN}📊 Gophish 部署资源列表{Colors.NC}")
    print("=" * 70)
    print()
    
    for i, deploy_file in enumerate(deployment_files, 1):
        try:
            with open(deploy_file, 'r') as f:
                info = json.load(f)
            
            print(f"{Colors.CYAN}[{i}] {info['name']}{Colors.NC}")
            print(f"    云服务商: {info['provider']}")
            print(f"    服务器IP: {Colors.GREEN}{info['ip']}{Colors.NC}")
            print(f"    实例ID:   {info.get('id', 'N/A')}")
            print(f"    部署时间: {info['time']}")
            
            if 'password' in info:
                print(f"    管理密码: {Colors.YELLOW}{info['password']}{Colors.NC}")
            
            print(f"    访问地址:")
            print(f"      管理后台: https://{info['ip']}:3333")
            print(f"      钓鱼页面: http://{info['ip']}")
            print()
        except Exception as e:
            print(f"{Colors.RED}读取文件失败: {deploy_file.name}{Colors.NC}")
            print(f"    错误: {str(e)}")
            print()
    
    print("=" * 70)
    print()
    print(f"{Colors.YELLOW}💡 提示:{Colors.NC}")
    print(f"  销毁资源: {Colors.CYAN}python scripts/destroy.py -p <provider>{Colors.NC}")
    print(f"  查看备份: {Colors.CYAN}ls backups/{Colors.NC}")
    print()

if __name__ == '__main__':
    main()
