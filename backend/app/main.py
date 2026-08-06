from fastapi import FastAPI, Request, HTTPException
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


def _port_probe(host: str = "127.0.0.1", port: int = 8000, exit_on_occupy: bool = False,
                launcher_script: str = "run.py") -> bool:
    """Port occupancy probe. ASCII-only output (keeps cmd.exe cp936 happy and
    avoids triggering ``... is not recognized as an internal command`` errors
    from Windows bat files).

    launcher_script: the fallback script name shown in the "change port" hint
    (defaults to "run.py" - the new preferred single-file entry).
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
            # ① 先试 PowerShell Get-NetTCPConnection（最新 Windows）
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

            # ② PowerShell 没拿到 PID 就用 netstat 原生兜底（所有 Windows 都有）
            if not procs_info:
                ns = subprocess.run(
                    ["netstat", "-ano", "-p", "tcp"],
                    capture_output=True, text=True, timeout=10,
                ).stdout.splitlines()
                port_str = ":" + str(int(port))
                for line in ns:
                    parts = line.split()
                    if len(parts) < 5: continue
                    # netstat 输出格式固定为：
                    #   Proto  Local Address      Foreign Address    State        PID
                    #   TCP    127.0.0.1:8000     0.0.0.0:0          LISTENING    39536
                    # parts[1] 为本地地址(127.0.0.1:8000)，精确匹配端口号
                    is_tcp = parts[0].upper() == "TCP"
                    local_addr_match = parts[1].endswith(port_str)
                    is_listening = parts[-2].upper() == "LISTENING"
                    if is_tcp and local_addr_match and is_listening:
                        try: pid = int(parts[-1])
                        except ValueError: continue
                        if pid not in pids:
                            pids.append(pid)
                            procs_info.append((pid, "unknown", ""))

            # ③ netstat 拿到 PID 但进程名 unknown → 用 tasklist 再补一次（中文环境最稳）
            if procs_info and any(name == "unknown" for (_, name, _) in procs_info):
                # 为所有未知 PID 一次性查 tasklist
                unknown_pids = [pid for (pid, name, _) in procs_info if name == "unknown"]
                if unknown_pids:
                    # tasklist /FI "PID eq x" /FO CSV /NH → CSV 输出，列 0=进程名 1=PID
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
                            try:
                                p = int(cols[1])
                                pid_to_name[p] = cols[0]
                            except ValueError:
                                pass
                        procs_info[:] = [
                            (pid, pid_to_name.get(pid, name), path)
                            for (pid, name, path) in procs_info
                        ]
                    except Exception as _ek2:
                        print(f"[port-probe] (tasklist fallback skipped: {_ek2})")
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
            if path:
                print(f"    - PID {pid:<7d}  {name:<20s}  {path}")
            else:
                print(f"    - PID {pid:<7d}  {name:<20s}")
        print()
        # PowerShell kill 命令（需要管理员权限，且中文 PS 环境兼容）
        kill_cmd_ps = "Stop-Process -Id " + ",".join(str(p) for p in pids) + " -Force"
        # CMD 原生 kill 命令（中文环境更稳，不需要管理员，直接复制就能用）
        kill_cmd_cmd = " & ".join(f"taskkill /PID {p} /F" for p in pids)
        print("  -> kill in PowerShell (run once):")
        print(f"       {kill_cmd_ps}")
        print("  -> kill in CMD.exe / Windows Terminal (copy & paste):")
        print(f"       {kill_cmd_cmd}")
    else:
        print("  owner(s): unknown")
        print()
        print("  -> kill hint (brute): Stop-Process -Name python -Force  (closes ALL python.exe)")
    next_port = int(port) + 1
    print()
    print(f"  -> or change port: python {launcher_script} --host {host} --port {next_port}")
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
from app.routers.enterprise_router import student_router as student_interview_router
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
#
# 注意：FastAPI/Starlette 的 @app.exception_handler 会"拦截"响应并绕过 CORSMiddleware，
# 所以这里返回 JSONResponse 时必须 **手动补齐 CORS 头**。否则浏览器看不到
# Access-Control-Allow-Origin，就把真实的 500 错误误报为"CORS 被拦"（你在 DevTools
# 里看到的错误会是 CORS，真正原因反而被完全隐藏）。
def _apply_cors_headers(request: Request, response: JSONResponse) -> JSONResponse:
    origin = request.headers.get("origin") or "*"
    response.headers.setdefault("Access-Control-Allow-Origin", origin)
    response.headers.setdefault("Access-Control-Allow-Credentials", "true")
    response.headers.setdefault(
        "Access-Control-Allow-Methods",
        request.headers.get("access-control-request-method", "GET,POST,PUT,DELETE,PATCH,OPTIONS")
    )
    response.headers.setdefault(
        "Access-Control-Allow-Headers",
        request.headers.get("access-control-request-headers",
                            "Authorization,Content-Type,Accept,X-Requested-With")
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = traceback.format_exc()
    print(f"[ERROR] {request.method} {request.url}")
    print(error_detail)

    resp = JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误，请联系管理员",
            "detail": str(exc) if app.debug else ""
        }
    )
    return _apply_cors_headers(request, resp)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # HTTPException 也走同一个 CORS 补齐逻辑，避免 401/403/404 时浏览器被误报成 CORS
    # 同时返回 detail 和 error 字段，兼容前端不同版本的读取方式
    resp = JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "detail": exc.detail,
            "error": exc.detail
        }
    )
    return _apply_cors_headers(request, resp)

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
app.include_router(student_interview_router)
app.include_router(job_match_router)

# ---- 静态文件：uploads 目录 ----
# 1) 以 backend/ 为基准解析绝对路径，避免"从哪个目录启动 python"导致找不到
# 2) 启动时 mkdir 保证目录存在，避免首次上传 500
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_UPLOADS_DIR = os.path.join(_BACKEND_ROOT, "uploads")
os.makedirs(_UPLOADS_DIR, exist_ok=True)

if os.path.isdir(_UPLOADS_DIR):
    app.mount("/uploads", StaticFiles(directory=_UPLOADS_DIR), name="uploads")
else:
    # 兜底：相对路径（老逻辑）
    try:
        os.makedirs("uploads", exist_ok=True)
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    except Exception:
        pass

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
        _port_probe(_h, _p, exit_on_occupy=False, launcher_script="run.py")
        print(
            f"[port-probe] INFO uvicorn will bind {_h}:{_p} next; "
            f"if WinError 10048 appears, kill PID(s) listed above or use: "
            f"python run.py --port {int(_p) + 1}"
        )
