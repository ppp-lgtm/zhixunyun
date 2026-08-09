r"""
Zhixunyun Backend - One-file Launcher (run.py)
===============================================

这是新的统一启动入口。比之前的 serve.py 语义更直观，功能更全：

  - 依赖自检：fastapi / uvicorn / sqlalchemy / pydantic 等核心包缺一就提示；
  - 启动只连 MySQL：没有任何 SQLite 兜底分支；连接失败会明确报错并退出；
  - 目录兜底：uploads/ / reports/ 不存在就自动建；
  - 端口占用：探测 + 列出占用进程 PID + 给一键 kill 命令；
  - venv 友好：检测到当前解释器不在 venv/.venv 里就提示先激活；
  - Banner：启动后集中打印 API Docs / Health / Uploads 三个 URL，方便快速打开。

用户使用步骤（Windows CMD 一条龙）：

    cd g:\b1提交物\code\zhixunyun\backend
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python run.py --init-mysql       (第一次：连 MySQL SERVER 创建 eval_system 库)
    python run.py                    (平时：127.0.0.1:8000)
    python run.py --port 8001        (切端口)
    python run.py --host 0.0.0.0     (局域网可访问)

全程输出英文，避免 cmd.exe cp936/GBK 乱码。
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# 固定工作目录：无论用户从哪打命令，都把 CWD 固定到 backend/
# 这样 uploads/ / reports/ 能稳定落到 backend/ 下
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


# ===========================================================================
# 0. 颜色 / Banner 工具（不依赖第三方库，仅在 Windows 下 colorama 生效）
# ===========================================================================
def _colorama_init() -> None:
    try:
        import colorama  # type: ignore
        colorama.just_fix_windows_console()
    except Exception:
        pass


_colorama_init()


class C:
    OK = "\033[32m"     # green
    WARN = "\033[33m"   # yellow
    ERR = "\033[31m"    # red
    INFO = "\033[36m"   # cyan
    BOLD = "\033[1m"
    RESET = "\033[0m"


def banner(host: str, port: int, db_url_display: str, detected_venv: bool) -> None:
    sep = "=" * 68
    print()
    print(sep)
    print(f"   {C.BOLD}ZhiXunYun Backend{C.RESET}  v2.0  (One-file launcher: run.py)")
    print(f"   project root : {ROOT}")
    print(f"   python exe   : {sys.executable}")
    if not detected_venv:
        print(f"   {C.WARN}WARN: not running inside venv/.venv; "
              f"activate first via venv\\Scripts\\activate{C.RESET}")
    print(f"   database     : {C.INFO}{db_url_display}{C.RESET}")
    print(sep)
    print(f"   {C.BOLD}Quick Links (Ctrl+click to open):{C.RESET}")
    print(f"     [{C.INFO}Home{C.RESET}]       http://{host}:{port}/")
    print(f"     [{C.INFO}Docs{C.RESET}]       http://{host}:{port}/docs")
    print(f"     [{C.INFO}Redoc{C.RESET}]      http://{host}:{port}/redoc")
    print(f"     [{C.INFO}Health{C.RESET}]     http://{host}:{port}/api/health")
    print(f"     [{C.INFO}Test{C.RESET}]       http://{host}:{port}/api/test")
    if host == "0.0.0.0":
        print(f"   {C.WARN}WARNING: bound to 0.0.0.0 - LAN accessible, "
              f"ensure firewall rules fit your needs.{C.RESET}")
    print(sep)
    # ══════════════════════════════════════════════════════════════
    # .ENV 加载摘要 + AI Key 状态（只读环境变量，不含密钥内容）
    # ══════════════════════════════════════════════════════════════
    try:
        from app.config import get_settings
        _s = get_settings()
        _rep = getattr(_s, "ENV_LOAD_REPORT", None) or []
        _loaded = [r for r in _rep if r.get("loaded")]
        _missed = [r for r in _rep if str(r.get("reason", "")) == "NOT FOUND"]
        _skipped = [r for r in _rep if str(r.get("reason", "")).startswith("SKIP")]
        _failed = [r for r in _rep if not r.get("loaded") and r not in _missed and r not in _skipped]

        print(f"   {C.BOLD}.ENV Load Summary{C.RESET}")
        print(f"     loaded    : {len(_loaded):>2d} file(s)")
        if _loaded:
            for r in _loaded:
                print(f"        + {r.get('path','')}")
        if _skipped:
            print(f"     skipped   : {len(_skipped):>2d}  (已找到正式 .env，跳过 .env.example fallback)")
        if _failed:
            print(f"     failed    : {len(_failed):>2d}  (READ_ERROR/already-set)")
        # AI Key 状态（不含密钥）
        def _key_status(name: str, k: str):
            if not k:
                return (C.WARN, "NOT SET")
            if k in {"sk-your-api-key", "sk-xxx", "sk-your-deepseek-key"}:
                return (C.WARN, "EXAMPLE PLACEHOLDER")
            if k.startswith("sk-") and len(k) < 16:
                return (C.WARN, f"TOO SHORT ({len(k)} chars)")
            return (C.OK, f"OK (prefix {k[:6]}..., len {len(k)})")
        _ds_status = _key_status("DEEPSEEK", getattr(_s, "DEEPSEEK_API_KEY", ""))
        _si_status = _key_status("SILICON", getattr(_s, "SILICON_API_KEY", ""))
        print(f"   {C.BOLD}AI Keys{C.RESET} (no secrets, len/prefix only)")
        print(f"     DeepSeek  : {_ds_status[0]}{_ds_status[1]}{C.RESET}")
        print(f"     Silicon   : {_si_status[0]}{_si_status[1]}{C.RESET}")
        # 典型场景提示
        if _ds_status[0] == C.WARN and getattr(_s, "ENV_EXAMPLE_HAS_DEEPSEEK", False):
            _ex_path = getattr(_s, "ENV_EXAMPLE_PATH", "")
            print(f"   {C.WARN}→ HINT: .env.example 里已填了 DeepSeek Key，但当前没生效。{C.RESET}")
            if _ex_path:
                print(f"        .env.example = {_ex_path}")
            cmd_hint = "cd " + str(ROOT) + "> if(-not(Test-Path .env)){Copy-Item .env.example .env}"
            print("        若之前版本的 config.py 只读取了 .env.example fallback，请 Ctrl+C 重启后端即可生效；")
            print("        或执行：" + cmd_hint)
        print(sep)
    except Exception as _env_diag_err:
        # 诊断失败不影响主启动流程，静默吞错
        pass


# ===========================================================================
# 1. 依赖自检：缺啥就直接给 pip 命令，不要等 uvicorn 启动后再 ImportError
# ===========================================================================
REQUIRED_CORE = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("sqlalchemy", "SQLAlchemy"),
    ("pydantic", "pydantic"),
]

OPTIONAL_WARN = [
    # NOTE: PyPI name != python import name.  PyMySQL is installed via pip but
    # imported as `pymysql` (lowercase).
    ("pymysql", "PyMySQL"),   # required when DATABASE_URL is mysql+pymysql://...
    ("dotenv", "python-dotenv"),
]


def dependency_preflight() -> tuple[bool, list[str]]:
    """Return (ok, missing_msgs). 核心包缺即 fail；可选包缺仅 yellow WARN。"""
    missing_core: list[str] = []
    missing_opt: list[str] = []
    for mod, pip_name in REQUIRED_CORE:
        try:
            __import__(mod)
        except Exception:
            missing_core.append(pip_name)
    for mod, pip_name in OPTIONAL_WARN:
        try:
            __import__(mod)
        except Exception:
            missing_opt.append(pip_name)
    if missing_opt:
        print(f"{C.WARN}[WARN]{C.RESET} optional package(s) not installed: "
              f"{', '.join(missing_opt)}")
        print(f"       install: pip install {' '.join(missing_opt)}")
    if missing_core:
        print(f"{C.ERR}[FAIL]{C.RESET} core package(s) not installed: "
              f"{', '.join(missing_core)}")
        print(f"       install: pip install {' '.join(missing_core)}")
        print(f"       or     : pip install -r requirements.txt")
        return False, missing_core
    return True, []


# ===========================================================================
# 2. 目录自检：uploads/ reports/ 必须存在（StaticFiles mount 依赖）
# ===========================================================================
def ensure_dirs() -> None:
    for d in ("uploads", "reports"):
        p = ROOT / d
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            print(f"{C.INFO}[DIR ]{C.RESET} created missing folder: {d}/")


# ===========================================================================
# 3. 数据库兜底：若没有 DATABASE_URL 且 MySQL 连不上，自动切 SQLite，
#    绝不让第一次启动就卡死在 MySQL connection refused
# ===========================================================================
def _sanitize_db_url(url: str) -> str:
    """Hide the password from display output (safe for banners / logs).

    Avoids the regex look-behind fixed-width bug: Python stdlib's `re` only accepts
    fixed-width look-behind patterns so (?<=://...) chokes if the user:password part
    contains special chars of variable length; a simple manual split is robust
    portable across all dialect URLs and raises no re.error.
    """
    if "://" not in url:
        return url
    schema, rest = url.split("://", 1)
    if "@" not in rest:
        return url  # no user:password
    creds, remainder = rest.split("@", 1)
    if ":" not in creds:
        return url  # user without password, nothing to mask
    user, _password = creds.split(":", 1)
    return f"{schema}://{user}:***@{remainder}"


# ===========================================================================
# 3b. Apply a new DATABASE_URL to the live singletons (NOT just os.environ).
#
# This is the critical piece that was missing:
#   app.config.DATABASE_URL / _SETTINGS_SINGLETON  are evaluated at module
#   import time;  app.models.database.engine/SessionLocal  are also built
#   once.  Writing a new value into  os.environ['DATABASE_URL']  AFTER those
#   modules have been imported does NOTHING.  apply_new_database_url()
#   explicitly rewires both singletons AND the module-level bindings that
#   every router imports from `from app.models.database import X`.
#
# 项目约束：只允许 MySQL / PostgreSQL。任何 sqlite:///... 或其他本地文件
# 数据库一律在入口这里直接拒绝，避免"悄悄写到本地文件"的历史问题。
# ===========================================================================
def apply_new_database_url(effective_url: str) -> None:
    """Propagate ``effective_url`` as the authoritative DATABASE_URL.

    Actions (idempotent, safe to call repeatedly):
      1. write into ``os.environ`` so any future ``_env(...)`` call sees it
      2. patch ``app.config.DATABASE_URL`` and drop the cached Settings singleton
         so a new call to ``get_settings()`` builds a fresh object with the
         new URL (no importlib.reload of the whole module -> no risk of
         clobbering other module-level initialisation done elsewhere).
      3. dispose the old engine (if any) to release open sockets / connections
      4. build a fresh engine + sessionmaker, then patch the 3 public names
         on ``app.models.database`` that every downstream consumer imports:
         ``engine``, ``SessionLocal``, ``DATABASE_URL``.

    The module-level ``Base = declarative_base()`` on app.models.database is
    NEVER rebuilt - the model classes registered onto it keep their bound
    metadata (which is what Base.metadata.create_all() walks).  Only the
    *connections* the pool opens are re-routed to the new target.
    """
    from sqlalchemy import create_engine as _create_engine
    from sqlalchemy.orm import sessionmaker as _sessionmaker

    # Hard guard: NO local / file-based databases allowed at runtime.
    if not (effective_url.startswith("mysql") or effective_url.startswith("postgresql")):
        print(f"{C.ERR}[FAIL]{C.RESET} project is locked to MySQL/PostgreSQL "
              f"only; got DATABASE_URL={effective_url!r}.  Fix .env or --db-url.")
        raise SystemExit(2)

    # (1) environment
    os.environ["DATABASE_URL"] = effective_url

    # (2) app.config layer (patch bindings, do NOT reload module -> safer)
    import app.config as _acfg
    _acfg.DATABASE_URL = effective_url  # type: ignore[attr-defined]
    _acfg._SETTINGS_SINGLETON = None    # drop singleton
    _acfg.get_settings()                # rebuild now (best-effort, not fatal)

    # (3) + (4) app.models.database layer (patch bindings, NO reload)
    import app.models.database as _adb

    try:
        old_engine = getattr(_adb, "engine", None)
        if old_engine is not None:
            old_engine.dispose()
    except Exception:  # pragma: no cover - best effort
        pass

    new_engine = _create_engine(
        effective_url,
        echo=False,
        future=True,
        connect_args={},
    )
    new_SessionLocal = _sessionmaker(
        bind=new_engine, autoflush=False, autocommit=False,
    )
    _adb.engine = new_engine           # type: ignore[attr-defined]
    _adb.DATABASE_URL = effective_url  # type: ignore[attr-defined]
    _adb.SessionLocal = new_SessionLocal  # type: ignore[attr-defined]


# ===========================================================================
# 3c. Database bootstrap: probe MySQL (init if requested) and fail loudly
#     if anything is wrong.  NO SILENT FALLBACK TO LOCAL FILES EVER.
#
# New semantic rules (user demanded: "明确使用mysql，另一个数据库的相关
# 文件都删掉不要留痕"):
#   * --db-url override wins everything (db_url_override argument)
#   * only mysql+pymysql:// or postgresql:///... URLs are allowed at runtime.
#     If user accidentally sets a sqlite:// or any other file URL, we EXIT 2
#     immediately with a clear error, so writes NEVER go to an unexpected place.
#   * probe always runs. If probe fails, we EXIT 1 with troubleshooting steps
#     matched to the Navicat connection panel.
#   * --init-mysql: BEFORE probing the DB, connect to MySQL SERVER (strip the
#     database name from URL) and run  CREATE DATABASE IF NOT EXISTS <db>
#     CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  so Navicat can see it.
# ===========================================================================
def database_bootstrap(
    db_url_override: str | None = None,
    force_mysql: bool = False,
    init_mysql: bool = False,
) -> str:
    """
    Probe current DATABASE_URL (after dotenv load + optional --db-url override).
    Returns the sanitized display URL (password masked).
    """
    # Ensure dotenv is loaded into os.environ early
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        def load_dotenv(*a, **kw):  # fallback
            return None
    env_file = ROOT.parent / ".env"   # backend/.. = zhixunyun/
    if env_file.exists():
        load_dotenv(env_file)

    from sqlalchemy import create_engine as _create_engine, text as _text
    from sqlalchemy import make_url as _make_url
    import app.config as _acfg

    # 1) cmdline override wins everything; write to env so all subsequent reads
    #    (including apply_new_database_url / get_settings) see it.
    if db_url_override:
        cleaned = db_url_override.strip()
        if cleaned:
            os.environ["DATABASE_URL"] = cleaned

    env_url = (os.environ.get("DATABASE_URL") or "").strip()

    # Default used only if neither .env nor --db-url set anything.
    DEFAULT_URL = (
        "mysql+pymysql://root:root@localhost:3306/eval_system?charset=utf8mb4"
    )

    effective_candidate = env_url or DEFAULT_URL

    # --- Hard reject any non-MySQL/PostgreSQL URL up front. ------------------
    if not (effective_candidate.startswith("mysql") or effective_candidate.startswith("postgresql")):
        print(f"{C.ERR}[FAIL]{C.RESET} project is locked to MySQL/PostgreSQL ONLY.")
        print(f"       got DATABASE_URL = {effective_candidate!r}")
        print(f"       fix: write the MySQL URL into backend/.env OR pass --db-url")
        raise SystemExit(2)

    # --- pre-step: --init-mysql ------------------------------------------------
    if init_mysql:
        if effective_candidate.startswith("mysql"):
            try:
                _u = _make_url(effective_candidate)
                db_name = _u.database
                if db_name:
                    _server_url = _u.set(database=None)
                    _probe = _create_engine(
                        _server_url.render_as_string(hide_password=False),
                        echo=False, future=True, connect_args={"connect_timeout": 4},
                    )
                    with _probe.connect() as conn:
                        # MySQL DDL is implicitly committing; ensure no open txn
                        conn.execute(_text("COMMIT"))
                        conn.execute(
                            _text(
                                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                                "DEFAULT CHARACTER SET utf8mb4 "
                                "COLLATE utf8mb4_unicode_ci"
                            )
                        )
                    try:
                        _probe.dispose()
                    except Exception:
                        pass
                    print(f"{C.OK}[INIT]{C.RESET} MySQL ensured database: `{db_name}` (utf8mb4)")
            except Exception as exc:
                print(f"{C.ERR}[FAIL]{C.RESET} --init-mysql failed on "
                      f"{_sanitize_db_url(effective_candidate)}: {exc}")
                raise
        else:
            print(f"{C.WARN}[WARN]{C.RESET} --init-mysql only applies to mysql+pymysql URLs; "
                  f"current is {effective_candidate.split(':',1)[0]}")

    # --- ONLY branch that remains: MySQL / PostgreSQL (probe + fail loudly)
    effective_sa_url = None
    effective: str | None = None
    try:
        effective_sa_url = _make_url(effective_candidate)
        probe = _create_engine(
            effective_candidate, echo=False, future=True,
            connect_args={"connect_timeout": 3} if effective_candidate.startswith("mysql") else {},
        )
        with probe.connect() as conn:
            conn.execute(_text("SELECT 1"))
        try:
            probe.dispose()
        except Exception:
            pass
        effective = effective_candidate
    except Exception as exc:
        print(f"{C.ERR}[FAIL]{C.RESET} DATABASE probe failed: {exc}")
        sep = "=" * 68
        print(sep)
        print("   TROUBLESHOOTING (match Navicat connection panel):")
        print("     - 1) Is MySQL running? Can Navicat 'Test Connection' succeed?")
        print("           Fix host/port/firewall/MySQL service first.")
        print("     - 2) Username / password match Navicat?")
        print("     - 3) Database already exists? run:  python run.py --init-mysql")
        if effective_sa_url is not None:
            print(
                f"     - target   host={effective_sa_url.host or 'localhost'}  "
                f"port={effective_sa_url.port or 3306}  "
                f"user={effective_sa_url.username or 'root'}  "
                f"database={effective_sa_url.database or 'eval_system'}"
            )
        print(sep)
        raise SystemExit(1)

    # --- finalise: apply effective URL to ALL singletons -------------------
    apply_new_database_url(effective)

    # Smoke-check the now-applied engine (go through app.models.database so
    # we know router-lifetime sessions use the same target).
    try:
        from app.models.database import engine as _eng
        with _eng.connect() as conn:
            conn.execute(_text("SELECT 1"))
    except Exception as exc:
        print(f"{C.ERR}[FAIL]{C.RESET} cannot open final database "
              f"({_sanitize_db_url(effective)}): {exc}")
        raise

    # Build display string (password masked)
    display = _sanitize_db_url(effective)
    if effective.startswith("mysql") or effective.startswith("postgresql"):
        try:
            u = _make_url(effective)
            display = (
                f"{u.drivername}://{u.username or '?'}@"
                f"{u.host or 'localhost'}:{u.port or (3306 if 'mysql' in u.drivername else 5432)}"
                f"/{u.database or '?'}"
            )
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # DB LOCATOR stdout block - so users NEVER wonder "where did writes go".
    # -----------------------------------------------------------------------
    print()
    print("-" * 68)
    from app.models.database import engine as _eng_final
    from sqlalchemy import inspect as _si
    _insp = _si(_eng_final)
    _tables = sorted(_insp.get_table_names())
    _users_count = -1
    if "users" in _tables:
        try:
            with _eng_final.connect() as _c:
                _users_count = _c.execute(_text("SELECT COUNT(*) FROM users")).scalar()
        except Exception:
            _users_count = -1
    try:
        u = _make_url(effective)
        print(f"{C.BOLD} DB LOCATOR: {u.drivername.upper()}{C.RESET}")
        print(f"   host             = {u.host or 'localhost'}")
        print(f"   port             = {u.port or 3306}")
        print(f"   user             = {u.username or 'root'}")
        print(f"   database         = {u.database or 'eval_system'}")
        print(f"   charset          = utf8mb4")
        print(f"   Navicat:  open {u.database or 'eval_system'} →  Tables →  users  →  F5 (Refresh)")
    except Exception:
        print(f"{C.BOLD} DB LOCATOR: REMOTE{C.RESET}  url={display}")
    print(f"   dialect          = {_eng_final.dialect.name}")
    print(f"   table count      = {len(_tables)}")
    print(f"   users row count  = {_users_count if _users_count >= 0 else '(no users table)'}")
    print("-" * 68)
    print()
    return display


# ===========================================================================
# 4. venv 检测：提醒用户是否真的在 venv 里
# ===========================================================================
def detect_venv() -> bool:
    exe = Path(sys.executable)
    parts = [p.lower() for p in exe.parts]
    if "venv" in parts or ".venv" in parts:
        return True
    # macOS/linux style: project/.venv/bin/python
    if "bin" in parts and ("venv" in parts or ".venv" in parts):
        return True
    if os.environ.get("VIRTUAL_ENV"):
        return True
    return False


# ===========================================================================
# 5. Database bootstrap (auto-create tables / pre-flight health check).
#    Ensures MySQL (eval_system) has all tables BEFORE uvicorn starts,
#    so the first /api/auth/login does not hit "no such table: users".
# ===========================================================================
def ensure_models_loaded() -> None:
    """Import all model modules so they register their tables on Base.metadata.

    SQLAlchemy 2.x only picks up a class in Base.metadata.create_all() when the
    module defining that class has been imported at least once.  The routers
    import them lazily but run.py wants to create_all BEFORE any request arrives,
    so we force-import them here (with clear error if any module breaks).
    """
    # NOTE: ordered by FK dependency to avoid "referenced table does not exist"
    # warnings (users -> enterprises -> enterprise_mentors -> classes/class_members
    # -> tasks -> submissions -> evaluations/...).
    try:
        import app.models.tables            # noqa: F401
        import app.models.enterprise_models # noqa: F401
        import app.models.class_models      # noqa: F401
    except Exception as e:
        print(f"{C.ERR}[FAIL]{C.RESET} cannot import model modules: {e}")
        raise


def database_create_all() -> int:
    """Create all missing tables (idempotent). Returns number of newly created tables.

    Strategy:
      1. call ensure_models_loaded() so every __tablename__ is registered.
      2. compute current physical table set by reflecting the engine (works for
         any SQLAlchemy-supported remote DB: MySQL, PostgreSQL).
      3. diff against Base.metadata.tables, call create_all() (which itself is
         safe), then count the diff so we can print a human-readable delta.
    """
    from sqlalchemy import inspect as _sa_inspect
    from app.models.database import Base, engine

    ensure_models_loaded()

    before: set[str] = set(_sa_inspect(engine).get_table_names())
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"{C.ERR}[FAIL]{C.RESET} Base.metadata.create_all raised: {e}")
        raise
    after: set[str] = set(_sa_inspect(engine).get_table_names())
    created = sorted(after - before)

    # Quick smoke SELECT 1 to prove DB is reachable
    try:
        from sqlalchemy import text as _text
        with engine.connect() as conn:
            conn.execute(_text("SELECT 1"))
    except Exception as e:
        print(f"{C.ERR}[FAIL]{C.RESET} DB post-create sanity SELECT 1 failed: {e}")
        raise

    n = len(created)
    if n == 0:
        print(f"{C.INFO}[DB  ]{C.RESET} schema OK - {len(after)} tables present "
              f"(0 newly created, idempotent)")
    else:
        print(f"{C.OK}[DB  ]{C.RESET} schema ready - created {n} new table(s):")
        for t in created:
            print(f"         + {t}")
    return n


# ===========================================================================
# 6. Port occupancy probe (RUN.PY LOCAL COPY - avoids importing app.main
#    early, which would trigger the module-level uvicorn import-time probe
#    and cause FAIL banner to print twice).
#    Logic mirrors app.main._port_probe, kept in sync manually.
# ===========================================================================
def local_port_probe(host: str, port: int, exit_on_occupy: bool = False,
                     launcher_script: str = "run.py") -> bool:
    """Run.py's own port-probe (run BEFORE app.main is imported).

    This avoids the triple-FAIL banner from handshakes:
      run_uvicorn() -> from app.main import _port_probe  [prints FAIL #1 + INFO]
      run_uvicorn() -> _port_probe exit_on_occupy=False  [prints FAIL #2]
      run_uvicorn() -> _port_probe again                  [prints FAIL #3]
    """
    import socket
    import os
    import sys
    import subprocess

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        s.bind((host, port))
        s.close()
        print(f"{C.INFO}[port]{C.RESET} {host}:{port} is free")
        return True
    except OSError:
        s.close()

    pids: list[int] = []
    procs_info: list[tuple[int, str, str]] = []
    try:
        if os.name == "nt":
            # ① PowerShell (newer Windows)
            try:
                cmd = (
                    "Get-NetTCPConnection -LocalPort " + str(int(port)) +
                    " -State Listen -ErrorAction SilentlyContinue " +
                    "| Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique " +
                    "| ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue " +
                    "| Select-Object Id,ProcessName,Path } | ConvertTo-Json"
                )
                out = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                    capture_output=True, text=True, timeout=12,
                ).stdout.strip()
                if out and out not in ("null", "[]"):
                    import json as _json
                    data = _json.loads(out)
                    if isinstance(data, dict): data = [data]
                    for d in data:
                        pid = int(d.get("Id") or 0)
                        name = str(d.get("ProcessName") or "")
                        path = str(d.get("Path") or "")
                        if pid and pid not in pids:
                            pids.append(pid)
                            procs_info.append((pid, name, path))
            except Exception:
                pass

            # ② netstat fallback (all Windows versions). Match parts[1] END with :port
            if not procs_info:
                ns = subprocess.run(
                    ["netstat", "-ano", "-p", "tcp"],
                    capture_output=True, text=True, timeout=10,
                ).stdout.splitlines()
                port_str = ":" + str(int(port))
                for line in ns:
                    parts = line.split()
                    if len(parts) < 5: continue
                    if (parts[0].upper() == "TCP" and
                        parts[1].endswith(port_str) and
                        parts[-2].upper() == "LISTENING"):
                        try: pid = int(parts[-1])
                        except ValueError: continue
                        if pid not in pids:
                            pids.append(pid)
                            procs_info.append((pid, "unknown", ""))

            # ③ tasklist fallback (Chinese Windows is rock-solid for name lookup)
            if procs_info and any(n == "unknown" for (_, n, _) in procs_info):
                unknown_pids = [p for (p, n, _) in procs_info if n == "unknown"]
                if unknown_pids:
                    pid_filters = " or ".join(f"PID eq {p}" for p in unknown_pids)
                    try:
                        tl = subprocess.run(
                            ["tasklist", "/FI", pid_filters, "/FO", "CSV", "/NH"],
                            capture_output=True, text=True, timeout=10,
                        ).stdout.splitlines()
                        pid_to_name: dict[int, str] = {}
                        for line in tl:
                            line = line.strip()
                            if not line: continue
                            cols = [c.strip().strip('"') for c in line.split('","')]
                            if len(cols) < 2: continue
                            try: pid_to_name[int(cols[1])] = cols[0]
                            except ValueError: pass
                        procs_info[:] = [
                            (p, pid_to_name.get(p, n), path)
                            for (p, n, path) in procs_info
                        ]
                    except Exception:
                        pass
    except Exception:
        pass

    sep = "=" * 68
    print()
    print(sep)
    print(f"{C.ERR}[PORT OCCUPIED]{C.RESET} {host}:{port} cannot be bound")
    print(sep)
    if procs_info:
        print(f"  owner process(es): {len(procs_info)}")
        for pid, name, path in procs_info:
            if path:
                print(f"    - PID {pid:<7d}  {name:<20s}  {path}")
            else:
                print(f"    - PID {pid:<7d}  {name:<20s}")
        print()
        kill_cmd_cmd = " & ".join(f"taskkill /PID {p} /F" for p in pids)
        kill_cmd_ps = "Stop-Process -Id " + ",".join(str(p) for p in pids) + " -Force"
        print(f"  -> Kill via CMD.exe (copy & paste):")
        print(f"       {kill_cmd_cmd}")
        print(f"  -> Kill via PowerShell:")
        print(f"       {kill_cmd_ps}")
    else:
        print("  owner process: unknown (could not resolve PID)")
        print()
        print(f"  -> Hint: close ALL python.exe processes (use Task Manager)")
    next_port = int(port) + 1
    print()
    print(f"  -> {C.BOLD}RECOMMENDED FIX (copy & run):{C.RESET}")
    print(f"       python {launcher_script} --port {next_port}")
    print(sep)
    print()
    if exit_on_occupy:
        sys.exit(2)
    return False


# ===========================================================================
# 6. 主启动：先本地 port_probe → 再 uvicorn.run (此时 import app.main)
# ===========================================================================
def run_uvicorn(host: str, port: int, reload: bool, workers: int,
                access_log: bool, log_level: str) -> int:
    # Step 1 - RUN.PY LOCAL probe. If port is occupied, exit(2) NOW.
    # (do NOT import app.main here; module-level preflight probe would print FAIL again)
    local_port_probe(host, port, exit_on_occupy=True, launcher_script="run.py")

    # Step 2 - try uvicorn import
    try:
        import uvicorn
    except ImportError as e:
        print(f"{C.ERR}[ERR ]{C.RESET} uvicorn not installed: {e}")
        print("       run:  venv\\Scripts\\pip install uvicorn fastapi")
        return 3

    # Step 3 - uvicorn.run (app.main imported by uvicorn, happens AFTER port-probe success)
    try:
        print(f"{C.OK}[RUN ]{C.RESET} uvicorn[{host}:{port}] "
              f"reload={reload} workers={1 if reload else max(1,int(workers))} "
              f"log_level={log_level} access_log={access_log}")
        uvicorn.run(
            "app.main:app",
            host=host, port=port,
            reload=reload,
            workers=1 if reload else max(1, int(workers)),
            loop="asyncio",
            log_level=log_level,
            access_log=access_log,
        )
        return 0
    except OSError as e:
        is_10048 = (
            getattr(e, "winerror", None) == 10048
            or "10048" in str(e)
            or "address already in use" in str(e).lower()
        )
        if is_10048:
            print()
            print("=" * 68)
            print(f"{C.ERR}[FAIL]{C.RESET} uvicorn caught WinError 10048 "
                  f"on {host}:{port} (port occupied)")
            print("=" * 68)
            from app.main import _port_probe
            _port_probe(host, port, exit_on_occupy=False, launcher_script="run.py")
            print()
            print(f"-> quick fallback:   python run.py --port {int(port) + 1}")
            print("=" * 68)
            return 2
        traceback.print_exc()
        return 4
    except KeyboardInterrupt:
        print(f"\n{C.OK}[EXIT]{C.RESET} Ctrl+C, goodbye.")
        return 0
    except Exception:
        traceback.print_exc()
        return 5


# ===========================================================================
# 7. CLI 入口
# ===========================================================================
def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="python run.py",
        description="Zhixunyun backend one-file launcher (venv friendly, port-aware).",
    )
    ap.add_argument("--host", default="127.0.0.1",
                    help="Bind address, default 127.0.0.1")
    ap.add_argument("--port", type=int, default=8000,
                    help="Bind port, default 8000")
    ap.add_argument("--reload", action="store_true",
                    help="Enable uvicorn reload (Windows may leak port ownership)")
    ap.add_argument("--workers", type=int, default=1,
                    help="Worker count, default 1. Keep 1 on Windows.")
    ap.add_argument("--no-access-log", action="store_true", default=True,
                    dest="no_access_log",
                    help="Disable HTTP access log (default: disabled, clean console)")
    ap.add_argument("--access-log", dest="no_access_log", action="store_false",
                    help="Enable HTTP access log")
    ap.add_argument("--log-level", default="info",
                    choices=["critical", "error", "warning", "info", "debug", "trace"])
    ap.add_argument("--skip-dep-check", action="store_true",
                    help="Skip dependency preflight check")
    ap.add_argument("--db-url", dest="db_url", default=None,
                    help="Override DATABASE_URL from cmdline (e.g. mysql+pymysql://user:pwd@host:3306/dbname?charset=utf8mb4). "
                         "Takes precedence over .env.  ONLY mysql/pg URLs allowed.")
    ap.add_argument("--force-mysql", action="store_true",
                    help="(Historical / no-op; this is now the default behaviour.) "
                         "Project will only connect to MySQL/PostgreSQL and will "
                         "NEVER silently fall back to any local file.  Kept for "
                         "backward compatibility of existing launch scripts.")
    ap.add_argument("--init-mysql", action="store_true",
                    help="Before create_all: connect to MySQL SERVER (no database name) and run "
                         "'CREATE DATABASE IF NOT EXISTS <dbname> DEFAULT CHARACTER SET utf8mb4 "
                         "COLLATE utf8mb4_unicode_ci'. You still need to provide reachable server "
                         "credentials via .env or --db-url.")
    return ap


def main() -> int:
    ap = build_arg_parser()
    args = ap.parse_args()

    # --- Step 1: dependency preflight ----------------------------------------
    if not args.skip_dep_check:
        t0 = time.time()
        ok, missing = dependency_preflight()
        if not ok:
            print(f"\n{C.ERR}[FAIL]{C.RESET} preflight failed after "
                  f"{time.time() - t0:.2f}s. Install missing deps then retry.")
            return 3

    # --- Step 2: venv notice -------------------------------------------------
    in_venv = detect_venv()
    if not in_venv:
        print(f"{C.WARN}[WARN]{C.RESET} current python.exe is not inside a venv/.venv. "
              f"For clean isolation, run first:")
        print(f"       1) python -m venv venv")
        print(f"       2) venv\\Scripts\\activate")
        print(f"       3) pip install -r requirements.txt")

    # --- Step 3: ensure folders ---------------------------------------------
    ensure_dirs()

    # --- Step 4: database bootstrap (MySQL/PostgreSQL ONLY) -----------------
    # NOTE: --skip-db-fallback argument is now a no-op (there is no fallback
    # anyway, project only accepts mysql/pg URLs).  We still accept the flag
    # for backward compat of existing cmdline scripts without failing parsing.
    try:
        db_display = database_bootstrap(
            db_url_override=args.db_url,
            force_mysql=args.force_mysql,
            init_mysql=args.init_mysql,
        )
    except SystemExit:
        # database_bootstrap raised SystemExit after FAIL troubleshooting.
        # Bubble up directly so exit code is preserved.
        raise
    except Exception as exc:
        print(f"{C.ERR}[FAIL]{C.RESET} database bootstrap failed: {exc}")
        return 1

    # --- Step 5: create ALL missing tables BEFORE uvicorn binds -------------
    try:
        database_create_all()
    except Exception as exc:
        print(f"{C.ERR}[FAIL]{C.RESET} database_create_all failed BEFORE server start: {exc}")
        print(f"       Hint: if using MySQL ensure {db_display} is reachable and user has CREATE privilege")
        return 1

    # --- Step 5.5: best-effort ALTER for missing columns -------------------
    # Base.metadata.create_all() never adds new columns onto *existing*
    # tables, so over time our submissions/users/classes tables drift.  Run
    # migrate_cols.upgrade() which adds known columns (step_evidences, meta,
    # extra, etc.) and indexes if missing.  Errors are non-fatal (just warn).
    try:
        from app.models.migrate_cols import upgrade as _upgrade_cols
        from pymysql import connect as _pyconnect
        import os as _os
        from urllib.parse import urlparse as _urlparse, unquote as _unquote
        _db_url = _os.environ.get("DATABASE_URL") or ""
        if _db_url.startswith("mysql"):
            _u = _urlparse(_db_url)
            _conn = _pyconnect(
                host=_u.hostname or "localhost",
                port=_u.port or 3306,
                user=_unquote(_u.username or "") or "root",
                password=_unquote(_u.password or "") if _u.password else "",
                database=(_u.path.lstrip("/") or "eval_system"),
                charset="utf8mb4",
            )
            try:
                _c, _i = _upgrade_cols(_conn, dry_run=False)
                if _c or _i:
                    print(f"{C.OK}[MIG ]{C.RESET} schema sync: +{_c} column(s), +{_i} index(es)")
            finally:
                _conn.close()
    except Exception as _migExc:
        print(f"{C.WARN}[MIG ]{C.RESET} schema sync step skipped (non-fatal): {_migExc}")

    # --- Step 6: banner ------------------------------------------------------
    banner(args.host, args.port, db_display, in_venv)

    # --- Step 7: uvicorn -----------------------------------------------------
    return run_uvicorn(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        access_log=not args.no_access_log,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    sys.exit(main())
