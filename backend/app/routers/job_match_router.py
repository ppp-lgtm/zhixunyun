"""
岗位匹配 HTTP 端点（B1 第 3/4 步）。
前缀: /api/job-match
"""
from __future__ import annotations

import os
import io
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.tables import LoginAccount, Teacher, Student, Submission, Evaluation, Task
from app.models.class_models import Class, ClassMember as CM2, ClassMember
from app.models.enterprise_models import EnterpriseMentor, JobPosition, Enterprise
from app.services.job_matcher import (
    calculate_job_match,
    get_student_weighted_avg,
    batch_match_class,
    batch_match_student_to_jobs,
)
from app.services.report_generator import (
    _ensure_fpdf,
    _register_cn_fonts,
    _safe_cn,
    _mpl_bar,
    _mpl_hist,
    _pdf_add_image_if,
)
from app.utils.auth import decode_token

router = APIRouter(prefix="/api/job-match", tags=["岗位匹配"])


# ============================================================
# ID 转换辅助函数
# ============================================================

def _account_to_student_id(db: Session, account_id: int) -> Optional[int]:
    """login_accounts.id → students.id"""
    if not account_id:
        return None
    row = db.query(Student).filter(Student.account_id == int(account_id)).first()
    return row.id if row else None


def _account_to_teacher_id(db: Session, account_id: int) -> Optional[int]:
    """login_accounts.id → teachers.id"""
    if not account_id:
        return None
    row = db.query(Teacher).filter(Teacher.account_id == int(account_id)).first()
    return row.id if row else None


def _student_pk_to_account_id(db: Session, student_pk: int) -> Optional[int]:
    """students.id → login_accounts.id"""
    if not student_pk:
        return None
    row = db.query(Student).filter(Student.id == int(student_pk)).first()
    return row.account_id if row else None


def _teacher_pk_to_account_id(db: Session, teacher_pk: int) -> Optional[int]:
    """teachers.id → login_accounts.id"""
    if not teacher_pk:
        return None
    row = db.query(Teacher).filter(Teacher.id == int(teacher_pk)).first()
    return row.account_id if row else None


def _batch_account_to_student_ids(db: Session, account_ids: List[int]) -> dict:
    """批量：login_accounts.id → students.id。返回 {account_id: student_pk}"""
    if not account_ids:
        return {}
    rows = db.query(Student).filter(Student.account_id.in_(list(set(int(x) for x in account_ids if x)))).all()
    return {r.account_id: r.id for r in rows}


def _batch_student_pk_to_account_ids(db: Session, student_pks: List[int]) -> dict:
    """批量：students.id → login_accounts.id。返回 {student_pk: account_id}"""
    if not student_pks:
        return {}
    rows = db.query(Student).filter(Student.id.in_(list(set(int(x) for x in student_pks if x)))).all()
    return {r.id: r.account_id for r in rows}


def _role_is_teacher(user: LoginAccount, token_role: Optional[str] = None) -> bool:
    if user and user.role == "teacher":
        return True
    return token_role == "teacher"


def _role_is_student(user: LoginAccount, token_role: Optional[str] = None) -> bool:
    if user and user.role == "student":
        return True
    return token_role == "student"


def _role_is_enterprise(user: LoginAccount, token_role: Optional[str] = None) -> bool:
    if user and user.role == "mentor":
        return True
    return token_role == "enterprise"


# ============================================================
# 鉴权：同时兼容 ?token=xxx（和 enterprise_router 一致）与 Authorization: Bearer
# ============================================================

def _extract_token(
    token_query: Optional[str] = Query(None, alias="token", description="登录 token（URL 查询参数）"),
    authorization: Optional[str] = Header(None, description="Authorization: Bearer <token>"),
) -> Optional[str]:
    if token_query:
        return token_query
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(None, 1)[1].strip()
    if authorization:
        return authorization.strip()
    return None


