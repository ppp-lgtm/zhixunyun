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
_BACKEND_DIR = _ROOT / "backend"
_CWD_DIR = Path.cwd()

# ══════════════════════════════════════════════════════════════════════════════
# .env 加载：多位置依次尝试（优先级从高到低，后加载不会覆盖已存在的同名环境变量）
#   1) 启动目录的 .env              (最高优先级：如从 backend/ 启动就 backend/.env)
#   2) 启动目录的 .env.local        (本地覆盖，如本机特殊配置)
#   3) 项目根目录 zhixunyun/ .env   (标准位置)
#   4) 项目根目录 zhixunyun/ .env.example — 仅当 .env 缺失时兜底（用户常忘复制改名）
# 最后两个 (.env/.env.example) 也在 _CWD_DIR 再各查一份，兼容任何启动 cwd
# ══════════════════════════════════════════════════════════════════════════════
_ENV_SEARCH_ORDER = [
    # (path, is_fallback_only, comment)
    (_CWD_DIR / ".env",          False, "cwd/.env (最高优先级)"),
    (_CWD_DIR / ".env.local",    False, "cwd/.env.local"),
    (_ROOT / ".env",             False, "project-root/.env (标准位置)"),
    (_BACKEND_DIR / ".env",      False, "backend/.env"),
    (_ROOT / ".env.example",     True,  "project-root/.env.example (仅在 .env 缺失时使用)"),
    (_CWD_DIR / ".env.example",  True,  "cwd/.env.example (仅在 .env 缺失时使用)"),
]

# 先判断 .env 有没有存在于任何正式位置（用来决定是否启用 .env.example 兜底）
def _has_any_official_env() -> bool:
    official = [p for p, _, _ in _ENV_SEARCH_ORDER[:4] if p.exists() and p.is_file()]
    return len(official) > 0

_has_official = _has_any_official_env()

ENV_LOAD_REPORT: list[dict] = []

for _p, _fb_only, _comment in _ENV_SEARCH_ORDER:
    if _fb_only and _has_official:
        # .env.example 只在 .env 未放置时才读取，避免示例值覆盖真实值
        ENV_LOAD_REPORT.append({
            "path": str(_p), "loaded": False, "comment": _comment,
            "reason": "SKIP — 已找到正式 .env 文件，不读取 .env.example",
        })
        continue
    if not _p.exists() or not _p.is_file():
        ENV_LOAD_REPORT.append({
            "path": str(_p), "loaded": False, "comment": _comment,
            "reason": "NOT FOUND",
        })
        continue
    try:
        # override=False：.env 里已有同名变量不被后来的 .env.example 覆盖
        _loaded = load_dotenv(_p, override=False, encoding="utf-8")
        ENV_LOAD_REPORT.append({
            "path": str(_p), "loaded": bool(_loaded), "comment": _comment,
            "reason": "OK" if _loaded else "already-set(override=False未覆盖)",
        })
    except Exception as _e:
        ENV_LOAD_REPORT.append({
            "path": str(_p), "loaded": False, "comment": _comment,
            "reason": f"READ_ERROR: {_e}",
        })


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(key)
    if val is None or val == "":
        return default
    return val


# ================== 数据库 ==================
# NOTE: 项目全程只允许 MySQL / PostgreSQL。
# 如果你写了 sqlite:// 或其他本地文件数据库，run.py 会在启动时直接拒绝并报错，
# 绝对不会"默默降级"，避免数据写到 Navicat 看不到的位置。
#
# MySQL 连接参数说明（和 Navicat 新建连接时的面板一一对应）：
#   Host     = localhost
#   Port     = 3306
#   Username = root
#   Password = root
#   Database = eval_system
#   Charset  = utf8mb4（支持 emoji 和任意中文）
DATABASE_URL = _env(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/eval_system?charset=utf8mb4",
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
        # ══════════════════════════════════════════════════════════════
        # 启动时 .env 加载诊断报告（只读，诊断文本用；不包含任何密钥值）
        # ══════════════════════════════════════════════════════════════
        self.ENV_LOAD_REPORT = list(ENV_LOAD_REPORT)  # shallow copy
        self.ENV_HAS_OFFICIAL = _has_official
        # 用于提示：.env.example 中有没有实际填了 DEEPSEEK_API_KEY 非默认占位（≠ '' & ≠ 'sk-your-xxx'）
        _candidate = (
            _ROOT / ".env.example" if (_ROOT / ".env.example").exists()
            else (_CWD_DIR / ".env.example" if (_CWD_DIR / ".env.example").exists() else None)
        )
        self.ENV_EXAMPLE_HAS_DEEPSEEK = False
        self.ENV_EXAMPLE_PATH = str(_candidate) if _candidate is not None else ""
        if _candidate is not None:
            try:
                _text = _candidate.read_text(encoding="utf-8", errors="ignore")
                import re as _re
                _m = _re.search(r"^[\s]*DEEPSEEK_API_KEY[\s]*=[\s]*(.*)[\s]*$", _text, _re.MULTILINE)
                if _m:
                    _v = _m.group(1).strip().strip('"').strip("'")
                    _blacklist = {"", "sk-your-api-key", "sk-xxx", "sk-your-deepseek-key", "sk-your"}
                    if _v not in _blacklist and len(_v) >= 8:
                        self.ENV_EXAMPLE_HAS_DEEPSEEK = True
            except Exception:
                pass


_SETTINGS_SINGLETON: Optional[Settings] = None


def get_settings() -> Settings:
    global _SETTINGS_SINGLETON
    if _SETTINGS_SINGLETON is None:
        _SETTINGS_SINGLETON = Settings()
    return _SETTINGS_SINGLETON
