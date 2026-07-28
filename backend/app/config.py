"""Settings loaded from environment variables.

本地开发时把配置写在项目根目录 .env 文件里（和 README / .gitignore 同层），
示例见根目录 .env.example。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*a, **kw):  # noqa: D401
        return None


# 根目录：backend/ 的上一级（zhixunyun/）
_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(key)
    if val is None or val == "":
        return default
    return val


# ================== 数据库 ==================
DATABASE_URL = _env(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/eval_system",
)

# ================== JWT ==================
JWT_SECRET = _env("JWT_SECRET", "eval-system-secret-key-2026")
JWT_ALGORITHM = _env("JWT_ALGORITHM", "HS256")
_JWT_EXPIRE_HOURS_RAW = _env("JWT_EXPIRE_HOURS", "24")
try:
    JWT_EXPIRE_HOURS: float = float(_JWT_EXPIRE_HOURS_RAW or "24")
except Exception:  # pragma: no cover
    JWT_EXPIRE_HOURS = 24.0

# ================== AI 服务 ==================
DEEPSEEK_API_KEY = _env("DEEPSEEK_API_KEY", "") or ""
DEEPSEEK_BASE_URL = _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com") or "https://api.deepseek.com"

SILICON_API_KEY = _env("SILICON_API_KEY", "") or ""
SILICON_BASE_URL = (
    _env("SILICON_BASE_URL", "https://api.siliconflow.cn/v1") or "https://api.siliconflow.cn/v1"
)


class Settings:
    """一个轻量的 settings 容器，方便其他模块调用 get_settings() 拿到同一个对象。"""

    def __init__(self) -> None:
        self.DATABASE_URL = DATABASE_URL
        self.JWT_SECRET = JWT_SECRET
        self.JWT_ALGORITHM = JWT_ALGORITHM
        self.JWT_EXPIRE_HOURS = JWT_EXPIRE_HOURS
        self.DEEPSEEK_API_KEY = DEEPSEEK_API_KEY
        self.DEEPSEEK_BASE_URL = DEEPSEEK_BASE_URL
        self.SILICON_API_KEY = SILICON_API_KEY
        self.SILICON_BASE_URL = SILICON_BASE_URL


_SETTINGS_SINGLETON: Optional[Settings] = None


def get_settings() -> Settings:
    global _SETTINGS_SINGLETON
    if _SETTINGS_SINGLETON is None:
        _SETTINGS_SINGLETON = Settings()
    return _SETTINGS_SINGLETON
