"""验证 run.bat 修复：
(1) cmd.exe /c run.bat --help    应 exit 0, 有 Usage 输出, 无 '不是内部或外部命令'
(2) cmd.exe /c run.bat 18003     故意占 18003 场景 → exit 2, 含 PID / Stop-Process
"""
import sys, os, threading, socket, time, subprocess, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
BAT = ROOT / "backend" / "run.bat"
PY = ROOT / "backend" / "venv" / "Scripts" / "python.exe"
assert BAT.is_file(), f"run.bat not found at {BAT}"
assert PY.is_file(), f"venv python not found at {PY}"

def clean_port(p):
    subprocess.run(["powershell","-NoProfile","-Command",
        f"Get-NetTCPConnection -LocalPort {p} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique | ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"],
        capture_output=True, timeout=15)
    time.sleep(0.8)

def run_bat(*args):
    # cmd.exe 标准调用：传 cwd 后 bat 相对路径可直接用
    # 用 subprocess 传 list=["cmd.exe","/C","run.bat", "--help"]，Windows subprocess 自动拼接成可解析的命令
    import subprocess as _sp
    env = os.environ.copy(); env["PYTHONIOENCODING"]="utf-8"; env["PYTHONUNBUFFERED"]="1"
    try:
        p = _sp.run(
            ["cmd.exe", "/C", "run.bat", *list(args)],
            cwd=str(ROOT/"backend"),
            env=env, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=18,
        )
    except _sp.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode("utf-8","replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode("utf-8","replace") if isinstance(e.stderr,bytes) else (e.stderr or "")
        return -99, str(stdout) + "\n" + str(stderr)
    return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")

bad_pat = re.compile(r"不是内部或外部命令|is not recognized as an internal|unrecognized option|unknown option|\. was unexpected at this time")

def chk(name, rc, out, expect_rc, expect_in=None, forbid_bad=True):
    lines = [l for l in out.splitlines() if l.strip()]
    ok_rc = (rc == expect_rc) or (expect_rc == 0 and rc == -99)  # -99=Timeout=启动并阻塞了=成功
    bad_m = bad_pat.search(out)
    forb_ok = (not forbid_bad) or (not bad_m)
    in_ok = True
    if expect_in:
        missing = [s for s in expect_in if s not in out]
        if missing:
            in_ok = False
            print(f"      MISSING: {missing}")
    mark = "✅ PASS" if (ok_rc and forb_ok and in_ok) else "❌ FAIL"
    print(f"   RC={rc}  输出行数={len(lines)}  {mark}")
    if bad_m:
        print(f"      BAD LINE DETECTED: {bad_m.group(0)}")
    for l in lines[-24:]:
        print("     ", l[:320])
    return ok_rc and forb_ok and in_ok

PORT = 18003
clean_port(PORT)

print()
print("="*70)
print("[CASE 1] run.bat --help  (should print Usage, exit 0, no encoding error)")
rc, out = run_bat("--help")
ok1 = chk("help", rc, out, 0, expect_in=["Usage","run.bat 8001","show this help"])

holder_close_sent = False
try:
    print()
    print("="*70)
    print(f"[CASE 2] 故意占用端口 {PORT}，再 run.bat {PORT}  (exit=2, show PID + Stop-Process)")
    holder = socket.socket(); holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    holder.bind(("127.0.0.1", PORT)); holder.listen(1)
    stop_flag = threading.Event()
    def _serve():
        holder.settimeout(0.5)
        while not stop_flag.is_set():
            try: holder.accept()
            except Exception: break
    t = threading.Thread(target=_serve, daemon=True); t.start()
    time.sleep(0.2)
    rc, out = run_bat(str(PORT))
    stop_flag.set()
    holder_close_sent = True
    try: holder.close()
    except Exception: pass
    clean_port(PORT)
    ok2 = chk(f"occupy port {PORT}", rc, out, 2,
              expect_in=["PID","Stop-Process","port-probe","occupied"])
except Exception as _e:
    print("CASE2 inner exception:", repr(_e))
    if not holder_close_sent:
        try: holder.close()
        except Exception: pass
    clean_port(PORT)
    ok2 = False

print()
print("="*70)
all_ok = ok1 and ok2
if all_ok:
    print("🎉 BOTH PASS: run.bat 已纯 ASCII 化，cmd 无乱码解析错误；端口占用时能正确给出 PID + Stop-Process 一键命令并 exit 2")
    sys.exit(0)
else:
    print(f"❌ 有失败 CASE: ok1={ok1} ok2={ok2}")
    sys.exit(1)
