"""A3 自测试脚本：企业评价 / 三方对比 / 学生浏览接口。

运行方式（在 backend/ 目录执行）：
    cd backend && python _verify_a3.py
不需要真实 MySQL，使用内存 SQLite。
"""
from __future__ import annotations

import os
import sys

# 把 backend/ 加到 sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# 用文件型 SQLite（:memory: 在多线程下每个连接都是新的空库，FastAPI TestClient 会多线程访问
# 导致 "no such table"；改成同一个磁盘文件 + check_same_thread=False 即可复用同一个 DB）
_TEST_DB_PATH = os.path.join(_HERE, "__tmp_a3_test.db")
if os.path.exists(_TEST_DB_PATH):
    try:
        os.remove(_TEST_DB_PATH)
    except Exception:
        pass
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"

from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_engine = create_engine(
    f"sqlite:///{_TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(_engine, "connect")
def _on_conn(dbapi_conn, rec):
    try:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass


_TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

# 先把 Base 注册表加载好（tables / class_models / enterprise_models）
import app.models.tables  # noqa: E402,F401
import app.models.class_models  # noqa: E402,F401
import app.models.enterprise_models  # noqa: E402,F401
from app.models.database import Base  # noqa: E402
import app.models.database as _db_mod  # noqa: E402

# 彻底替换：所有模块里使用的 SessionLocal / engine 都挂到我们的测试 DB
_db_mod.engine = _engine
_db_mod.SessionLocal = _TestingSessionLocal

# 建表
Base.metadata.create_all(bind=_engine)
_tables = sorted(Base.metadata.tables.keys())
print(f"[verify_a3] 已创建表: {_tables}")
assert "users" in _tables
assert "enterprise_evaluations" in _tables

# 再 import main —— 这里 main 会把 SessionLocal 做顶层 import
from app.main import app  # noqa: E402
import app.main as _main_mod  # noqa: E402
_main_mod.SessionLocal = _TestingSessionLocal

# 给每个 router 里定义的 get_db 函数对象都挂上同一个 override 工厂
from collections.abc import Generator as _Gen  # noqa: E402


def _override_session_factory() -> _Gen:
    sess = _TestingSessionLocal()
    try:
        yield sess
    finally:
        sess.close()


import sys as _sys  # noqa: E402
_ov_count = 0
for _mname, _mod in list(_sys.modules.items()):
    if not (_mname.startswith("app.routers") or _mname == "app.models.database"):
        continue
    _g = getattr(_mod, "get_db", None)
    if callable(_g):
        app.dependency_overrides[_g] = _override_session_factory
        _ov_count += 1
print(f"[verify_a3] override 挂在 {_ov_count} 个不同的 get_db 函数对象上")

client = TestClient(app)


# ------------------ 模型类 ------------------
from app.models.tables import (  # noqa: E402
    User,
    Task,
    Submission,
    Evaluation,
)
from app.models.class_models import Class, ClassMember  # noqa: E402
from app.models.enterprise_models import (  # noqa: E402
    Enterprise,
    EnterpriseMentor,
    JobPosition,
    EnterpriseEvaluation,
)
from app.utils.auth import create_token, hash_password  # noqa: E402


def seed():
    db = _TestingSessionLocal()
    try:
        teacher = User(username="t1", password_hash=hash_password("p"), role="teacher", real_name="王老师")
        s1 = User(username="stu1", password_hash=hash_password("p"), role="student", real_name="张三", user_number="20240001")
        s2 = User(username="stu2", password_hash=hash_password("p"), role="student", real_name="李四", user_number="20240002")
        ent_user = User(username="ent1", password_hash=hash_password("p"), role="enterprise", real_name="李导师")
        ent_admin = User(username="ent_admin", password_hash=hash_password("p"), role="enterprise", real_name="企业管理员")
        db.add_all([teacher, s1, s2, ent_user, ent_admin])
        db.flush()
        t_id, s1_id, s2_id, eu_id, ea_id = teacher.id, s1.id, s2.id, ent_user.id, ent_admin.id

        ent = Enterprise(name="智讯云科技", contact_phone="13800000000", description="实训合作企业")
        db.add(ent)
        db.flush()
        ent_id = ent.id

        cls = Class(name="软件工程实训班", teacher_id=t_id, enterprise_id=ent_id,
                    invite_code="INV001", teacher_name="王老师")
        db.add(cls)
        db.flush()
        cls_id = cls.id

        for stu_id, sname, snum in [(s1_id, "张三", "20240001"), (s2_id, "李四", "20240002")]:
            db.add(ClassMember(
                class_id=cls_id, student_id=stu_id, student_name=sname, student_number=snum,
            ))

        db.add(EnterpriseMentor(enterprise_id=ent_id, user_id=ea_id, title="企业管理员", is_admin=1, real_name="企业管理员"))
        db.add(EnterpriseMentor(enterprise_id=ent_id, user_id=eu_id, title="前端技术导师", is_admin=0, real_name="李导师"))
        db.flush()

        jp = JobPosition(
            enterprise_id=ent_id,
            title="前端开发工程师",
            description="React/Vue 开发",
            skill_requirements=["HTML", "CSS", "TypeScript"],
            status="open",
            linked_classes=str(cls_id),
            created_by=ea_id,
        )
        db.add(jp)
        db.flush()
        jp_id = jp.id

        task = Task(
            title="企业实习任务",
            requirements="根据岗位要求完成项目",
            class_id=str(cls_id),
            created_by=t_id,
            status="published",
        )
        db.add(task)
        db.flush()
        task_id = task.id

        sub1 = Submission(task_id=task_id, student_id=s1_id, content="实习报告内容A",
                          class_id=str(cls_id), filename="report_a.docx")
        sub2 = Submission(task_id=task_id, student_id=s2_id, content="实习报告内容B",
                          class_id=str(cls_id), filename="report_b.docx")
        sub3 = Submission(task_id=task_id, student_id=s1_id, content="实习报告内容C 没被评价",
                          class_id=str(cls_id), filename="report_c.docx")
        db.add_all([sub1, sub2, sub3])
        db.flush()
        sub1_id, sub2_id, sub3_id = sub1.id, sub2.id, sub3.id

        db.add(Evaluation(submission_id=sub1_id, evaluator_type="ai", total_score=85, comment="AI 评价：整体不错",
                          dimension_scores=[
                              {"name": "代码质量", "score": 88, "reason": ""},
                              {"name": "文档规范性", "score": 82, "reason": ""},
                          ]))
        db.add(Evaluation(submission_id=sub2_id, evaluator_type="ai", total_score=70, comment="AI 评价：需要改进"))
        db.add(Evaluation(submission_id=sub1_id, evaluator_type="teacher", total_score=82, comment="教师评价：有进步"))
        db.commit()
        return {
            "teacher": {"id": t_id},
            "s1": {"id": s1_id},
            "s2": {"id": s2_id},
            "ent_user": {"id": eu_id},
            "ent_admin": {"id": ea_id},
            "ent": {"id": ent_id},
            "jp": {"id": jp_id},
            "task": {"id": task_id},
            "cls": {"id": cls_id},
            "sub1": {"id": sub1_id},
            "sub2": {"id": sub2_id},
            "sub3": {"id": sub3_id},
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DATA = seed()
T_MENTOR = create_token(user_id=DATA["ent_user"]["id"], role="enterprise")
T_ADMIN = create_token(user_id=DATA["ent_admin"]["id"], role="enterprise")
T_S1 = create_token(user_id=DATA["s1"]["id"], role="student")
T_S2 = create_token(user_id=DATA["s2"]["id"], role="student")
T_TEACHER = create_token(user_id=DATA["teacher"]["id"], role="teacher")


passed = 0
total_count = 0


def tc(cond, msg):
    global passed, total_count
    total_count += 1
    if cond:
        passed += 1
        print(f"  OK  {msg}")
    else:
        raise AssertionError(f"FAIL[{total_count}]: {msg}")


# =================== 用例 1：未登录访问 ===================
print("\n[TC 1] 未登录访问")
r = client.get("/api/enterprise/evaluations/submissions")
tc(r.status_code == 422, f"无 token 返回 422 (实际 {r.status_code})")
r = client.get("/api/enterprise/evaluations/submissions?token=invalid")
tc(r.status_code == 401, f"无效 token 返回 401 (实际 {r.status_code})")

# =================== 用例 2：非企业角色被拒 ===================
print("\n[TC 2] 非企业角色访问受限接口")
r = client.get(f"/api/enterprise/evaluations/submissions?token={T_S1}")
tc(r.status_code == 403, f"学生访问待评价列表 403 (实际 {r.status_code})")
r = client.get(f"/api/enterprise/evaluations/submissions?token={T_TEACHER}")
tc(r.status_code == 403, f"老师访问待评价列表 403 (实际 {r.status_code})")

# =================== 用例 3：待评价列表 ===================
print("\n[TC 3] 企业查看待评价列表")
r = client.get(f"/api/enterprise/evaluations/submissions?token={T_MENTOR}")
tc(r.status_code == 200, f"待评价列表 200 (实际 {r.status_code})")
js = r.json()
tc("list" in js and "total" in js, "返回 list+total 字段")
tc(js["total"] >= 2, f"至少有 2 条提交可评价 (实际 {js['total']})")
if js["list"]:
    keys = set(js["list"][0].keys())
    for k in ["submission_id", "submitted_at", "filename"]:
        tc(k in keys, f"待评价列表包含 {k}")

# =================== 用例 4：获取提交详情 ===================
print("\n[TC 4] 企业查看提交详情")
sub1_id = DATA["sub1"]["id"]
r = client.get(f"/api/enterprise/evaluations/submissions/{sub1_id}?token={T_MENTOR}")
tc(r.status_code == 200, f"获取详情 200 (实际 {r.status_code})")
d = r.json()["data"]
tc(d.get("content") == "实习报告内容A", "详情内容正确")
tc("evaluations" in d, "详情包含 evaluations 列表")
ai_count = sum(1 for e in d["evaluations"] if e["evaluator_type"] == "ai")
tc(ai_count >= 1, f"至少 1 条 AI 评价 ({ai_count})")
t_count = sum(1 for e in d["evaluations"] if e["evaluator_type"] == "teacher")
tc(t_count >= 1, f"至少 1 条教师评价 ({t_count})")
tc(d.get("enterprise_evaluation") is None, "评价前企业评价为空")
tc("available_jobs" in d, "详情包含可选岗位")

r = client.get(f"/api/enterprise/evaluations/submissions/99999999?token={T_MENTOR}")
tc(r.status_code == 404, f"不存在的提交详情 404 (实际 {r.status_code})")

# =================== 用例 5：提交企业评价 ===================
print("\n[TC 5] 提交企业评价")
body = {
    "submission_id": sub1_id,
    "dimension_scores": [
        {"name": "专业基础", "score": 92, "reason": "扎实"},
        {"name": "工程能力", "score": 88, "reason": "能写"},
    ],
    "job_fit_score": 90,
    "strength_points": "基础好，沟通强",
    "improvement_points": "工程经验不足",
    "interview_suggest": "recommend",
    "comment": "企业评价：思路清晰，基本功扎实",
    "matched_job_id": DATA["jp"]["id"],
}
r = client.post("/api/enterprise/evaluations", params={"token": T_MENTOR}, json=body)
tc(r.status_code == 200, f"提交企业评价 200 (实际 {r.status_code}): {r.text[:120]}")
ee_id = r.json()["evaluation_id"]
tc(isinstance(ee_id, int) and ee_id > 0, f"返回 evaluation_id={ee_id}")
tc(r.json().get("total_score") is not None, "返回 total_score")

# 重复提交
r2 = client.post("/api/enterprise/evaluations", params={"token": T_MENTOR}, json=body)
tc(r2.status_code == 409, f"重复提交 409 (实际 {r2.status_code})")

# 非法分数
bad = dict(body)
bad["submission_id"] = DATA["sub2"]["id"]
bad["dimension_scores"] = [{"name": "x", "score": 150, "reason": ""}]
r3 = client.post("/api/enterprise/evaluations", params={"token": T_MENTOR}, json=bad)
tc(r3.status_code == 422, f"越界分数 422 (实际 {r3.status_code})")

# 空 comment 允许
ok2 = dict(body)
ok2["submission_id"] = DATA["sub2"]["id"]
ok2["dimension_scores"] = [{"name": "专业基础", "score": 78}]
ok2["comment"] = ""
r4 = client.post("/api/enterprise/evaluations", params={"token": T_MENTOR}, json=ok2)
tc(r4.status_code == 200, f"空 comment 允许 200 (实际 {r4.status_code})")

# 不存在的提交
bad2 = dict(body)
bad2["submission_id"] = 999999
r5 = client.post("/api/enterprise/evaluations", params={"token": T_MENTOR}, json=bad2)
tc(r5.status_code == 404, f"对不存在的提交评价 404 (实际 {r5.status_code})")

# =================== 用例 6：评价详情 / 修改 ===================
print("\n[TC 6] 企业查看 & 修改评价详情")
r = client.get(f"/api/enterprise/evaluations/{ee_id}?token={T_MENTOR}")
tc(r.status_code == 200, f"评价详情 200 (实际 {r.status_code})")
d = r.json()["data"]
tc(d["id"] == ee_id, "详情 id 正确")
tc(d.get("total_score") is not None, "详情 total_score 有值")
tc(d["matched_job"] and d["matched_job"]["id"] == DATA["jp"]["id"], "详情包含匹配岗位")

r = client.put(
    f"/api/enterprise/evaluations/{ee_id}",
    params={"token": T_MENTOR},
    json={
        "dimension_scores": [{"name": "专业基础", "score": 95}, {"name": "工程能力", "score": 91}],
        "job_fit_score": 94,
        "strength_points": "优秀",
        "improvement_points": "",
        "interview_suggest": "recommend",
        "comment": "修改后的企业评价",
    },
)
tc(r.status_code == 200, f"修改 200 (实际 {r.status_code})")

r = client.get(f"/api/enterprise/evaluations/{ee_id}?token={T_MENTOR}")
tc(r.json()["data"]["comment"] == "修改后的企业评价", "修改后 comment 同步")
tc(abs(r.json()["data"]["job_fit_score"] - 94) < 1e-6, "修改后 job_fit_score 正确")

# 管理员可改任意
r_bad = client.put(
    f"/api/enterprise/evaluations/{ee_id}",
    params={"token": T_ADMIN},
    json={"comment": "管理员终审修正"},
)
tc(r_bad.status_code == 200, f"企业管理员修改任意评价 200 (实际 {r_bad.status_code})")
r_check = client.get(f"/api/enterprise/evaluations/{ee_id}?token={T_MENTOR}")
tc(r_check.json()["data"]["comment"] == "管理员终审修正", "管理员修改已同步")

r404 = client.get(f"/api/enterprise/evaluations/99999?token={T_MENTOR}")
tc(r404.status_code == 404, f"评价详情 404 (实际 {r404.status_code})")

# =================== 用例 7：三方评价对比 ===================
print("\n[TC 7] 三方评价对比")
r = client.get(f"/api/enterprise/evaluations/compare/{sub1_id}?token={T_MENTOR}")
tc(r.status_code == 200, f"三方对比 200 (实际 {r.status_code})")
d = r.json()["data"]
ev = d["evaluations"]
tc(ev["ai"] is not None and ev["teacher"] is not None and ev["enterprise"] is not None,
   "AI/教师/企业评价齐全")
tc(abs(ev["ai"]["total_score"] - 85) < 1e-6, "AI 总分正确")
tc(abs(ev["teacher"]["total_score"] - 82) < 1e-6, "教师总分正确")
tc("parties" in d and "summary" in d and "dimension_breakdown" in d,
   "包含 parties/summary/dimension_breakdown 聚合")

sub2_id = DATA["sub2"]["id"]
r2 = client.get(f"/api/enterprise/evaluations/compare/{sub2_id}?token={T_MENTOR}")
tc(r2.status_code == 200, "部分缺失的三方对比 200")
d2 = r2.json()["data"]["evaluations"]
tc(d2["teacher"] is None and d2["ai"] is not None and d2["enterprise"] is not None,
   "教师缺失、AI+企业存在")

sub3_id = DATA["sub3"]["id"]
r3 = client.get(f"/api/enterprise/evaluations/compare/{sub3_id}?token={T_MENTOR}")
tc(r3.status_code == 200, "无任何评价的三方对比 200")
d3 = r3.json()["data"]["evaluations"]
tc(d3["ai"] is None and d3["teacher"] is None and d3["enterprise"] is None,
   "三方都缺失")

r404 = client.get(f"/api/enterprise/evaluations/compare/99999?token={T_MENTOR}")
tc(r404.status_code == 404, f"三方对比 404 (实际 {r404.status_code})")

# =================== 用例 8：学生我的企业评价 ===================
print("\n[TC 8] 学生查看我的企业评价列表")
r = client.get(f"/api/enterprise/student/my-evaluations?token={T_S1}")
tc(r.status_code == 200, f"学生端列表 200 (实际 {r.status_code})")
tc(r.json()["total"] >= 1, "S1 至少 1 条评价")
for it in r.json()["list"]:
    tc(it.get("mentor") is not None, "mentor 字段存在")

r2 = client.get(f"/api/enterprise/student/my-evaluations?token={T_S2}")
tc(r2.status_code == 200 and r2.json()["total"] == 1, "S2 恰好 1 条评价")

rx_t = client.get(f"/api/enterprise/student/my-evaluations?token={T_TEACHER}")
tc(rx_t.status_code == 200 and rx_t.json()["total"] == 0, "老师不传 class_id 返回空列表")
rx_e = client.get(f"/api/enterprise/student/my-evaluations?token={T_MENTOR}")
tc(rx_e.status_code == 200 and rx_e.json()["total"] == 0, "企业导师不传 class_id 返回空列表")

# =================== 用例 9：学生端三方对比 ===================
print("\n[TC 9] 学生端三方对比")
rc = client.get(f"/api/enterprise/student/compare/{sub1_id}?token={T_S1}")
tc(rc.status_code == 200, "学生端三方对比 200")
tc(rc.json()["data"]["evaluations"]["enterprise"] is not None, "学生端包含企业评价")

rc2 = client.get(f"/api/enterprise/student/compare/{sub1_id}?token={T_S2}")
tc(rc2.status_code == 403, f"S2 看 S1 的对比 403 (实际 {rc2.status_code})")

rc3 = client.get(f"/api/enterprise/student/compare/{sub1_id}?token={T_MENTOR}")
tc(rc3.status_code == 200, f"企业导师看本班学生对比 200 (实际 {rc3.status_code})")


print("\n================== ALL CASES PASSED ==================")
print(f"A3 自测通过：{passed}/{total_count} 断言")
print(f"[verify_a3] 清理临时 DB: {_TEST_DB_PATH}")
try:
    os.remove(_TEST_DB_PATH)
except Exception:
    pass
