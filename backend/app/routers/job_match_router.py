"""
岗位匹配 HTTP 端点（B1 第 3/4 步）。
前缀: /api/job-match
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.tables import User, Submission, Evaluation, Task
from app.models.class_models import Class, ClassMember as CM2, ClassMember
from app.models.enterprise_models import EnterpriseMentor, JobPosition, Enterprise
from app.services.job_matcher import (
    calculate_job_match,
    get_student_weighted_avg,
    batch_match_class,
    batch_match_student_to_jobs,
)
from app.utils.auth import decode_token

router = APIRouter(prefix="/api/job-match", tags=["岗位匹配"])


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
) -> User:
    if not token:
        raise HTTPException(401, "缺少 Token")
    payload = decode_token(token)
    if not payload or not payload.get("user_id"):
        raise HTTPException(401, "Token 无效或已过期")
    user = db.query(User).filter(User.id == int(payload["user_id"])).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def require_login(user: User = Depends(get_current_user)) -> User:
    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role != "teacher":
        raise HTTPException(403, "仅教师可访问")
    return user


def require_student(user: User = Depends(get_current_user)) -> User:
    if user.role != "student":
        raise HTTPException(403, "仅学生可访问")
    return user


def require_enterprise(user: User = Depends(get_current_user)) -> User:
    if user.role != "enterprise":
        raise HTTPException(403, "仅企业导师可访问")
    return user


# ============================================================
# 共享工具：查某个学生的所有评价 + 班级成员校验 + 企业可见班级
# ============================================================

def _get_mentor_enterprise_id(db: Session, user: User) -> Optional[int]:
    if user.role != "enterprise":
        return None
    row = db.query(EnterpriseMentor).filter(EnterpriseMentor.user_id == user.id).first()
    return row.enterprise_id if row else None


def _class_ids_for_enterprise(db: Session, enterprise_id: Optional[int]) -> List[int]:
    if not enterprise_id:
        return []
    rows = db.query(Class.id).filter(Class.enterprise_id == enterprise_id).all()
    return [r[0] for r in rows]


def _student_ids_in_class_ids(db: Session, class_ids: List[int]) -> List[int]:
    if not class_ids:
        return []
    # 兼容 class_class_members & class_members 两张可能的历史表
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


def _load_student_evaluations(db: Session, student_ids: List[int]):
    """批量加载学生评价（Evaluation：ai/teacher）。返回 {student_id: [ev, ev]}"""
    if not student_ids:
        return {}
    evs = (
        db.query(Evaluation, Submission.student_id)
        .join(Submission, Evaluation.submission_id == Submission.id)
        .filter(Submission.student_id.in_(student_ids))
        .filter(Evaluation.evaluator_type.in_(["ai", "teacher"]))
        .all()
    )
    out: dict = {sid: [] for sid in student_ids}
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


def _load_student_basics(db: Session, student_ids: List[int]) -> dict:
    if not student_ids:
        return {}
    users = db.query(User).filter(User.id.in_(student_ids)).all()
    # 查学生的班级（可能多个，取第一个班级名做展示）
    memberships: dict = {}
    try:
        from app.models.tables import ClassMember as TCM
        q = (
            db.query(TCM.student_id, Class.name)
            .join(Class, Class.id == TCM.class_id)
            .filter(TCM.student_id.in_(student_ids))
            .all()
        )
        for sid, cname in q:
            memberships.setdefault(sid, cname)
    except Exception:
        pass
    try:
        q2 = (
            db.query(CM2.student_id, Class.name)
            .join(Class, Class.id == CM2.class_id)
            .filter(CM2.student_id.in_(student_ids))
            .all()
        )
        for sid, cname in q2:
            memberships.setdefault(sid, cname)
    except Exception:
        pass
    out = {}
    for u in users:
        out[u.id] = {
            "id": u.id,
            "real_name": u.real_name or u.username,
            "username": u.username,
            "user_number": getattr(u, "user_number", ""),
            "email": getattr(u, "email", ""),
            "avatar": getattr(u, "avatar", ""),
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
    me: User = Depends(require_login),
):
    """
    单学生 × 单岗位 匹配详情。
    - 学生角色：只能查自己的 student_id
    - 教师/企业：可以查自己可见范围内的学生
    """
    # 权限
    if me.role == "student" and int(student_id) != int(me.id):
        raise HTTPException(403, "学生角色只能查看自己的匹配结果")

    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(404, "学生不存在")

    if me.role == "teacher":
        # 只要该学生在该老师任一班级下即可（简化：暂不做严格过滤）
        pass
    if me.role == "enterprise":
        eid = _get_mentor_enterprise_id(db, me)
        visible_students = _student_ids_in_class_ids(db, _class_ids_for_enterprise(db, eid))
        if visible_students and student_id not in visible_students:
            raise HTTPException(403, "无权查看该学生")

    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(404, "岗位不存在")
    if me.role == "enterprise":
        eid = _get_mentor_enterprise_id(db, me)
        if eid and int(job.enterprise_id) != int(eid):
            raise HTTPException(403, "只能查看本企业的岗位")

    ev_map = _load_student_evaluations(db, [student_id])
    dim_scores = get_student_weighted_avg(ev_map.get(student_id, []), last_n=last_n, decay=decay)
    result = calculate_job_match(dim_scores, job.skill_requirements or [])

    # 附上学生/岗位基础信息，前端少调一次接口
    basics = _load_student_basics(db, [student_id]).get(student_id, {})
    enterprise = db.query(Enterprise).filter(Enterprise.id == job.enterprise_id).first()
    return {
        "success": True,
        "student": {"id": student_id, **basics},
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
    me: User = Depends(require_login),
):
    """学生 TOP N 岗位匹配榜（前端 C3：EStudentProfile 的 TOP5 岗位榜）"""
    if me.role == "student" and int(student_id) != int(me.id):
        raise HTTPException(403, "学生角色只能查看自己的岗位榜")

    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(404, "学生不存在")

    # 加载岗位
    q = db.query(JobPosition).filter(JobPosition.status == "open")
    if job_id:
        q = q.filter(JobPosition.id == job_id)
    if enterprise_id:
        q = q.filter(JobPosition.enterprise_id == enterprise_id)
    if me.role == "enterprise":
        eid = _get_mentor_enterprise_id(db, me)
        if eid:
            q = q.filter(JobPosition.enterprise_id == eid)  # 企业只能看自己的岗位
    jobs = q.all()

    ev_map = _load_student_evaluations(db, [student_id])
    dim_scores = get_student_weighted_avg(ev_map.get(student_id, []), last_n=last_n, decay=decay)

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

    basics = _load_student_basics(db, [student_id]).get(student_id, {})
    return {
        "success": True,
        "student": {"id": student_id, **basics, "dimension_avg": dim_scores},
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
    me: User = Depends(require_login),
):
    """岗位匹配 TOP 榜（前端 C3 EJobMatch 左栏 + 直方图数据源）"""
    # 班级 / 岗位 存在性
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "班级不存在")
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(404, "岗位不存在")

    # 权限
    if me.role == "enterprise":
        eid = _get_mentor_enterprise_id(db, me)
        visible_class_ids = _class_ids_for_enterprise(db, eid)
        if int(class_id) not in visible_class_ids:
            raise HTTPException(403, "该企业无权查看此班级")
        if eid and int(job.enterprise_id) != int(eid):
            raise HTTPException(403, "只能匹配本企业的岗位")

    student_ids = _student_ids_in_class_ids(db, [class_id])
    if not student_ids:
        return {"success": True, "total": 0, "top_n": top_n,
                "class": {"id": class_id, "name": cls.name},
                "job": {"id": job.id, "title": job.title}, "list": []}

    ev_map = _load_student_evaluations(db, student_ids)
    dim_avg: dict = {
        sid: get_student_weighted_avg(ev_map.get(sid, []), last_n=last_n, decay=decay)
        for sid in student_ids
    }
    basics = _load_student_basics(db, student_ids)
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


@router.get("/generate-report")
def generate_match_report(
    class_id: int,
    job_id: int,
    top_n: int = Query(50, ge=1, le=500),
    min_score: float = Query(40.0, ge=0.0, le=100.0),
    fmt: str = Query("text", description="text / json"),
    db: Session = Depends(get_db),
    me: User = Depends(require_login),
):
    """生成班级×岗位的文字版匹配报告（企业端"下载报告"按钮用）"""
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "班级不存在")
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(404, "岗位不存在")
    if me.role == "enterprise":
        eid = _get_mentor_enterprise_id(db, me)
        if eid and int(job.enterprise_id) != int(eid):
            raise HTTPException(403, "只能下载本企业岗位的报告")

    # 复用 batch_class_match 内部逻辑，避免重复
    student_ids = _student_ids_in_class_ids(db, [class_id])
    basics = _load_student_basics(db, student_ids)
    ev_map = _load_student_evaluations(db, student_ids)
    dim_avg = {
        sid: get_student_weighted_avg(ev_map.get(sid, []))
        for sid in student_ids
    }
    rows = batch_match_class(
        students_scores=dim_avg,
        student_basics=basics,
        skill_requirements=job.skill_requirements or [],
        top_n=top_n,
        min_score=min_score,
    )
    text = _build_report_text(rows, cls.name, job.title)
    if fmt == "json":
        return {"success": True, "rows": rows, "report_text": text}
    return {"success": True, "report_text": text}