def get_current_user(
    token: Optional[str] = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> LoginAccount:
    if not token:
        raise HTTPException(401, "缺少 Token")
    payload = decode_token(token)
    if not payload or not payload.get("user_id"):
        raise HTTPException(401, "Token 无效或已过期")
    user = db.query(LoginAccount).filter(LoginAccount.id == int(payload["user_id"])).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def _get_token_role_raw(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("role")


def require_login(user: LoginAccount = Depends(get_current_user)) -> LoginAccount:
    return user


def require_teacher(
    user: LoginAccount = Depends(get_current_user),
    token: Optional[str] = Depends(_extract_token),
) -> LoginAccount:
    token_role = _get_token_role_raw(token)
    if not _role_is_teacher(user, token_role):
        raise HTTPException(403, "仅教师可访问")
    return user


def require_student(
    user: LoginAccount = Depends(get_current_user),
    token: Optional[str] = Depends(_extract_token),
) -> LoginAccount:
    token_role = _get_token_role_raw(token)
    if not _role_is_student(user, token_role):
        raise HTTPException(403, "仅学生可访问")
    return user


def require_enterprise(
    user: LoginAccount = Depends(get_current_user),
    token: Optional[str] = Depends(_extract_token),
) -> LoginAccount:
    token_role = _get_token_role_raw(token)
    if not _role_is_enterprise(user, token_role):
        raise HTTPException(403, "仅企业导师可访问")
    return user


# ============================================================
# 共享工具：查某个学生的所有评价 + 班级成员校验 + 企业可见班级
# ============================================================

def _get_mentor_enterprise_id(db: Session, user: LoginAccount) -> Optional[int]:
    # user.role 用 mentor；兼容 token role 未映射的情况也查 EnterpriseMentor(account_id=user.id)
    row = db.query(EnterpriseMentor).filter(EnterpriseMentor.account_id == user.id).first()
    return row.enterprise_id if row else None


def _class_ids_for_enterprise(db: Session, enterprise_id: Optional[int]) -> List[int]:
    """企业可见班级：和 enterprise_router._enterprise_visible_class_ids 保持一致。

    1. 直接绑定 enterprise_id 的班级 + 岗位 linked_classes 绑定的班级（去重）
    2. 若 1) 为空（没绑定任何班级），按产品需求回退为**全部活跃班级**，
       保证企业端岗位匹配页 / 评价页永远有数据入口。"""
    direct_ids = set()
    from_job = set()
    if enterprise_id:
        direct = (
            db.query(Class.id)
            .filter(Class.enterprise_id == enterprise_id)
            .filter(Class.status == "active")
            .all()
        )
        direct_ids = {r[0] for r in direct}
        jobs = (
            db.query(JobPosition.linked_classes)
            .filter(JobPosition.enterprise_id == enterprise_id)
            .all()
        )
        for (linked,) in jobs:
            if not linked:
                continue
            for sid in linked.split(","):
                if sid.isdigit():
                    from_job.add(int(sid))
    visible = direct_ids | from_job
    if visible:
        return list(visible)
    all_active = db.query(Class.id).filter(Class.status == "active").all()
    return [c[0] for c in all_active]


def _student_pks_in_class_ids(db: Session, class_ids: List[int]) -> List[int]:
    """返回 class_ids 班级内的 students.id 列表（PK）。"""
    if not class_ids:
        return []
    ids = set()
    try:
        q1 = db.query(CM2.student_id).filter(CM2.class_id.in_(class_ids)).all()
        for (i,) in q1:
            ids.add(i)
    except Exception:
        pass
    try:
        from app.models.tables import ClassMember as TCM
        q2 = db.query(TCM.student_id).filter(TCM.class_id.in_(class_ids)).all()
        for (i,) in q2:
            ids.add(i)
    except Exception:
        pass
    return list(ids)


def _student_account_ids_in_class_ids(db: Session, class_ids: List[int]) -> List[int]:
    """返回 class_ids 班级内的 login_accounts.id 列表（对外兼容）。"""
    pks = _student_pks_in_class_ids(db, class_ids)
    if not pks:
        return []
    pk_map = _batch_student_pk_to_account_ids(db, pks)
    return [pk_map[pk] for pk in pks if pk in pk_map]


def _load_student_evaluations_by_pk(db: Session, student_pks: List[int]):
    """批量加载学生评价（students.id PK 列表）。返回 {student_pk: [ev, ev]}"""
    if not student_pks:
        return {}
    evs = (
        db.query(Evaluation, Submission.student_id)
        .join(Submission, Evaluation.submission_id == Submission.id)
        .filter(Submission.student_id.in_(student_pks))
        .filter(Evaluation.evaluator_type.in_(["ai", "teacher"]))
        .all()
    )
    out: dict = {sid: [] for sid in student_pks}
    for ev, sid in evs:
        row = {
            "submission_id": ev.submission_id,
            "evaluator_type": ev.evaluator_type,
            "total_score": ev.total_score,
            "dimension_scores": ev.dimension_scores,
            "comment": ev.comment,
            "created_at": ev.created_at,
        }
        out.setdefault(sid, []).append(row)
    return out


def _load_student_basics_by_account(db: Session, account_ids: List[int]) -> dict:
    """批量加载学生基础信息（按 login_accounts.id）。返回 {account_id: {id,real_name,...}}"""
    if not account_ids:
        return {}
    clean_ids = [int(x) for x in account_ids if x]
    if not clean_ids:
        return {}
    accounts = db.query(LoginAccount).filter(LoginAccount.id.in_(clean_ids)).all()
    students = db.query(Student).filter(Student.account_id.in_(clean_ids)).all()
    stu_by_acc = {s.account_id: s for s in students}

    account_set = set(clean_ids)
    memberships: dict = {}
    try:
        from app.models.tables import ClassMember as TCM
        stu_pks = [stu.id for stu in students if stu.account_id in account_set]
        if stu_pks:
            q = (
                db.query(TCM.student_id, Class.name)
                .join(Class, Class.id == TCM.class_id)
                .filter(TCM.student_id.in_(stu_pks))
                .all()
            )
            pk_to_acc = {s.id: s.account_id for s in students}
            for spk, cname in q:
                aid = pk_to_acc.get(spk)
                if aid is not None and aid not in memberships:
                    memberships[aid] = cname
    except Exception:
        pass
    try:
        stu_pks = [stu.id for stu in students if stu.account_id in account_set]
        if stu_pks:
            q2 = (
                db.query(CM2.student_id, Class.name)
                .join(Class, Class.id == CM2.class_id)
                .filter(CM2.student_id.in_(stu_pks))
                .all()
            )
            pk_to_acc = {s.id: s.account_id for s in students}
            for spk, cname in q2:
                aid = pk_to_acc.get(spk)
                if aid is not None and aid not in memberships:
                    memberships[aid] = cname
    except Exception:
        pass

    out = {}
    for u in accounts:
        s = stu_by_acc.get(u.id)
        real_name_val = ""
        user_number_val = ""
        if s:
            real_name_val = s.real_name or u.username or ""
            user_number_val = s.student_no or ""
        else:
            real_name_val = u.username or ""
        out[u.id] = {
            "id": u.id,
            "real_name": real_name_val,
            "username": u.username or "",
            "user_number": user_number_val,
            "email": u.email or "",
            "avatar": u.avatar or "",
            "class_name": memberships.get(u.id, ""),
        }
    return out


def _jobs_visible_to_enterprise(db: Session, enterprise_id: Optional[int]) -> List[int]:
    if not enterprise_id:
        return []
    rows = db.query(JobPosition.id).filter(JobPosition.enterprise_id == enterprise_id).all()
    return [r[0] for r in rows]


# ============================================================
# 端点 1：单岗位 → 单学生：匹配详情（基础，所有登录角色可查自己）
# ============================================================

@router.get("/detail")
def match_one_detail(
    student_id: int,
    job_id: int,
    last_n: int = Query(5, ge=1, le=50),
    decay: float = Query(0.8, ge=0.1, le=1.0),
    db: Session = Depends(get_db),
    me: LoginAccount = Depends(require_login),
    token: Optional[str] = Depends(_extract_token),
):
    """
    单学生 × 单岗位 匹配详情。
    - 学生角色：只能查自己的 student_id
    - 教师/企业：可以查自己可见范围内的学生
    """
    token_role = _get_token_role_raw(token)

    student_account_id = int(student_id)
    student_pk = _account_to_student_id(db, student_account_id)
    if not student_pk:
        raise HTTPException(404, "学生不存在")
    student_acc = db.query(LoginAccount).filter(LoginAccount.id == student_account_id).first()
    if not student_acc or not _role_is_student(student_acc, None):
        raise HTTPException(404, "学生不存在")

    # 权限
    if _role_is_student(me, token_role) and student_account_id != int(me.id):
        raise HTTPException(403, "学生角色只能查看自己的匹配结果")

    if _role_is_enterprise(me, token_role):
        eid = _get_mentor_enterprise_id(db, me)
        visible_account_ids = _student_account_ids_in_class_ids(db, _class_ids_for_enterprise(db, eid))
        if visible_account_ids and student_account_id not in visible_account_ids:
            raise HTTPException(403, "无权查看该学生")

    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(404, "岗位不存在")
    if _role_is_enterprise(me, token_role):
        eid = _get_mentor_enterprise_id(db, me)
        if eid and int(job.enterprise_id) != int(eid):
            raise HTTPException(403, "只能查看本企业的岗位")

    ev_map = _load_student_evaluations_by_pk(db, [student_pk])
    dim_scores = get_student_weighted_avg(ev_map.get(student_pk, []), last_n=last_n, decay=decay)
    result = calculate_job_match(dim_scores, job.skill_requirements or [])

    basics = _load_student_basics_by_account(db, [student_account_id]).get(student_account_id, {})
    enterprise = db.query(Enterprise).filter(Enterprise.id == job.enterprise_id).first()
    return {
        "success": True,
        "student": {"id": student_account_id, **basics},
        "job": {
            "id": job.id,
            "title": job.title,
            "job_type": job.job_type,
            "level": job.level,
            "salary_range": job.salary_range,
            "city": job.city,
            "enterprise_id": job.enterprise_id,
            "enterprise_name": enterprise.name if enterprise else "",
            "skill_requirements": job.skill_requirements or [],
        },
        "student_dimension_avg": dim_scores,
        **result,
    }


# ============================================================
# 端点 2：单学生 → 对全部 / 指定岗位 → TOP 榜
# 计划书：/job-match/student/{id}
# ============================================================

@router.get("/student/{student_id}")
def student_match_top_jobs(
    student_id: int,
    job_id: Optional[int] = None,
    enterprise_id: Optional[int] = None,
    top_n: int = Query(10, ge=1, le=200),
    last_n: int = Query(5, ge=1, le=50),
    decay: float = Query(0.8, ge=0.1, le=1.0),
    db: Session = Depends(get_db),
    me: LoginAccount = Depends(require_login),
    token: Optional[str] = Depends(_extract_token),
):
    """学生 TOP N 岗位匹配榜（前端 C3：EStudentProfile 的 TOP5 岗位榜）"""
    token_role = _get_token_role_raw(token)

    student_account_id = int(student_id)
    student_pk = _account_to_student_id(db, student_account_id)
    if not student_pk:
        raise HTTPException(404, "学生不存在")
    student_acc = db.query(LoginAccount).filter(LoginAccount.id == student_account_id).first()
    if not student_acc or not _role_is_student(student_acc, None):
        raise HTTPException(404, "学生不存在")

    if _role_is_student(me, token_role) and student_account_id != int(me.id):
        raise HTTPException(403, "学生角色只能查看自己的岗位榜")

    q = db.query(JobPosition).filter(JobPosition.status == "open")
    if job_id:
        q = q.filter(JobPosition.id == job_id)
    if enterprise_id:
        q = q.filter(JobPosition.enterprise_id == enterprise_id)
    if _role_is_enterprise(me, token_role):
        eid = _get_mentor_enterprise_id(db, me)
        if eid:
            q = q.filter(JobPosition.enterprise_id == eid)
    jobs = q.all()

    ev_map = _load_student_evaluations_by_pk(db, [student_pk])
    dim_scores = get_student_weighted_avg(ev_map.get(student_pk, []), last_n=last_n, decay=decay)

    def _job_to_payload(j):
        ent = db.query(Enterprise).filter(Enterprise.id == j.enterprise_id).first()
        return {
            "id": j.id,
            "title": j.title,
            "job_type": j.job_type,
            "level": j.level,
            "city": j.city,
            "salary_range": j.salary_range,
            "enterprise_id": j.enterprise_id,
            "enterprise_name": ent.name if ent else "",
            "skill_requirements": j.skill_requirements or [],
        }

    list_result = batch_match_student_to_jobs(
        student_scores=dim_scores,
        jobs=[_job_to_payload(j) for j in jobs],
        top_n=top_n,
    )

    basics = _load_student_basics_by_account(db, [student_account_id]).get(student_account_id, {})
    return {
        "success": True,
        "student": {"id": student_account_id, **basics, "dimension_avg": dim_scores},
        "total": len(list_result),
        "top_n": top_n,
        "list": list_result,
    }


# ============================================================
# 端点 3：全班 × 单岗位 → TOP N 学生榜（计划书 /batch-class）
# ============================================================

@router.get("/batch-class")
def batch_class_match(
    class_id: int,
    job_id: int,
    top_n: int = Query(20, ge=1, le=500),
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    last_n: int = Query(5, ge=1, le=50),
    decay: float = Query(0.8, ge=0.1, le=1.0),
    db: Session = Depends(get_db),
    me: LoginAccount = Depends(require_login),
    token: Optional[str] = Depends(_extract_token),
):
    """岗位匹配 TOP 榜（前端 C3 EJobMatch 左栏 + 直方图数据源）"""
    token_role = _get_token_role_raw(token)

    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "班级不存在")
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(404, "岗位不存在")

    if _role_is_enterprise(me, token_role):
        eid = _get_mentor_enterprise_id(db, me)
        visible_class_ids = _class_ids_for_enterprise(db, eid)
        if int(class_id) not in visible_class_ids:
            raise HTTPException(403, "该企业无权查看此班级")
        if eid is not None:
            has_own_job = (
                db.query(JobPosition.id)
                .filter(JobPosition.enterprise_id == eid)
                .first()
                is not None
            )
            if has_own_job and int(job.enterprise_id) != int(eid):
                raise HTTPException(403, "只能匹配本企业的岗位")

    student_pks = _student_pks_in_class_ids(db, [class_id])
    if not student_pks:
        return {"success": True, "total": 0, "top_n": top_n,
                "class": {"id": class_id, "name": cls.name},
                "job": {"id": job.id, "title": job.title}, "list": []}

    pk_to_acc = _batch_student_pk_to_account_ids(db, student_pks)
    account_ids = [pk_to_acc[pk] for pk in student_pks if pk in pk_to_acc]

    ev_map_pk = _load_student_evaluations_by_pk(db, student_pks)
    ev_map_acc: dict = {}
    for pk, evs in ev_map_pk.items():
        aid = pk_to_acc.get(pk)
        if aid is not None:
            ev_map_acc[aid] = evs

    dim_avg: dict = {}
    for pk in student_pks:
        aid = pk_to_acc.get(pk)
        if aid is None:
            continue
        dim_avg[aid] = get_student_weighted_avg(ev_map_acc.get(aid, []), last_n=last_n, decay=decay)

    basics = _load_student_basics_by_account(db, account_ids)
    matched = batch_match_class(
        students_scores=dim_avg,
        student_basics=basics,
        skill_requirements=job.skill_requirements or [],
        top_n=top_n,
        min_score=min_score,
    )
    ent = db.query(Enterprise).filter(Enterprise.id == job.enterprise_id).first()
    return {
        "success": True,
        "class": {"id": class_id, "name": cls.name},
        "job": {
            "id": job.id,
            "title": job.title,
            "job_type": job.job_type,
            "enterprise_id": job.enterprise_id,
            "enterprise_name": ent.name if ent else "",
            "skill_requirements": job.skill_requirements or [],
        },
        "total": len(matched),
        "top_n": top_n,
        "list": matched,
    }


# ============================================================
# 端点 4：生成文字版匹配报告（计划书 /generate-report）
# ============================================================

def _build_report_text(match_rows, class_name, job_title) -> str:
    if not match_rows:
        return f"【{class_name}】班级对【{job_title}】暂无满足条件的学生。\n"
    lines = []
    lines.append(f"班级【{class_name}】 × 岗位【{job_title}】 岗位匹配报告")
    lines.append("=" * 40)
    lines.append(f"符合条件学生共 {len(match_rows)} 名，TOP 10 如下：")
    for i, r in enumerate(match_rows[:10], 1):
        name = r.get("real_name") or r.get("username") or f"学生{r.get('student_id', '?')}"
        lines.append(f"\nNo.{i}. {name}（{r.get('class_name','')} {r.get('user_number','')}）")
        lines.append(f"    匹配分：{r.get('match_score')}   必选技能漏项：{r.get('must_failed_count', 0)} 项")
        if r.get("highlights"):
            lines.append("    亮点：" + "、".join(
                f"{h['name']}超门槛{h['delta']}分（{h['student_score']}/{h['threshold']}）"
                for h in r["highlights"][:3]
            ))
        if r.get("gaps"):
            majors = [g for g in r["gaps"] if g.get("level") == "major"]
            minors = [g for g in r["gaps"] if g.get("level") == "minor"]
            if majors:
                lines.append("    🔴 明显短板：" + "、".join(
                    f"{g['name']} {g['student_score']}/{g['threshold']} 差{abs(g['delta'])}分"
                    for g in majors[:3]
                ))
            if minors:
                lines.append("    🟡 小幅差距：" + "、".join(
                    f"{g['name']} {g['student_score']}/{g['threshold']} 差{abs(g['delta'])}分"
                    for g in minors[:3]
                ))
        must_names = [d["name"] for d in r.get("dimension_breakdown", [])
                      if d.get("must") and not d.get("passed")]
        if must_names:
            lines.append("    ❌ 必选技能未达标：" + "、".join(must_names))
    return "\n".join(lines) + "\n"


# ============================================================
#  排版精美的 PDF 报告生成（B1 匹配页下载按钮 fmt=pdf）
# ============================================================
def _normalize_reqs_for_pdf(reqs_raw):
    """把 job.skill_requirements 归一成统一结构数组"""
    reqs = reqs_raw or []
    if isinstance(reqs, str):
        try:
            import json as _json
            reqs = _json.loads(reqs)
        except Exception:
            tokens = [t.strip() for t in str(reqs).replace("，", ",").replace("；", ";").replace(";", ",").split(",") if t.strip()]
            reqs = [{"name": t, "weight": 20, "threshold": 60, "must": False} for t in tokens]
    if isinstance(reqs, list):
        out = []
        for r in reqs:
            if isinstance(r, str):
                out.append({"name": r, "weight": 20, "threshold": 60, "must": False})
            elif isinstance(r, dict):
                out.append({
                    "name": str(r.get("name", "") or "").strip(),
                    "weight": float(r.get("weight", 20) or 20),
                    "threshold": float(r.get("threshold", 60) or 60),
                    "must": bool(r.get("must", False)),
                })
        return [r for r in out if r["name"]]
    return []


def _build_report_pdf(filename, match_rows, class_name, job_info, enterprise_name) -> str:
    """生成排版精美的 PDF 报告，保存到 reports/ 并返回绝对路径。"""
    _ensure_fpdf()
    try:
        from fpdf import FPDF  # type: ignore
    except Exception:
        raise RuntimeError("缺少 fpdf2 依赖")

    from app.services.report_generator import REPORT_DIR
    os.makedirs(REPORT_DIR, exist_ok=True)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    fn, fnb = _register_cn_fonts(pdf)
    tmp_files: list[str] = []
    job_title = job_info.get("title") or "岗位"
    reqs = _normalize_reqs_for_pdf(job_info.get("skill_requirements"))

    # ----------- 色彩（和项目 UI 色板对应） -----------
    COLOR_SEAL = (255, 90, 31)     # 印章红：主标题、装饰条
    COLOR_AMBER = (244, 183, 64)   # 琥珀金：副装饰
    COLOR_JADE = (29, 185, 85)     # 翡翠：亮点/通过
    COLOR_COBALT = (61, 90, 254)   # 钴蓝：标题 2 级
    COLOR_INK = (44, 36, 24)       # 正文墨色
    COLOR_INK_3 = (115, 109, 96)   # 次级文字
    COLOR_PAPER = (246, 243, 236)  # 纸底
    COLOR_LINE = (222, 214, 199)   # 分隔线

    n_students = len(match_rows)
    avg_score = round(sum(float(r.get("match_score") or 0) for r in match_rows) / n_students, 1) if n_students else 0
    gt80 = sum(1 for r in match_rows if float(r.get("match_score") or 0) >= 80)
    gt70 = sum(1 for r in match_rows if float(r.get("match_score") or 0) >= 70)
    must_fail_total = sum(int(r.get("must_failed_count") or 0) for r in match_rows)

    # ============================================================
    # 第 1 页：封面
    # ============================================================
    pdf.add_page()
    # 顶部印章红装饰横条
    pdf.set_fill_color(*COLOR_SEAL)
    pdf.rect(10, 10, 190, 4, "F")
    # 左竖条
    pdf.set_fill_color(*COLOR_AMBER)
    pdf.rect(14, 20, 2.5, 60, "F")

    pdf.set_font(fn, "B", 13)
    pdf.set_text_color(*COLOR_COBALT)
    pdf.set_xy(24, 25)
    pdf.cell(0, 8, "ZHI XUN YUN  ·  知 训 云  人 才 匹 配 报 告",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(fn, "B", 30)
    pdf.set_text_color(*COLOR_INK)
    pdf.ln(12)
    pdf.set_x(24)
    pdf.cell(0, 16, "学 生 岗 位 匹 配 分 析",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(24)
    pdf.set_font(fn, "B", 30)
    pdf.set_text_color(*COLOR_SEAL)
    pdf.cell(0, 16, "报 告 书",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    # 副标题卡（班级 × 岗位）
    pdf.set_fill_color(255, 249, 244)
    pdf.set_draw_color(*COLOR_SEAL)
    card_y = pdf.get_y()
    pdf.set_x(24)
    pdf.cell(162, 82, "", border=1, fill=True,
             new_x="LMARGIN", new_y="TOP")
    # 卡片内标题
    pdf.set_y(card_y + 8)
    pdf.set_x(34)
    pdf.set_font(fn, "B", 12)
    pdf.set_text_color(*COLOR_INK_3)
    pdf.cell(0, 6, "匹 配 对 象",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_x(34)
    pdf.set_font(fn, "B", 18)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 10, f"班 级  ·  {_safe_cn(class_name, 40)}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(34)
    pdf.cell(0, 10, f"岗 位  ·  {_safe_cn(job_title, 40)}",
             new_x="LMARGIN", new_y="NEXT")
    if enterprise_name:
        pdf.set_x(34)
        pdf.set_font(fn, "", 13)
        pdf.set_text_color(*COLOR_INK_3)
        pdf.cell(0, 8, f"招 聘 企 业  ·  {_safe_cn(enterprise_name, 50)}",
                 new_x="LMARGIN", new_y="NEXT")

    # 分隔线
    pdf.set_draw_color(*COLOR_LINE)
    pdf.line(34, card_y + 58, 176, card_y + 58)

    pdf.set_y(card_y + 62)
    pdf.set_x(34)
    pdf.set_font(fn, "", 11)
    pdf.set_text_color(*COLOR_INK_3)
    pdf.cell(72, 7, f"生成日期：{datetime.now().strftime('%Y 年 %m 月 %d 日')}",
             new_x="RIGHT", new_y="TOP")
    pdf.cell(90, 7, f"报告编号：ZM-{datetime.now().strftime('%Y%m%d%H%M')}-{class_id if False else hash(class_name + job_title) % 10000:04d}",
             new_x="LMARGIN", new_y="NEXT")

    # 封面右下角印章装饰
    pdf.set_fill_color(*COLOR_SEAL)
    pdf.rect(144, 232, 44, 44, "DF")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(fn, "B", 14)
    pdf.set_xy(144, 240)
    pdf.cell(44, 10, "ZHI XUN YUN", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(144, 251)
    pdf.set_font(fn, "B", 10)
    pdf.cell(44, 7, "知 训 云 · 专 用", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(144, 259)
    pdf.set_font(fn, "", 9)
    pdf.cell(44, 7, "MATCH REPORT", align="C",
             new_x="LMARGIN", new_y="NEXT")

    # 底部横条
    pdf.set_fill_color(*COLOR_SEAL)
    pdf.rect(10, 286, 190, 4, "F")

    # ============================================================
    # 第 2 页：核心指标 + 目录
    # ============================================================
    pdf.add_page()
    pdf.set_fill_color(*COLOR_SEAL)
    pdf.rect(10, 10, 190, 2, "F")
    pdf.ln(6)
    pdf.set_font(fn, "B", 18)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 10, "一 、 核 心 指 标 概 览",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 4 个 KPI 卡（绝对 X 坐标，避免 cell 的 new_x 重置导致全部叠到最左侧）
    cards = [
        ("符 合 条 件 学 生", f"{n_students}", "人", COLOR_COBALT, "#3D5AFE"),
        ("平 均 匹 配 分", f"{avg_score}", "分", COLOR_SEAL, "#FF5A1F"),
        ("≥ 80 分 人 数", f"{gt80}", "人", COLOR_JADE, "#1DB955"),
        ("≥ 70 分 人 数", f"{gt70}", "人", COLOR_AMBER, "#F4B740"),
    ]
    col_w = pdf.epw / 4
    lm = pdf.l_margin
    card_top = pdf.get_y()
    for i, (k, v, u, c_hex, _css) in enumerate(cards):
        card_x = lm + i * col_w
        # 背景卡
        pdf.set_fill_color(c_hex[0], c_hex[1], c_hex[2])
        pdf.set_xy(card_x, card_top)
        pdf.cell(col_w, 36, "", border=0, fill=True,
                 new_x="RIGHT", new_y="TOP")
        # 数字
        pdf.set_xy(card_x, card_top + 5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(fn, "B", 22)
        pdf.cell(col_w, 14, f"{v} {u}", align="C",
                 new_x="RIGHT", new_y="TOP")
        # 标签
        pdf.set_xy(card_x, card_top + 21)
        pdf.set_font(fn, "", 10)
        pdf.set_text_color(255, 245, 238)
        pdf.cell(col_w, 8, _safe_cn(k), align="C",
                 new_x="RIGHT", new_y="TOP")
    pdf.set_y(card_top + 42)

    # 额外指标行
    pdf.set_text_color(*COLOR_INK_3)
    pdf.set_font(fn, "", 11)
    meta_line = [
        f"岗位门槛维度：{len(reqs)} 项",
        f"必选维度：{sum(1 for r in reqs if r['must'])} 项",
        f"全班必选漏项合计：{must_fail_total} 项",
    ]
    for i, t in enumerate(meta_line):
        pdf.set_x(10 + i * (pdf.epw / 3))
        pdf.cell(pdf.epw / 3, 7, _safe_cn(t), align="C",
                 new_x="RIGHT", new_y="TOP")
    pdf.ln(10)

    # 匹配分分布直方图
    pdf.set_font(fn, "B", 15)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 10, "二 、 全 班 匹 配 分 分 布",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    scores = [float(r.get("match_score") or 0) for r in match_rows]
    hist_png = _mpl_hist(
        scores, bins=10,
        title=f"{_safe_cn(class_name)} → {_safe_cn(job_title)}  匹配分分布直方图",
        color="#FF5A1F")
    if _pdf_add_image_if(pdf, hist_png, w=180, cleanup_paths=tmp_files):
        pdf.ln(6)
    else:
        pdf.set_font(fn, "", 10)
        pdf.set_text_color(*COLOR_INK_3)
        pdf.multi_cell(0, 6, "  （图表组件不可用：请 pip install matplotlib）")
        pdf.ln(4)

    # 目录
    pdf.set_font(fn, "B", 15)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 10, "三 、 报 告 章 节 导 览",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_draw_color(*COLOR_LINE)
    outline = [
        ("一", "核心指标概览", "本页"),
        ("二", "全班匹配分分布直方图", "本页"),
        ("三", "岗位门槛维度说明（权重 / 门槛 / 必选）", "P.3"),
        ("四", "TOP N 候选人排行榜（表格）", "P.3"),
        ("五", "TOP 3 候选人详细画像 × 维度对标", "P.4 - P.6"),
        ("六", "招聘建议与结语", "末页"),
    ]
    pdf.set_font(fn, "", 11)
    for num, title_txt, page_ref in outline:
        y0 = pdf.get_y()
        # 编号
        pdf.set_text_color(*COLOR_SEAL)
        pdf.set_font(fn, "B", 11)
        pdf.cell(10, 7, f"{num}.", new_x="RIGHT", new_y="TOP")
        # 标题
        pdf.set_text_color(*COLOR_INK)
        pdf.set_font(fn, "", 11)
        pdf.cell(145, 7, _safe_cn(title_txt), new_x="RIGHT", new_y="TOP")
        # 页码
        pdf.set_text_color(*COLOR_INK_3)
        pdf.cell(0, 7, page_ref, align="R",
                 new_x="LMARGIN", new_y="NEXT")
        # 点线
        pdf.set_draw_color(*COLOR_LINE)
        pdf.line(20, y0 + 6.5, 200, y0 + 6.5)

    # ============================================================
    # 第 3 页：岗位门槛说明 + TOP 排行榜表格
    # ============================================================
    pdf.add_page()
    pdf.set_fill_color(*COLOR_COBALT)
    pdf.rect(10, 10, 190, 2, "F")
    pdf.ln(6)
    pdf.set_font(fn, "B", 18)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 10, "三 、 岗 位 门 槛 维 度 说 明",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    if not reqs:
        pdf.set_font(fn, "", 11)
        pdf.set_text_color(*COLOR_INK_3)
        pdf.multi_cell(0, 7, "  该岗位暂未设置技能门槛，系统按默认维度（20% 权重 / 60 分门槛）进行匹配计算。")
        pdf.ln(4)
    else:
        # 表头
        headers = ["序 号", "维 度 名 称", "权 重", "门 槛 分", "是 否 必 选"]
        ws = [18, 82, 30, 30, 30]
        pdf.set_font(fn, "B", 10.5)
        pdf.set_fill_color(*COLOR_COBALT)
        pdf.set_text_color(255, 255, 255)
        for w, h in zip(ws, headers):
            pdf.cell(w, 9, _safe_cn(h), border="TB", align="C", fill=True,
                     new_x="RIGHT", new_y="TOP")
        pdf.ln(9)
        # 内容
        pdf.set_font(fn, "", 10.5)
        for idx, r in enumerate(reqs, 1):
            fill = (idx % 2 == 0)
            if fill:
                pdf.set_fill_color(248, 245, 238)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(*COLOR_INK)
            vals = [
                str(idx),
                _safe_cn(r["name"], 20),
                f"{round(r['weight'])}%",
                f"{round(r['threshold'])}",
                "★ 必选" if r["must"] else "○ 加分",
            ]
            for w, v in zip(ws, vals):
                align = "C"
                if w == ws[1]:
                    align = "L"
                col_t = COLOR_SEAL if (r["must"] and w == ws[4]) else COLOR_INK
                pdf.set_text_color(*col_t)
                pdf.cell(w, 8, v, border="B", align=align, fill=fill,
                         new_x="RIGHT", new_y="TOP")
            pdf.ln(8)
        # 小计行
        pdf.set_fill_color(*COLOR_PAPER)
        pdf.set_font(fn, "B", 10.5)
        pdf.set_text_color(*COLOR_INK_3)
        pdf.cell(sum(ws[:2]), 8, f"  合 计  ·  共 {len(reqs)} 项维度，权重合计 {round(sum(r['weight'] for r in reqs))}%",
                 border="T", align="L", fill=True, new_x="RIGHT", new_y="TOP")
        pdf.cell(sum(ws[2:]), 8, "", border="T", align="R", fill=True,
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # TOP 排行榜表格
    pdf.set_fill_color(*COLOR_SEAL)
    pdf.rect(10, pdf.get_y(), 190, 2, "F")
    pdf.ln(6)
    pdf.set_font(fn, "B", 18)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 10, f"四 、 TOP {min(len(match_rows), 20)} 候 选 人 排 行 榜",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    if not match_rows:
        pdf.set_font(fn, "", 11)
        pdf.set_text_color(*COLOR_INK_3)
        pdf.multi_cell(0, 7, "  该班级暂无可匹配的学生。建议降低最低匹配分，或补充班级评价数据后重新匹配。")
    else:
        # 表头
        hdrs = ["排 名", "姓 名", "学 号", "班 级", "匹配分", "必选漏项", "亮点 / 缺口摘要"]
        ws = [14, 24, 30, 26, 20, 22, 54]
        pdf.set_font(fn, "B", 10)
        pdf.set_fill_color(*COLOR_SEAL)
        pdf.set_text_color(255, 255, 255)
        for w, h in zip(ws, hdrs):
            pdf.cell(w, 9, _safe_cn(h), border=0, align="C", fill=True,
                     new_x="RIGHT", new_y="TOP")
        pdf.ln(9)

        show_rows = match_rows[:20]
        pdf.set_font(fn, "", 10)
        for idx, r in enumerate(show_rows, 1):
            fill = (idx % 2 == 0)
            bg_fill_odd = (255, 255, 255)
            bg_fill_even = (248, 245, 238)
            bg = bg_fill_even if fill else bg_fill_odd
            if idx <= 3:
                if idx == 1:
                    bg = (255, 246, 224)  # 金
                elif idx == 2:
                    bg = (242, 244, 247)  # 银
                else:
                    bg = (255, 240, 224)  # 铜

            # 亮点 + 缺口摘要
            hl = r.get("highlights") or []
            gp = r.get("gaps") or []
            parts = []
            if hl:
                parts.append("+" + "、".join(f"{h['name']}{h['delta']}" for h in hl[:2]))
            if gp:
                majors = [g for g in gp if g.get("level") == "major"]
                if majors:
                    parts.append("-" + "、".join(f"{g['name']}{abs(g['delta'])}" for g in majors[:2]))
                else:
                    parts.append("~" + "、".join(f"{g['name']}{abs(g['delta'])}" for g in gp[:2]))
            summary_txt = "  ".join(parts) if parts else "—"

            vals = [
                f"No.{idx}",
                _safe_cn(r.get("real_name") or r.get("username") or "", 8),
                _safe_cn(r.get("user_number") or "", 12),
                _safe_cn(r.get("class_name") or class_name or "", 10),
                f"{round(float(r.get('match_score') or 0))}",
                f"{int(r.get('must_failed_count') or 0)} 项",
                _safe_cn(summary_txt, 28),
            ]
            pdf.set_fill_color(*bg)
            row_y = pdf.get_y()
            # 背景整行
            x_start = pdf.get_x()
            for w, v, hdr_w in zip(ws, vals, ws):
                pass
            # 直接用多个 cell 做行背景
            for w in ws:
                pdf.cell(w, 16, "", border="B", fill=True,
                         new_x="RIGHT", new_y="TOP")
            # 文字
            pdf.set_y(row_y + 1)
            pdf.set_x(x_start)
            # 排名
            if idx <= 3:
                medal_color = COLOR_SEAL if idx == 1 else (COLOR_INK_3 if idx == 2 else COLOR_AMBER)
                pdf.set_text_color(*medal_color)
                pdf.set_font(fn, "B", 10)
            else:
                pdf.set_text_color(*COLOR_INK)
                pdf.set_font(fn, "", 10)
            pdf.cell(ws[0], 14, vals[0], align="C", new_x="RIGHT", new_y="TOP")
            # 姓名
            pdf.set_text_color(*COLOR_INK)
            pdf.set_font(fn, "B", 10)
            pdf.cell(ws[1], 14, vals[1], align="C", new_x="RIGHT", new_y="TOP")
            # 学号 / 班级
            pdf.set_font(fn, "", 10)
            pdf.set_text_color(*COLOR_INK_3)
            pdf.cell(ws[2], 14, vals[2], align="C", new_x="RIGHT", new_y="TOP")
            pdf.cell(ws[3], 14, vals[3], align="C", new_x="RIGHT", new_y="TOP")
            # 匹配分
            score = float(r.get("match_score") or 0)
            if score >= 85:
                pdf.set_text_color(*COLOR_JADE)
            elif score >= 70:
                pdf.set_text_color(*COLOR_COBALT)
            elif score >= 60:
                pdf.set_text_color(*COLOR_AMBER)
            else:
                pdf.set_text_color(*COLOR_SEAL)
            pdf.set_font(fn, "B", 12)
            pdf.cell(ws[4], 14, vals[4], align="C", new_x="RIGHT", new_y="TOP")
            # 必选漏项
            mf_count = int(r.get("must_failed_count") or 0)
            if mf_count > 0:
                pdf.set_text_color(*COLOR_SEAL)
                pdf.set_font(fn, "B", 10)
            else:
                pdf.set_text_color(*COLOR_JADE)
                pdf.set_font(fn, "", 10)
            pdf.cell(ws[5], 14, vals[5], align="C", new_x="RIGHT", new_y="TOP")
            # 摘要
            pdf.set_text_color(*COLOR_INK)
            pdf.set_font(fn, "", 9.5)
            pdf.cell(ws[6], 14, vals[6], align="L",
                     new_x="LMARGIN", new_y="NEXT")
            # 如果下一行超页，确保表格继续
            if pdf.get_y() + 16 > 270 and idx < len(show_rows) - 1:
                pdf.add_page()
                # 续表头
                pdf.set_fill_color(*COLOR_SEAL)
                pdf.rect(10, 10, 190, 2, "F")
                pdf.ln(6)
                pdf.set_font(fn, "B", 10)
                pdf.set_text_color(255, 255, 255)
                pdf.set_fill_color(*COLOR_SEAL)
                for w, h in zip(ws, hdrs):
                    pdf.cell(w, 9, _safe_cn(h), border=0, align="C", fill=True,
                             new_x="RIGHT", new_y="TOP")
                pdf.ln(9)

    # ============================================================
    # TOP 3 候选人详细画像（每人一页，最多 3 页）
    # ============================================================
    for rank_idx, r in enumerate(match_rows[:3], 1):
        pdf.add_page()
        pdf.set_fill_color(*COLOR_SEAL)
        pdf.rect(10, 10, 190, 2, "F")
        pdf.ln(6)
        pdf.set_font(fn, "B", 17)
        pdf.set_text_color(*COLOR_INK)
        pdf.cell(0, 10, f"五 、 TOP {rank_idx} 候 选 人 详 细 画 像",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        stu_name = r.get("real_name") or r.get("username") or f"学生{r.get('student_id', '?')}"
        stu_no = r.get("user_number") or "—"
        stu_cls = r.get("class_name") or class_name or "—"
        match_s = round(float(r.get("match_score") or 0), 1)
        mf_c = int(r.get("must_failed_count") or 0)

        # 学生信息卡
        pdf.set_fill_color(255, 249, 244)
        pdf.set_draw_color(*COLOR_SEAL)
        card_y = pdf.get_y()
        pdf.cell(pdf.epw, 44, "", border=1, fill=True,
                 new_x="LMARGIN", new_y="TOP")
        # 大排名徽章
        if rank_idx == 1:
            medal_rgb = (245, 158, 11)
        elif rank_idx == 2:
            medal_rgb = (148, 163, 184)
        else:
            medal_rgb = (217, 119, 6)
        pdf.set_fill_color(*medal_rgb)
        pdf.set_draw_color(*medal_rgb)
        pdf.ellipse(20, card_y + 6, 40, 32, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(fn, "B", 14)
        pdf.set_xy(20, card_y + 14)
        pdf.cell(40, 10, f"TOP {rank_idx}", align="C",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(20, card_y + 24)
        pdf.set_font(fn, "", 9)
        pdf.cell(40, 6, "CANDIDATE", align="C",
                 new_x="LMARGIN", new_y="NEXT")
        # 基本信息文字
        pdf.set_font(fn, "B", 16)
        pdf.set_text_color(*COLOR_INK)
        pdf.set_xy(66, card_y + 6)
        pdf.cell(0, 11, _safe_cn(stu_name, 20),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(fn, "", 11)
        pdf.set_text_color(*COLOR_INK_3)
        pdf.set_x(66)
        pdf.cell(0, 7, f"学 号  ·  {_safe_cn(stu_no, 30)}      班 级  ·  {_safe_cn(stu_cls, 30)}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(66)
        pdf.set_font(fn, "B", 12)
        pdf.set_text_color(*COLOR_SEAL)
        pdf.cell(0, 8, f"综 合 匹 配 分  ·  {match_s} / 100      必选漏项  ·  {mf_c} 项",
                 new_x="LMARGIN", new_y="NEXT")
        # 等级说明
        pdf.set_font(fn, "", 10)
        if match_s >= 85:
            grade_label = "★★★★★  强 烈 推 荐 面 试"
            pdf.set_text_color(*COLOR_JADE)
        elif match_s >= 70:
            grade_label = "★★★★  建 议 优 先 面 试"
            pdf.set_text_color(*COLOR_COBALT)
        elif match_s >= 60:
            grade_label = "★★★  满 足 基 本 条 件，可 考 虑"
            pdf.set_text_color(*COLOR_AMBER)
        else:
            grade_label = "★★  与 岗 位 差 距 较 大，慎 重"
            pdf.set_text_color(*COLOR_SEAL)
        pdf.set_x(66)
        pdf.cell(0, 7, grade_label,
                 new_x="LMARGIN", new_y="NEXT")

        pdf.set_y(card_y + 50)

        # 维度对标条形图（横向）
        pdf.set_font(fn, "B", 14)
        pdf.set_text_color(*COLOR_INK)
        pdf.cell(0, 10, "5.1   维 度 得 分 vs 门 槛 对 标",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        dims = r.get("dimension_breakdown") or []
        if dims:
            # 用 matplotlib 画横条对比图（学生得分 vs 门槛）
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import numpy as np
                from app.services.report_generator import _ensure_cn_font
                _ensure_cn_font()
                names = [_safe_cn(d.get("name") or "维度", 10) for d in dims]
                stu_vs = [float(d.get("student_score") or 0) for d in dims]
                thr_vs = [float(d.get("threshold") or 60) for d in dims]
                y_pos = list(range(len(names)))
                fig_w = max(7, 2.5 + 0.5 * len(names))
                fig, ax = plt.subplots(figsize=(fig_w, 4.8), dpi=140)
                bar_h = 0.35
                bars1 = ax.barh([y + bar_h / 2 for y in y_pos], stu_vs, height=bar_h,
                                color="#FF5A1F", label="学生得分", edgecolor="white")
                bars2 = ax.barh([y - bar_h / 2 for y in y_pos], thr_vs, height=bar_h,
                                color="#3D5AFE", alpha=0.7, label="岗位门槛", edgecolor="white")
                ax.set_yticks(y_pos)
                ax.set_yticklabels(names, fontsize=9)
                ax.invert_yaxis()
                ax.set_xlim(0, 100)
                ax.set_xlabel("得分")
                ax.set_title(f"{_safe_cn(stu_name)} · 维度得分 vs 岗位门槛 对 照 图",
                             fontsize=12, fontweight="bold", pad=10)
                ax.legend(loc="lower right", fontsize=8)
                ax.grid(axis="x", linestyle="--", alpha=0.3)
                ax.axvline(60, color="#F4B740", linestyle=":", linewidth=0.8, label="60 分及格线")
                for bar, v in zip(bars1, stu_vs):
                    ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2,
                            f"{v:.0f}", va="center", fontsize=7.5, color="#FF5A1F")
                for bar, v in zip(bars2, thr_vs):
                    ax.text(v + 0.6, bar.get_y() + bar.get_height() / 2,
                            f"{v:.0f}", va="center", fontsize=7.5, color="#3D5AFE", alpha=0.9)
                fig.tight_layout()
                # 保存临时 PNG
                tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "reports")
                os.makedirs(tmp_dir, exist_ok=True)
                import uuid
                tmp_path = os.path.join(tmp_dir, f"_tmp_dim_{uuid.uuid4().hex[:8]}.png")
                fig.savefig(tmp_path, bbox_inches="tight", facecolor="white")
                plt.close(fig)
                tmp_files.append(tmp_path)
                if os.path.exists(tmp_path):
                    _pdf_add_image_if(pdf, open(tmp_path, "rb").read(), w=180, cleanup_paths=tmp_files)
                    pdf.ln(3)
            except Exception:
                pass

        # 亮点 / 缺口
        pdf.set_font(fn, "B", 14)
        pdf.set_text_color(*COLOR_INK)
        pdf.cell(0, 10, "5.2   亮 点 与 短 板 分 析",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        hl = r.get("highlights") or []
        gp = r.get("gaps") or []
        # 左：亮点（翡翠绿块）
        col2_w = pdf.epw / 2 - 3
        block_y = pdf.get_y()
        # 亮点卡
        pdf.set_fill_color(236, 253, 245)
        pdf.set_draw_color(*COLOR_JADE)
        pdf.cell(col2_w, 8, "", border="TLR", fill=True,
                 new_x="RIGHT", new_y="TOP")
        pdf.set_xy(pdf.get_x() - col2_w, block_y + 1)
        pdf.set_text_color(*COLOR_JADE)
        pdf.set_font(fn, "B", 11)
        pdf.cell(col2_w, 6, "  ■  HIGHLIGHT · 岗 位 优 势 亮 点",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(10)
        if not hl:
            pdf.set_fill_color(236, 253, 245)
            pdf.cell(col2_w, 46, "", border="LRB", fill=True,
                     new_x="RIGHT", new_y="TOP")
            pdf.set_xy(10, block_y + 11)
            pdf.set_font(fn, "", 10)
            pdf.set_text_color(*COLOR_INK_3)
            pdf.set_x(16)
            pdf.cell(col2_w - 12, 40, "  该学生各维度与门槛基本持平，无显著超越项。",
                     align="L", new_x="LMARGIN", new_y="NEXT")
        else:
            # 亮点行
            highlight_block_h = 8 + 10 * min(3, len(hl)) + 6
            pdf.set_fill_color(236, 253, 245)
            pdf.cell(col2_w, highlight_block_h, "", border="LRB", fill=True,
                     new_x="RIGHT", new_y="TOP")
            iy = block_y + 10
            for h in hl[:3]:
                pdf.set_xy(14, iy)
                pdf.set_text_color(*COLOR_JADE)
                pdf.set_font(fn, "B", 10)
                pdf.cell(col2_w - 8, 6,
                         f"  ●  {_safe_cn(h.get('name') or '维度', 12)}   超门槛 +{h.get('delta')} 分   "
                         f"（得 {round(float(h.get('student_score') or 0))} / 门槛 {round(float(h.get('threshold') or 0))}）",
                         new_x="LMARGIN", new_y="NEXT")
                iy += 10
        # 缺口卡
        right_x = 10 + col2_w + 6
        pdf.set_xy(right_x, block_y)
        pdf.set_fill_color(255, 243, 238)
        pdf.set_draw_color(*COLOR_SEAL)
        pdf.cell(col2_w, 8, "", border="TLR", fill=True,
                 new_x="RIGHT", new_y="TOP")
        pdf.set_xy(right_x, block_y + 1)
        pdf.set_text_color(*COLOR_SEAL)
        pdf.set_font(fn, "B", 11)
        pdf.cell(col2_w, 6, "  ■  GAP ·  待 提 升 短 板",
                 new_x="LMARGIN", new_y="NEXT")
        majors = [g for g in gp if g.get("level") == "major"]
        minors = [g for g in gp if g.get("level") == "minor"]
        total_gp = len(majors) + len(minors)
        gp_block_h = 8 + 10 * max(1, min(3, total_gp)) + 6
        pdf.set_xy(right_x, block_y + 8)
        pdf.set_fill_color(255, 243, 238)
        pdf.cell(col2_w, gp_block_h, "", border="LRB", fill=True,
                 new_x="LMARGIN", new_y="NEXT")
        iy = block_y + 10
        pdf.set_x(right_x + 4)
        if not gp:
            pdf.set_text_color(*COLOR_INK_3)
            pdf.set_font(fn, "", 10)
            pdf.cell(col2_w - 8, 40, "  未检测到明显短板，各项指标均达到或超过门槛要求。",
                     align="L", new_x="LMARGIN", new_y="NEXT")
        else:
            shown = 0
            for g in majors[:2]:
                pdf.set_xy(right_x + 4, iy)
                pdf.set_text_color(*COLOR_SEAL)
                pdf.set_font(fn, "B", 10)
                pdf.cell(col2_w - 8, 6,
                         f"  🔴  {_safe_cn(g.get('name') or '维度', 12)}   差 {abs(int(g.get('delta') or 0))} 分  "
                         f"（得 {round(float(g.get('student_score') or 0))} / 门槛 {round(float(g.get('threshold') or 0))}）",
                         new_x="LMARGIN", new_y="NEXT")
                iy += 10
                shown += 1
            for g in minors[:max(0, 3 - shown)]:
                pdf.set_xy(right_x + 4, iy)
                pdf.set_text_color(*COLOR_AMBER)
                pdf.set_font(fn, "", 10)
                pdf.cell(col2_w - 8, 6,
                         f"  🟡  {_safe_cn(g.get('name') or '维度', 12)}   差 {abs(int(g.get('delta') or 0))} 分  "
                         f"（得 {round(float(g.get('student_score') or 0))} / 门槛 {round(float(g.get('threshold') or 0))}）",
                         new_x="LMARGIN", new_y="NEXT")
                iy += 10
                shown += 1

        # 必选技能达标清单
        pdf.set_y(max(pdf.get_y(), block_y + max(60, gp_block_h + 12)))
        pdf.ln(4)
        pdf.set_font(fn, "B", 14)
        pdf.set_text_color(*COLOR_INK)
        pdf.cell(0, 10, "5.3   必 选 技 能 达 标 清 单",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        must_dims = [d for d in dims if d.get("must")]
        if not must_dims:
            pdf.set_font(fn, "", 10.5)
            pdf.set_text_color(*COLOR_INK_3)
            pdf.cell(0, 7, "  （本岗位无标注为「必选」的门槛）",
                     new_x="LMARGIN", new_y="NEXT")
        else:
            ws = [60, 30, 30, 70]
            hdrs = ["必 选 维 度", "学 生 得 分", "门 槛", "结 论"]
            pdf.set_font(fn, "B", 10)
            pdf.set_fill_color(*COLOR_COBALT)
            pdf.set_text_color(255, 255, 255)
            for w, h in zip(ws, hdrs):
                pdf.cell(w, 8, _safe_cn(h), border=0, align="C", fill=True,
                         new_x="RIGHT", new_y="TOP")
            pdf.ln(8)
            pdf.set_font(fn, "", 10)
            for i, d in enumerate(must_dims, 1):
                fill = (i % 2 == 0)
                if fill:
                    pdf.set_fill_color(248, 245, 238)
                else:
                    pdf.set_fill_color(255, 255, 255)
                passed = bool(d.get("passed"))
                if passed:
                    res_txt = "✅ 达 标"
                    pdf.set_text_color(*COLOR_JADE)
                else:
                    res_txt = "❌ 未 达 标"
                    pdf.set_text_color(*COLOR_SEAL)
                vals = [
                    _safe_cn(d.get("name") or "", 18),
                    f"{round(float(d.get('student_score') or 0))}",
                    f"{round(float(d.get('threshold') or 0))}",
                    res_txt,
                ]
                for w, v in zip(ws, vals):
                    pdf.cell(w, 8, v, border="B", align="C", fill=fill,
                             new_x="RIGHT", new_y="TOP")
                pdf.ln(8)

        # 面试建议
        pdf.ln(4)
        pdf.set_font(fn, "B", 13)
        pdf.set_text_color(*COLOR_INK)
        pdf.cell(0, 9, "5.4   面 试 与 复 核 建 议",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.set_font(fn, "", 10.5)
        pdf.set_text_color(*COLOR_INK)
        tips = []
        if match_s >= 85:
            tips.append(f"【强烈推荐】综合匹配分 {match_s}，该生整体表现优异，建议在 3 个工作日内发起面试邀约。")
        elif match_s >= 70:
            tips.append(f"【优先考虑】综合匹配分 {match_s}，整体满足岗位大部分要求，建议安排技术一面。")
        elif match_s >= 60:
            tips.append(f"【可考虑】综合匹配分 {match_s}，达到基本门槛，可结合简历项目经历综合判断。")
        else:
            tips.append(f"【建议延后】综合匹配分 {match_s}，与岗位差距较大，除非有其他突出经历否则不建议优先面试。")
        if mf_c > 0:
            tips.append(f"必选技能有 {mf_c} 项未达标，面试时重点考核对应维度的实战能力，判断是否「临时没发挥」还是「确实薄弱」。")
        if hl:
            top_h = hl[0]
            tips.append(f"亮点维度「{top_h.get('name', '')}」超门槛 +{top_h.get('delta')} 分，可重点作为岗位核心贡献方向，安排相关项目负责人面。")
        if majors:
            top_m = majors[0]
            tips.append(f"短板「{top_m.get('name', '')}」差距 {abs(int(top_m.get('delta') or 0))} 分，入职后建议制定针对性补训计划（预计 4-8 周可追平）。")
        tips.append("面试题建议：围绕 TOP 2 最大短板维度设计编码题 / 场景题，避免仅靠简历判断。")
        for i, t in enumerate(tips, 1):
            pdf.set_x(14)
            pdf.set_text_color(*COLOR_INK)
            pdf.cell(0, 6.5, f"  {i}.  {_safe_cn(t, 80)}",
                     new_x="LMARGIN", new_y="NEXT")

    # ============================================================
    # 末页：招聘建议 + 结语 + 版权
    # ============================================================
    pdf.add_page()
    pdf.set_fill_color(*COLOR_JADE)
    pdf.rect(10, 10, 190, 2, "F")
    pdf.ln(6)
    pdf.set_font(fn, "B", 18)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 10, "六 、 招 聘 建 议 与 结 语",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # 建议块
    pdf.set_fill_color(248, 253, 250)
    pdf.set_draw_color(*COLOR_JADE)
    block_y = pdf.get_y()
    pdf.cell(pdf.epw, 46, "", border=1, fill=True,
             new_x="LMARGIN", new_y="TOP")
    pdf.set_xy(14, block_y + 4)
    pdf.set_text_color(*COLOR_JADE)
    pdf.set_font(fn, "B", 12)
    pdf.cell(0, 7, "■  RECRUIT · 整 体 招 聘 策 略 建 议",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    advice_lines = []
    if n_students == 0:
        advice_lines.append("当前班级暂无可匹配学生，建议：")
        advice_lines.append("  ① 扩大匹配范围（放宽最低分或调整班级范围）")
        advice_lines.append("  ② 与授课教师沟通是否有评价数据尚未录入")
        advice_lines.append("  ③ 视情况放宽门槛权重，或重新发布岗位说明")
    else:
        if gt80 >= 3:
            advice_lines.append(f"✅ 本班 ≥ 80 分候选人 {gt80} 人，人才供给充足，建议尽快组织批量面试（3 日内启动效率最高）。")
        elif gt80 >= 1:
            advice_lines.append(f"✅ 本班有 {gt80} 位高分候选人，建议重点锁定并尽快邀约，避免被其他企业先行录用。")
        elif gt70 >= 3:
            advice_lines.append(f"🔸 本班 ≥ 70 分候选人 {gt70} 人，整体人才质量中等偏上，可分 2 批安排面试。")
        else:
            advice_lines.append("🔸 本班高分候选人较少，建议结合多班级汇总后统一安排面试，或重新匹配其他班级。")
        if must_fail_total > n_students:
            advice_lines.append(f"⚠️  全班必选技能累计 {must_fail_total} 项漏项，建议在面试环节统一做必选维度的标准化笔试题。")
        advice_lines.append(f"📊 平均匹配分 {avg_score}，{class_name} → {job_title} 整体匹配度 {'良好' if avg_score >= 70 else '一般'}。")
        advice_lines.append("💡 建议面试流程：必选维度笔试 60 分钟 → 技术面 45 分钟 → HR / 部门面 30 分钟。")
    pdf.set_font(fn, "", 10.5)
    pdf.set_text_color(*COLOR_INK)
    for line in advice_lines:
        pdf.set_x(18)
        pdf.cell(0, 7, _safe_cn(line, 80),
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # 维度总体统计条（全班各维度均分排行，和岗位门槛对照）
    if reqs:
        pdf.set_font(fn, "B", 15)
        pdf.set_text_color(*COLOR_INK)
        pdf.cell(0, 10, "6.1   全 班 各 维 度 掌 握 情 况（vs 门 槛）",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np
            from app.services.report_generator import _ensure_cn_font
            _ensure_cn_font()
            # 计算全班各维度均分
            dim_names = [_safe_cn(r["name"], 12) for r in reqs]
            class_dims_avg = []
            for rd in reqs:
                rname = rd.get("name") or ""
                scores = []
                for s in match_rows:
                    for d in (s.get("dimension_breakdown") or []):
                        if (d.get("name") or "") == rname:
                            scores.append(float(d.get("student_score") or 0))
                            break
                class_dims_avg.append(round(sum(scores) / len(scores), 1) if scores else 0.0)
            thresholds = [round(float(r["threshold"]), 1) for r in reqs]
            x = list(range(len(dim_names)))
            fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=140)
            w_ = 0.36
            ax.bar([i - w_ / 2 for i in x], class_dims_avg, width=w_, color="#FF5A1F",
                   label=f"{_safe_cn(class_name)} 全班均分", edgecolor="white")
            ax.bar([i + w_ / 2 for i in x], thresholds, width=w_, color="#3D5AFE", alpha=0.75,
                   label=f"{_safe_cn(job_title)} 岗位门槛", edgecolor="white")
            ax.set_xticks(x)
            ax.set_xticklabels(dim_names, fontsize=9, rotation=10)
            ax.set_ylim(0, 105)
            ax.set_ylabel("得分 / 门槛")
            ax.set_title(f"{_safe_cn(class_name)} × {_safe_cn(job_title)} 维度掌握对照",
                         fontsize=12, fontweight="bold", pad=10)
            ax.axhline(60, color="#F4B740", linestyle=":", linewidth=0.8, label="及格线 60")
            ax.legend(loc="lower right", fontsize=8)
            ax.grid(axis="y", linestyle="--", alpha=0.3)
            fig.tight_layout()
            import uuid
            tmp_dir2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "reports")
            os.makedirs(tmp_dir2, exist_ok=True)
            tmp_path2 = os.path.join(tmp_dir2, f"_tmp_class_dim_{uuid.uuid4().hex[:8]}.png")
            fig.savefig(tmp_path2, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            tmp_files.append(tmp_path2)
            if os.path.exists(tmp_path2):
                _pdf_add_image_if(pdf, open(tmp_path2, "rb").read(), w=180, cleanup_paths=tmp_files)
                pdf.ln(3)
        except Exception:
            pass

    # 结语
    pdf.ln(4)
    pdf.set_font(fn, "B", 13)
    pdf.set_text_color(*COLOR_INK)
    pdf.cell(0, 9, "6.2   结 语",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font(fn, "", 10.5)
    pdf.set_text_color(*COLOR_INK)
    closing = (
        f"本报告基于「{_safe_cn(class_name)}」班级学生在实训评价系统中的历史表现，"
        f"结合「{_safe_cn(job_title)}」岗位的技能门槛与权重配置自动生成。"
        "匹配分数仅代表学生在当前课程维度下的综合表现，实际招聘中请结合简历、面试、笔试等多维度综合判断。"
        "祝企业招聘顺利，学生学有所成！"
    )
    # multi_cell 自动换行
    pdf.multi_cell(0, 7, _safe_cn(closing, 200))
    pdf.ln(6)

    # 签名区
    pdf.set_draw_color(*COLOR_LINE)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font(fn, "", 10)
    pdf.set_text_color(*COLOR_INK_3)
    pdf.cell(95, 6, f"招聘企业（盖章）：{_safe_cn(enterprise_name or '____________', 30)}",
             new_x="RIGHT", new_y="TOP")
    pdf.cell(95, 6, f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.cell(95, 6, "导师签字：________________",
             new_x="RIGHT", new_y="TOP")
    pdf.cell(95, 6, f"数据来源：知训云 实训评价匹配系统", align="R",
             new_x="LMARGIN", new_y="NEXT")

    # 页脚
    pdf.set_y(272)
    pdf.set_fill_color(*COLOR_SEAL)
    pdf.rect(10, 286, 190, 4, "F")
    pdf.set_font(fn, "", 9)
    pdf.set_text_color(*COLOR_INK_3)
    pdf.cell(0, 6, "— 本报告由知训云自动生成 · 仅用于企业招聘辅助，未经授权不得外传 —",
             align="C", new_x="LMARGIN", new_y="NEXT")

    # 保存
    filepath = os.path.join(REPORT_DIR, filename)
    pdf.output(filepath)
    # 清理临时图片
    for p in tmp_files:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    return filepath
# ---- end of _build_report_pdf ----


@router.get("/generate-report")
def generate_match_report(
    class_id: int,
    job_id: int,
    top_n: int = Query(50, ge=1, le=500),
    min_score: float = Query(40.0, ge=0.0, le=100.0),
    fmt: str = Query("pdf", description="pdf / text / json"),
    db: Session = Depends(get_db),
    me: LoginAccount = Depends(require_login),
    token: Optional[str] = Depends(_extract_token),
):
    """生成班级×岗位的匹配报告（企业端"下载报告"按钮用，默认 PDF 排版精美版）"""
    token_role = _get_token_role_raw(token)

    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "班级不存在")
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(404, "岗位不存在")
    if _role_is_enterprise(me, token_role):
        eid = _get_mentor_enterprise_id(db, me)
        visible_class_ids = _class_ids_for_enterprise(db, eid)
        if int(class_id) not in visible_class_ids:
            raise HTTPException(403, "该企业无权查看此班级")
        if eid is not None:
            has_own_job = (
                db.query(JobPosition.id)
                .filter(JobPosition.enterprise_id == eid)
                .first()
                is not None
            )
            if has_own_job and int(job.enterprise_id) != int(eid):
                raise HTTPException(403, "只能下载本企业岗位的报告")

    student_pks = _student_pks_in_class_ids(db, [class_id])
    pk_to_acc = _batch_student_pk_to_account_ids(db, student_pks)
    account_ids = [pk_to_acc[pk] for pk in student_pks if pk in pk_to_acc]

    basics = _load_student_basics_by_account(db, account_ids)
    ev_map_pk = _load_student_evaluations_by_pk(db, student_pks)
    ev_map_acc = {pk_to_acc[pk]: evs for pk, evs in ev_map_pk.items() if pk in pk_to_acc}

    dim_avg = {
        aid: get_student_weighted_avg(ev_map_acc.get(aid, []))
        for aid in account_ids
    }
    rows = batch_match_class(
        students_scores=dim_avg,
        student_basics=basics,
        skill_requirements=job.skill_requirements or [],
        top_n=top_n,
        min_score=min_score,
    )

    # -------- fmt=pdf：生成排版精美的 PDF --------
    if fmt.lower() == "pdf":
        enterprise_info = db.query(Enterprise).filter(Enterprise.id == job.enterprise_id).first()
        enterprise_name = enterprise_info.name if enterprise_info else ""
        job_dict = {
            "id": job.id,
            "title": job.title,
            "job_type": job.job_type,
            "skill_requirements": job.skill_requirements or [],
        }
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_cls = "".join(c for c in cls.name if c.isalnum() or '\u4e00' <= c <= '\u9fff') or f"class{class_id}"
        safe_job = "".join(c for c in (job.title or "job") if c.isalnum() or '\u4e00' <= c <= '\u9fff') or f"job{job_id}"
        filename = f"岗位匹配报告_{safe_cls}_{safe_job}_{ts}.pdf"
        try:
            abs_path = _build_report_pdf(filename, rows, cls.name, job_dict, enterprise_name)
        except Exception as e:
            raise HTTPException(500, f"PDF 报告生成失败：{e}")
        if not os.path.exists(abs_path):
            raise HTTPException(500, "PDF 报告文件生成失败")
        # Content-Disposition 带 UTF-8 文件名
        from urllib.parse import quote
        disposition = f"attachment; filename*=UTF-8''{quote(filename)}"
        return FileResponse(
            path=abs_path,
            media_type="application/pdf",
            headers={"Content-Disposition": disposition},
        )

    # -------- fallback：旧的 text / json 格式 --------
    text = _build_report_text(rows, cls.name, job.title)
    if fmt == "json":
        return {"success": True, "rows": rows, "report_text": text}
    return {"success": True, "report_text": text}
