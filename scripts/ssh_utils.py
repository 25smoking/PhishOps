#!/usr/bin/env python3
"""
SSH 密钥辅助函数
"""

import os
from pathlib import Path
from typing import Callable, Optional, Union

COMMON_SSH_KEY_NAMES = (
    'id_ed25519',
    'id_rsa',
    'id_ecdsa',
    'id_dsa',
)


def expand_ssh_key_path(raw_path: Union[str, Path]) -> Path:
    """展开 SSH 密钥路径，兼容 .pub 路径输入。"""
    expanded = os.path.expandvars(os.path.expanduser(str(raw_path)))
    path = Path(expanded)
    if path.suffix == '.pub':
        return Path(str(path)[:-4])
    return path


def get_default_ssh_key_candidates() -> list[Path]:
    """返回常见 SSH 私钥候选路径。"""
    ssh_dir = Path.home() / '.ssh'
    return [ssh_dir / key_name for key_name in COMMON_SSH_KEY_NAMES]


def list_ssh_key_candidates(configured_path: Optional[str] = None) -> list[Path]:
    """列出待检查的 SSH 私钥路径，自动去重。"""
    candidates: list[Path] = []
    if configured_path:
        candidates.append(expand_ssh_key_path(configured_path))
    candidates.extend(get_default_ssh_key_candidates())

    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str in seen:
            continue
        seen.add(candidate_str)
        unique_candidates.append(candidate)
    return unique_candidates


def resolve_ssh_key_path(
    configured_path: Optional[str] = None,
    log_warn: Optional[Callable[[str], None]] = None,
) -> Optional[Path]:
    """解析可用的 SSH 私钥路径。"""
    candidates = list_ssh_key_candidates(configured_path)
    configured_candidate = candidates[0] if configured_path and candidates else None

    for candidate in candidates:
        pub_key_path = Path(f"{candidate}.pub")
        if candidate.exists() and pub_key_path.exists():
            if configured_candidate and candidate != configured_candidate and log_warn:
                log_warn(
                    f"配置的 SSH_KEY_PATH 不可用: {configured_candidate}，"
                    f"已自动切换到可用密钥: {candidate}"
                )
            return candidate

    return None


def read_public_key(private_key_path: Path) -> str:
    """读取 SSH 公钥内容。"""
    return Path(f"{private_key_path}.pub").read_text(encoding='utf-8').strip()
