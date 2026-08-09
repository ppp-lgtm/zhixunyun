"""
Zhixunyun Backend Unified Entry (Windows friendly)
==================================================
Reasons for existence:
  * cmd.exe defaults to cp936/GBK; UTF-8 Chinese + emoji in bat files triggers
    '... is not recognized as an internal or external command'.
  * This file stays pure ASCII + English output.
  * 3-level protection before uvicorn.bind:
      1) Pre-flight port probe (_port_probe from app.main)
      2) uvicorn.run inside try/except
      3) On WinError 10048, prints occupier PID + PowerShell command again.

Usage:
  # Production / Defense presentation (recommended)
  python serve.py
  python serve.py --host 127.0.0.1 --port 8000

  # Local dev (reload. WARNING Windows reload can leak port ownership)
  python serve.py --reload
"""
from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="serve.py",
        description="Zhixunyun backend launcher. Port-occupancy aware, WinError 10048 safe.",
    )
    ap.add_argument("--host", default="127.0.0.1",
                    help="Bind address, default 127.0.0.1")
    ap.add_argument("--port", type=int, default=8000,
                    help="Bind port, default 8000")
    ap.add_argument("--reload", action="store_true",
                    help="Enable uvicorn reload (Windows port-leak prone)")
    ap.add_argument("--workers", type=int, default=1,
                    help="Worker count, default 1. Keep 1 on Windows.")
    ap.add_argument("--no-access-log", action="store_true", default=True,
                    help="Disable access log (default ON for clean presentation)")
    ap.add_argument("--access-log", dest="no_access_log", action="store_false",
                    help="Enable access log")
    ap.add_argument("--log-level", default="info",
                    choices=["critical","error","warning","info","debug","trace"])
    args = ap.parse_args()

    # Layer 1 - Port probe before anything else.
    from app.main import _port_probe
    if not _port_probe(args.host, args.port, exit_on_occupy=False):
        # Print once more then exit(2) so bat can branch on this
        _port_probe(args.host, args.port, exit_on_occupy=False)
        return 2

    # Layer 2 - uvicorn.run
    try:
        import uvicorn
    except ImportError as e:
        print("[ERR] uvicorn not installed:", e)
        print("      Please run: venv\\Scripts\\pip install uvicorn fastapi")
        return 3

    try:
        print(f"[serve.py] OK start uvicorn[{args.host}:{args.port}] "
              f"reload={args.reload} workers={1 if args.reload else max(1,int(args.workers))} "
              f"log_level={args.log_level}")
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=1 if args.reload else max(1, int(args.workers)),
            loop="asyncio",
            log_level=args.log_level,
            access_log=not args.no_access_log,
        )
        return 0
    except OSError as e:
        # Layer 3 - uvicorn.bind failed. Catch WinError 10048 exactly.
        is_10048 = (
            getattr(e, "winerror", None) == 10048
            or "10048" in str(e)
            or "address already in use" in str(e).lower()
        )
        if is_10048:
            print()
            print("="*68)
            print(f"[serve.py] FAIL uvicorn caught WinError 10048: "
                  f"port {args.host}:{args.port} occupied")
            print("="*68)
            _port_probe(args.host, args.port, exit_on_occupy=False)
            print()
            print(f"-> Easy fallback:    python serve.py --port {int(args.port)+1}")
            print("="*68)
            return 2
        traceback.print_exc()
        return 4
    except KeyboardInterrupt:
        print("\n[serve.py] Ctrl+C exit.")
        return 0
    except Exception:
        traceback.print_exc()
        return 5


if __name__ == "__main__":
    sys.exit(main())

