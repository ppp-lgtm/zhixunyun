"""
阶段 A2 验证脚本（极简版，规避缺失的 fitz/python-docx 等依赖）：
 - 不 import app.main，只单独挂载 enterprise + auth_router 到一个最小 FastAPI 实例
 - 数据库用临时 SQLite，不碰生产
"""
import sys, os, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Mock pymysql 让 models 导入成功
from types import ModuleType
_pymysql_mock = ModuleType("pymysql")
_pymysql_mock.paramstyle = "pyformat"
_pymysql_mock.threadsafety = 2
sys.modules.setdefault("pymysql", _pymysql_mock)
sys.modules.setdefault("MySQLdb", _pymysql_mock)
sys.modules["pymysql.cursors"] = ModuleType("pymysql.cursors")

# 2. 切换到 SQLite 临时库
from app.models import database as _dbmod
_tmpdb = tempfile.mktemp(suffix=".db")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
_engine = create_engine(f"sqlite:///{_tmpdb}", connect_args={"check_same_thread": False})
_dbmod.engine = _engine
_dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

from app.models.database import Base
import app.models.tables
import app.models.class_models
import app.models.enterprise_models

Base.metadata.create_all(bind=_engine)
print("✅ SQLite 临时库建表 OK")

# 3. 构造一个"最小 FastAPI 应用"，只挂载 2 个路由（避免其它缺依赖模块）
from fastapi import FastAPI
from app.routers.enterprise_router import router as enterprise_router
from app.routers.auth_router import router as auth_router
from fastapi.testclient import TestClient

app = FastAPI()
app.include_router(enterprise_router)
app.include_router(auth_router)
client = TestClient(app)

SEP = "=" * 60
print()
print(SEP)
print("阶段 A2 验证：企业端基础 API（TestClient，SQLite）")
print(SEP)


