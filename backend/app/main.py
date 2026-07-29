from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import traceback

# ============================================================
#  端口占用探测（启动前主动检查，避免 Windows --reload 假在线陷阱）
#  用法：
#    命令行直接探测：python -c "from app.main import _port_probe; _port_probe('127.0.0.1',8000,exit_on_occupy=True)"
#    uvicorn 启动时自动探测：在 uvicorn.run() 前调用一次即可
# ============================================================
import socket
import sys
import os
import subprocess


def _port_probe(host: str = "127.0.0.1", port: int = 8000, exit_on_occupy: bool = False) -> bool:
    """Port occupancy probe. ASCII-only output (keeps cmd.exe cp936 happy and
    avoids triggering ``... is not recognized as an internal command`` errors
    from Windows bat files).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        s.bind((host, port))
        s.close()
        print(f"[port-probe] OK {host}:{port} is free")
        return True
    except OSError:
        s.close()

    # --- occupied, find owner pid / process name ---
    pids: list[int] = []
    procs_info: list[tuple[int, str, str]] = []
    try:
        if os.name == "nt":
            cmd = (
                "Get-NetTCPConnection -LocalPort " + str(int(port)) +
                " -State Listen -ErrorAction SilentlyContinue " +
                "| Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique " +
                "| ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue " +
                "| Select-Object Id,ProcessName,Path } | ConvertTo-Json"
            )
            out = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                capture_output=True, text=True, timeout=15,
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
            if not procs_info:
                ns = subprocess.run(
                    ["netstat", "-ano", "-p", "tcp"],
                    capture_output=True, text=True, timeout=10,
                ).stdout.splitlines()
                target = ":" + str(int(port)) + " "
                for line in ns:
                    parts = line.split()
                    if len(parts) < 5: continue
                    if parts[0].upper() == "TCP" and target in parts[1] and parts[-2].upper() == "LISTENING":
                        try: pid = int(parts[-1])
                        except ValueError: continue
                        if pid not in pids:
                            pids.append(pid)
                            procs_info.append((pid, "unknown", ""))
    except Exception as ek:
        print(f"[port-probe] (owner lookup skipped: {ek})")

    bar = "=" * 68
    print()
    print(bar)
    print(f"[port-probe] FAIL {host}:{port} occupied")
    print(bar)
    if procs_info:
        print(f"  owner(s): {len(procs_info)}")
        for pid, name, path in procs_info:
            print(f"    - PID {pid:<7d}  {name:<20s}  {path}")
        print()
        kill_cmd = "Stop-Process -Id " + ",".join(str(p) for p in pids) + " -Force"
        print("  -> kill in PowerShell (run once):")
        print(f"       {kill_cmd}")
    else:
        print("  owner(s): unknown")
    next_port = int(port) + 1
    print()
    print(f"  -> or change port: python serve.py --host {host} --port {next_port}")
    print(bar)
    print()
    if exit_on_occupy:
        sys.exit(2)
    return False


from app.models.database import SessionLocal
from app.routers.evaluate import router as evaluate_router
from app.routers.upload import router as upload_router
from app.routers.upload_eval import router as upload_eval_router
from app.routers.report import router as report_router
from app.routers.auth_router import router as auth_router_router
from app.routers.teacher_score import router as teacher_router
from app.routers.criteria import router as criteria_router
from app.routers.statistics import router as stats_router
from app.routers.class_router import router as class_router
from app.routers.user_profile import router as profile_router
from app.routers.task_manage import router as task_manage_router
from app.routers.notifications import router as notif_router
from app.utils.ai_evaluator import is_ai_configured
from app.routers.search import router as search_router
from app.routers.enterprise_router import router as enterprise_router
from app.routers.job_match_router import router as job_match_router

app = FastAPI(
    title="实训教学评价系统",
    description="基于大模型技术的软件实训教学结果检查评价与报表系统",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = traceback.format_exc()
    print(f"[ERROR] {request.method} {request.url}")
    print(error_detail)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误，请联系管理员",
            "detail": str(exc) if app.debug else ""
        }
    )

app.include_router(evaluate_router)
app.include_router(upload_router)
app.include_router(upload_eval_router)
app.include_router(report_router)
app.include_router(auth_router_router)
app.include_router(teacher_router)
app.include_router(criteria_router)
app.include_router(stats_router)
app.include_router(class_router)
app.include_router(profile_router)
app.include_router(task_manage_router)
app.include_router(notif_router)
app.include_router(search_router)
app.include_router(enterprise_router)
app.include_router(job_match_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def hello():
    return {"message": "实训评价系统启动成功！"}

@app.get("/api/health")
def health_check():
    db_ok = False
    db_error = ""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception as e:
        db_error = str(e)

    return {
        "status": "ok" if db_ok and is_ai_configured() else "degraded",
        "database": "connected" if db_ok else f"disconnected: {db_error}",
        "ai_configured": is_ai_configured(),
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/test")
def test():
    return {"message": "前后端联通成功！", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # 直接 python app/main.py 启动时，也先做端口探测
    _port_probe("127.0.0.1", 8000, exit_on_occupy=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, workers=1)


# ============================================================
#  模块导入期端口预检测（解决你直接跑 `uvicorn app.main:app` 时跳过 __main__ 的问题）
#  原理：
#    当执行 uvicorn app.main:app 时，uvicorn 会 `import app.main`，模块级代码都会跑。
#    所以我们在模块最末尾：解析 uvicorn 的 CLI args → 拿到 host/port → 先做一次 _port_probe。
#    这样即便你不写 serve.py、不双击 run.bat、直接手打 uvicorn 命令，
#    也能在 uvicorn 自己 bind 之前先告诉你"谁占了端口 + 怎么杀"。
# ============================================================
import argparse as _argparse


def _guess_uvicorn_host_port(argv=None) -> tuple[str, int] | None:
    """从 sys.argv / uvicorn.config 里推断 (host, port)。

    uvicorn app.main:app --host 0.0.0.0 --port 8000 这种命令，
    启动时会先 import app.main，此时 sys.argv 里的 --host/--port 还在，
    我们自己构造一个最小 ArgumentParser 偷偷解析一次即可。
    """
    try:
        ap = _argparse.ArgumentParser(add_help=False)
        ap.add_argument("--host", default="127.0.0.1")
        ap.add_argument("--port", type=int, default=8000)
        ap.add_argument("--fd", type=int, default=None)
        ap.add_argument("--uds", default=None)
        ns, _unknown = ap.parse_known_args(argv)
        # uvicorn 多 worker 场景下子进程会带 --fd，这时不需要我们探测（父进程已经 bind 了）
        if ns.fd is not None or ns.uds is not None:
            return None
        return str(ns.host), int(ns.port)
    except Exception:
        return None


# Only run preflight probe when uvicorn imports us (hand-run `uvicorn app.main:app`).
# When we ARE __main__ the user runs `python app/main.py` which already probes first.
if __name__ != "__main__":
    _hp = _guess_uvicorn_host_port()
    if _hp:
        _h, _p = _hp
        # Print-only, do NOT sys.exit() here - uvicorn's normal flow must remain unbroken.
        _port_probe(_h, _p, exit_on_occupy=False)
        print(
            f"[port-probe] INFO uvicorn will bind {_h}:{_p} next; "
            f"if WinError 10048 appears, kill PID(s) listed above or use: "
            f"python serve.py --port {int(_p) + 1}"
        )