def _ok(title, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {title:40s} {detail}")
    return cond


token = None
uid = None
eid = None
job_id = None

# 1) 企业注册
try:
    r = client.post("/api/enterprise/register", json={
        "username": "longke", "password": "123456",
        "real_name": "李导师", "title": "技术总监",
        "enterprise_name": "龙科软件（测试）",
        "enterprise_short_name": "龙科",
        "industry": "软件与信息技术服务", "scale": "200-1000",
        "contact_phone": "13800138000", "contact_email": "hr@longke.test",
        "address": "北京市海淀区中关村大街1号",
        "description": "专注 AI 与数字化转型",
    })
    ok = r.status_code == 200 and r.json().get("success")
    _ok("POST /api/enterprise/register   企业注册",
        ok,
        f"status={r.status_code} msg={r.json().get('message', r.text[:50]) if r.content else ''}")
    if ok:
        uid = r.json()["user_id"]; eid = r.json()["enterprise_id"]
        print(f"        └─ user_id={uid} eid={eid} is_admin={r.json()['is_admin']}")
except Exception as e:
    _ok("POST /api/enterprise/register   企业注册", False, str(e))

# 2) 学生走企业登录被拒
try:
    client.post("/api/auth/register", json={"username": "stu1", "password": "111111", "role": "student"})
    r = client.post("/api/enterprise/login", json={"username": "stu1", "password": "111111"})
    _ok("POST /api/enterprise/login（学生） 拒绝非企业", r.status_code != 200, f"status={r.status_code}")
except Exception as e:
    _ok("POST /api/enterprise/login（学生） 拒绝非企业", False, str(e))

# 3) 企业导师登录
try:
    r = client.post("/api/enterprise/login", json={"username": "longke", "password": "123456"})
    ok = r.status_code == 200 and r.json().get("success")
    _ok("POST /api/enterprise/login      企业导师登录", ok, f"status={r.status_code}")
    if ok:
        token = r.json()["token"]
        print(f"        └─ enterprise={r.json().get('enterprise')}")
except Exception as e:
    _ok("POST /api/enterprise/login      企业导师登录", False, str(e))

# 4) Profile
try:
    r = client.get("/api/enterprise/profile", params={"token": token})
    ok = r.status_code == 200 and r.json().get("success")
    _ok("GET  /api/enterprise/profile    Profile",
        ok,
        f"status={r.status_code}" if not ok else f"stats={r.json()['stats']}")
except Exception as e:
    _ok("GET  /api/enterprise/profile    Profile", False, str(e))

# 5) 创建岗位
try:
    r = client.post("/api/enterprise/jobs", params={"token": token}, json={
        "title": "前端开发（Vue3）",
        "job_type": "技术岗", "level": "初级",
        "salary_range": "10k-15k", "city": "北京",
        "description": "负责 SaaS 前端开发",
        "requirements": "Vue3/TS/Tailwind/HTTP",
        "responsibilities": "开发/bug修复/CR",
        "skill_requirements": [
            {"name": "前端框架-Vue", "weight": 1.5, "threshold": 75},
            {"name": "文档规范",     "weight": 1.0, "threshold": 60},
            {"name": "代码规范性",   "weight": 1.2, "threshold": 70},
            {"name": "算法与数据结构","weight": 0.8, "threshold": 50},
            {"name": "需求理解",     "weight": 1.0, "threshold": 60},
        ],
        "tags": "Vue3,TypeScript,Tailwind",
        "status": "open",
    })
    ok = r.status_code == 200 and r.json().get("success")
    _ok("POST /api/enterprise/jobs       创建岗位",
        ok,
        f"status={r.status_code} msg={r.json().get('message', r.text[:50]) if r.content else ''}")
    if ok:
        job_id = r.json()["job_id"]; print(f"        └─ job_id={job_id}")
except Exception as e:
    _ok("POST /api/enterprise/jobs       创建岗位", False, str(e))

# 6) 岗位列表
try:
    r = client.get("/api/enterprise/jobs", params={"token": token})
    ok = r.status_code == 200 and r.json().get("success")
    _ok("GET  /api/enterprise/jobs       岗位列表",
        ok,
        f"status={r.status_code} total={r.json().get('total') if ok else 'N/A'}")
except Exception as e:
    _ok("GET  /api/enterprise/jobs       岗位列表", False, str(e))

# 7) 岗位详情
try:
    if job_id is None:
        _ok("GET  /api/enterprise/jobs/{id}  岗位详情", False, "缺 job_id")
    else:
        r = client.get(f"/api/enterprise/jobs/{job_id}", params={"token": token})
        ok = r.status_code == 200 and r.json().get("success")
        data = r.json()["data"] if ok else {}
        _ok("GET  /api/enterprise/jobs/{id}  岗位详情",
            ok,
            f"维度数={len(data.get('skill_requirements', []))}" if ok else r.text[:40])
        if ok and data.get("skill_requirements"):
            print(f"        └─ skill[0]={data['skill_requirements'][0]}")
except Exception as e:
    _ok("GET  /api/enterprise/jobs/{id}  岗位详情", False, str(e))

# 8) 更新岗位
try:
    if job_id is None:
        _ok("PUT  /api/enterprise/jobs/{id}  更新岗位", False, "缺 job_id")
    else:
        r = client.put(f"/api/enterprise/jobs/{job_id}", params={"token": token},
                       json={"title": "前端（Vue3+TS）", "city": "上海"})
        ok = r.status_code == 200 and r.json().get("success")
        _ok("PUT  /api/enterprise/jobs/{id}  更新岗位",
            ok, f"status={r.status_code} msg={r.json().get('message', r.text[:30]) if r.content else ''}")
except Exception as e:
    _ok("PUT  /api/enterprise/jobs/{id}  更新岗位", False, str(e))

# 9) 删除岗位
try:
    if job_id is None:
        _ok("DEL  /api/enterprise/jobs/{id}  删除岗位", False, "缺 job_id")
    else:
        r = client.delete(f"/api/enterprise/jobs/{job_id}", params={"token": token})
        ok = r.status_code == 200 and r.json().get("success")
        _ok("DEL  /api/enterprise/jobs/{id}  删除岗位", ok, f"status={r.status_code}")
except Exception as e:
    _ok("DEL  /api/enterprise/jobs/{id}  删除岗位", False, str(e))

# 10) 岗位下拉 / 班级下拉
try:
    r = client.get("/api/enterprise/jobs/all", params={"token": token})
    ok = r.status_code == 200 and r.json().get("success")
    _ok("GET  /api/enterprise/jobs/all   岗位下拉",
        ok, f"count={len(r.json()['list']) if ok else 0}")
except Exception as e:
    _ok("GET  /api/enterprise/jobs/all   岗位下拉", False, str(e))

try:
    r = client.get("/api/enterprise/linked-classes/options", params={"token": token})
    ok = r.status_code == 200 and r.json().get("success")
    _ok("GET  /api/enterprise/linked-cls 班级下拉",
        ok, f"count={len(r.json()['list']) if ok else 0}")
except Exception as e:
    _ok("GET  /api/enterprise/linked-cls 班级下拉", False, str(e))

# 11) 无 Token 访问被拒绝
try:
    r = client.get("/api/enterprise/profile")
    ok = r.status_code in (422, 401, 403)
    _ok("GET  /api/enterprise/profile 无Token 应被拒绝",
        ok, f"status={r.status_code}")
except Exception as e:
    _ok("GET  /api/enterprise/profile 无Token 应被拒绝", False, str(e))


print()
print(SEP)
print("🎉 阶段 A2 验证结束（全部✅ = 通过）")
print(SEP)
print()
print("真实 MySQL 环境验证可在本地启动后端后手动执行 curl：")
print("  $ python uvicorn app.main:app --reload")
print("  $ curl -X POST http://127.0.0.1:8000/api/enterprise/register -H 'content-type: application/json' -d '{...}'")
print()
print("后续阶段可任选其一：")
print("  → B1：岗位匹配算法（纯逻辑，独立）")
print("  → A3：企业评价 API + 三方对比 GET /compare")

try: os.unlink(_tmpdb)
except: pass
