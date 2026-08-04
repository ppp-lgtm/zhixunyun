from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import SessionLocal
from app.models.tables import Submission, Evaluation, LoginAccount, Teacher, Student, EvaluationCriteria, Task
from app.models.class_models import Class, ClassMember

router = APIRouter(prefix="/api/statistics", tags=["数据统计"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# ID 转换辅助函数
# ============================================================

def _account_to_student_id(db: Session, account_id: int):
    if not account_id:
        return None
    row = db.query(Student).filter(Student.account_id == int(account_id)).first()
    return row.id if row else None


def _account_to_teacher_id(db: Session, account_id: int):
    if not account_id:
        return None
    row = db.query(Teacher).filter(Teacher.account_id == int(account_id)).first()
    return row.id if row else None


def _student_pk_to_account_id(db: Session, student_pk: int):
    if not student_pk:
        return None
    row = db.query(Student).filter(Student.id == int(student_pk)).first()
    return row.account_id if row else None


def _teacher_pk_to_account_id(db: Session, teacher_pk: int):
    if not teacher_pk:
        return None
    row = db.query(Teacher).filter(Teacher.id == int(teacher_pk)).first()
    return row.account_id if row else None


def _batch_student_pk_to_account(db: Session, student_pks):
    if not student_pks:
        return {}
    clean = [int(x) for x in student_pks if x]
    if not clean:
        return {}
    rows = db.query(Student).filter(Student.id.in_(clean)).all()
    return {r.id: r.account_id for r in rows}


def _batch_account_to_student_pk(db: Session, account_ids):
    if not account_ids:
        return {}
    clean = [int(x) for x in account_ids if x]
    if not clean:
        return {}
    rows = db.query(Student).filter(Student.account_id.in_(clean)).all()
    return {r.account_id: r.id for r in rows}


# 辅助函数：根据课程名获取所有关联的 submission ids
def get_course_submission_ids(db: Session, course: str):
    if not course:
        return None
    task_ids = db.query(Task.id).filter(Task.title == course, Task.status == "published").all()
    task_id_list = [t[0] for t in task_ids]
    if not task_id_list:
        return []
    sub_ids = db.query(Submission.id).filter(Submission.task_id.in_(task_id_list)).all()
    return [s[0] for s in sub_ids]


@router.get("/overview")
def get_overview(class_id: int = 0, course: str = "", db: Session = Depends(get_db)):
    course_sub_ids = get_course_submission_ids(db, course)

    if class_id > 0:
        sub_query = db.query(Submission.id).filter(Submission.class_id.like(f"%{class_id}%"))
        if course_sub_ids is not None:
            sub_query = sub_query.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        total_submissions = db.query(func.count(Submission.id)).filter(
            Submission.class_id.like(f"%{class_id}%")
        )
        if course_sub_ids is not None:
            total_submissions = total_submissions.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        total_submissions = total_submissions.scalar() or 0
        total_evaluations = db.query(func.count(Evaluation.id)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        avg_score = db.query(func.avg(Evaluation.total_score)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        max_score = db.query(func.max(Evaluation.total_score)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        min_score = db.query(func.min(Evaluation.total_score)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        # class_id 下的学生数：按 submissions 去重 student_id (students.pk)
        distinct_stu_pks = db.query(Submission.student_id).filter(
            Submission.class_id.like(f"%{class_id}%")
        ).distinct().all()
        student_count = len([x[0] for x in distinct_stu_pks if x[0]])
        teacher_count = 0
    else:
        base_query = db.query(Submission.id)
        if course_sub_ids is not None:
            base_query = base_query.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        sub_query = base_query
        total_submissions = db.query(func.count(Submission.id))
        if course_sub_ids is not None:
            total_submissions = total_submissions.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        total_submissions = total_submissions.scalar() or 0
        total_evaluations = db.query(func.count(Evaluation.id)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        avg_score = db.query(func.avg(Evaluation.total_score)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        max_score = db.query(func.max(Evaluation.total_score)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        min_score = db.query(func.min(Evaluation.total_score)).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_query)
        ).scalar() or 0
        # 全局统计：直接查 Student / Teacher 表，无需 role filter
        student_count = db.query(func.count(Student.id)).scalar() or 0
        teacher_count = db.query(func.count(Teacher.id)).scalar() or 0

    return {
        "success": True,
        "data": {
            "total_submissions": total_submissions,
            "total_evaluations": total_evaluations,
            "avg_score": round(float(avg_score) if avg_score else 0, 1),
            "max_score": float(max_score) if max_score else 0,
            "min_score": float(min_score) if min_score else 0,
            "student_count": student_count,
            "teacher_count": teacher_count
        }
    }


@router.get("/score-distribution")
def get_score_distribution(class_id: int = 0, course: str = "", db: Session = Depends(get_db)):
    course_sub_ids = get_course_submission_ids(db, course)

    if class_id > 0:
        sub_ids = db.query(Submission.id).filter(Submission.class_id.like(f"%{class_id}%"))
        if course_sub_ids is not None:
            sub_ids = sub_ids.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        sub_id_list = [s[0] for s in sub_ids.all()]
    else:
        sub_ids = db.query(Submission.id)
        if course_sub_ids is not None:
            sub_ids = sub_ids.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        sub_id_list = [s[0] for s in sub_ids.all()]

    if sub_id_list:
        evaluations = db.query(Evaluation.total_score).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_id_list)
        ).all()
    else:
        evaluations = []

    distribution = {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    for (score,) in evaluations:
        if score < 60:
            distribution["0-59"] += 1
        elif score < 70:
            distribution["60-69"] += 1
        elif score < 80:
            distribution["70-79"] += 1
        elif score < 90:
            distribution["80-89"] += 1
        else:
            distribution["90-100"] += 1

    return {"success": True, "data": [{"range": k, "count": v} for k, v in distribution.items()]}


@router.get("/trend")
def get_score_trend(class_id: int = 0, course: str = "", db: Session = Depends(get_db)):
    course_sub_ids = get_course_submission_ids(db, course)

    if class_id > 0:
        sub_ids = db.query(Submission.id).filter(Submission.class_id.like(f"%{class_id}%"))
        if course_sub_ids is not None:
            sub_ids = sub_ids.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        sub_id_list = [s[0] for s in sub_ids.all()]
    else:
        sub_ids = db.query(Submission.id)
        if course_sub_ids is not None:
            sub_ids = sub_ids.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        sub_id_list = [s[0] for s in sub_ids.all()]

    if sub_id_list:
        evaluations = db.query(
            Evaluation.total_score, Evaluation.created_at, Submission.filename
        ).join(Submission, Evaluation.submission_id == Submission.id).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_id_list)
        ).order_by(Evaluation.created_at.desc()).limit(20).all()
    else:
        evaluations = []

    return {
        "success": True,
        "data": [
            {"score": float(e.total_score), "time": e.created_at.strftime("%m-%d %H:%M") if e.created_at else "", "filename": e.filename}
            for e in reversed(evaluations)
        ]
    }


@router.get("/dimension-avg")
def get_dimension_avg(class_id: int = 0, course: str = "", db: Session = Depends(get_db)):
    course_sub_ids = get_course_submission_ids(db, course)

    if class_id > 0:
        sub_ids = db.query(Submission.id).filter(Submission.class_id.like(f"%{class_id}%"))
        if course_sub_ids is not None:
            sub_ids = sub_ids.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        sub_id_list = [s[0] for s in sub_ids.all()]
    else:
        sub_ids = db.query(Submission.id)
        if course_sub_ids is not None:
            sub_ids = sub_ids.filter(Submission.id.in_(course_sub_ids) if course_sub_ids else Submission.id == -1)
        sub_id_list = [s[0] for s in sub_ids.all()]

    if sub_id_list:
        evaluations = db.query(Evaluation.dimension_scores).filter(
            Evaluation.evaluator_type == "ai",
            Evaluation.submission_id.in_(sub_id_list)
        ).all()
    else:
        evaluations = []

    dimension_totals = {}
    dimension_counts = {}
    for (scores,) in evaluations:
        if scores:
            for item in scores:
                name = item.get("name", "未知")
                score = item.get("score", 0)
                dimension_totals[name] = dimension_totals.get(name, 0) + score
                dimension_counts[name] = dimension_counts.get(name, 0) + 1

    result = [{"name": name, "avg": round(dimension_totals[name] / dimension_counts[name], 1)} for name in dimension_totals]
    return {"success": True, "data": result}


@router.get("/student/{student_id}")
def get_student_scores(student_id: int, page: int = 1, page_size: int = 5, db: Session = Depends(get_db)):
    # 入参 student_id 是 login_accounts.id → 转 students.pk
    student_pk = _account_to_student_id(db, student_id)
    if not student_pk:
        return {
            "success": True,
            "data": {
                "records": [],
                "weakness": [],
                "total_count": 0,
                "avg_score": 0
            }
        }

    # 先查总数
    total_query = db.query(func.count(Submission.id)).join(
        Evaluation, Evaluation.submission_id == Submission.id
    ).filter(
        Submission.student_id == student_pk,
        Evaluation.evaluator_type == "ai"
    )
    total_count = total_query.scalar() or 0

    # 分页查询
    submissions = db.query(
        Submission.id, Submission.filename, Submission.created_at, Submission.task_id,
        Evaluation.total_score, Evaluation.dimension_scores, Evaluation.comment,
        Evaluation.step_completeness, Evaluation.logic_issues
    ).join(Evaluation, Evaluation.submission_id == Submission.id).filter(
        Submission.student_id == student_pk,
        Evaluation.evaluator_type == "ai"
    ).order_by(Submission.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 查任务标题
    task_ids = list(set(s.task_id for s in submissions if s.task_id))
    task_map = {}
    if task_ids:
        tasks = db.query(Task.id, Task.title).filter(Task.id.in_(task_ids)).all()
        task_map = {t.id: t.title for t in tasks}

    records = []
    dimension_weakness = {}

    # 统计所有数据的薄弱维度（不分页）
    all_scores = db.query(Evaluation.dimension_scores).join(
        Submission, Evaluation.submission_id == Submission.id
    ).filter(
        Submission.student_id == student_pk,
        Evaluation.evaluator_type == "ai"
    ).all()

    for (scores,) in all_scores:
        if scores:
            for item in scores:
                name = item.get("name", "")
                score = item.get("score", 0)
                if score < 70:
                    dimension_weakness[name] = dimension_weakness.get(name, 0) + 1

    for s in submissions:
        scores = s.dimension_scores or []
        records.append({
            "id": s.id,
            "filename": s.filename.split(',')[0] if s.filename else '',
            "task_title": task_map.get(s.task_id, '未知任务'),
            "time": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "",
            "total_score": float(s.total_score) if s.total_score else 0,
            "scores": scores,
            "comment": s.comment,
            "step_completeness": s.step_completeness or [],
            "logic_issues": s.logic_issues or []
        })

    weakness_list = sorted(dimension_weakness.items(), key=lambda x: x[1], reverse=True)
    weakness_list = [{"name": name, "count": count} for name, count in weakness_list[:3]]

    # 算平均分（全量）
    all_avg = db.query(func.avg(Evaluation.total_score)).join(
        Submission, Evaluation.submission_id == Submission.id
    ).filter(
        Submission.student_id == student_pk,
        Evaluation.evaluator_type == "ai"
    ).scalar() or 0

    return {
        "success": True,
        "data": {
            "records": records,
            "weakness": weakness_list,
            "total_count": total_count,
            "avg_score": round(float(all_avg), 1) if all_avg else 0
        }
    }


@router.get("/student/{student_id}/teacher-scores")
def get_student_teacher_scores(student_id: int, db: Session = Depends(get_db)):
    student_pk = _account_to_student_id(db, student_id)
    if not student_pk:
        return {"success": True, "data": []}

    results = db.query(
        Submission.id, Submission.filename, Submission.created_at,
        Evaluation.total_score, Evaluation.dimension_scores, Evaluation.comment
    ).join(Evaluation, Evaluation.submission_id == Submission.id).filter(
        Submission.student_id == student_pk,
        Evaluation.evaluator_type == "teacher"
    ).order_by(Submission.created_at.desc()).all()

    data = []
    for r in results:
        data.append({
            "submission_id": r.id,
            "filename": r.filename,
            "time": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
            "total_score": float(r.total_score) if r.total_score else 0,
            "scores": r.dimension_scores,
            "comment": r.comment
        })
    return {"success": True, "data": data}


@router.get("/class/{class_id}")
def get_class_stats(class_id: int, db: Session = Depends(get_db)):
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()

    all_member_pks = [m.student_id for m in members if m.student_id]
    pk_to_acc = _batch_student_pk_to_account(db, all_member_pks)

    # 预加载：student_pk → (student_name, student_number) 从 Student 表取，避免依赖 CM2 冗余字段
    stu_rows = db.query(Student).filter(Student.id.in_(all_member_pks)).all() if all_member_pks else []
    stu_info = {r.id: (r.real_name, r.student_no) for r in stu_rows}

    student_scores = []
    for m in members:
        spk = m.student_id
        account_id = pk_to_acc.get(spk) if spk else None

        name_from_info = stu_info.get(spk, ("", "")) if spk else ("", "")
        student_name = m.student_name or name_from_info[0] or ""
        student_number = m.student_number or name_from_info[1] or ""

        submissions = db.query(Submission.id, Submission.filename, Submission.created_at).filter(
            Submission.student_id == spk
        ).all()

        eval_scores = []
        for s in submissions:
            evals = db.query(Evaluation.total_score, Evaluation.evaluator_type).filter(Evaluation.submission_id == s.id).all()
            ai_score = next((e.total_score for e in evals if e.evaluator_type == "ai"), None)
            teacher_score = next((e.total_score for e in evals if e.evaluator_type == "teacher"), None)
            eval_scores.append({
                "submission_id": s.id,
                "filename": s.filename,
                "time": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "",
                "ai_score": float(ai_score) if ai_score else None,
                "teacher_score": float(teacher_score) if teacher_score else None
            })

        # 返回 student_id 仍用 login_accounts.id（对外契约兼容）
        out_student_id = account_id if account_id is not None else (spk or 0)
        student_scores.append({
            "student_id": out_student_id,
            "student_name": student_name,
            "student_number": student_number or "",
            "submission_count": len(eval_scores),
            "avg_ai_score": round(sum(e["ai_score"] for e in eval_scores if e["ai_score"]) / max(1, len([e for e in eval_scores if e["ai_score"]])), 1) if eval_scores else 0,
            "submissions": eval_scores
        })

    student_scores.sort(key=lambda x: x["avg_ai_score"], reverse=True)

    all_scores = [s["avg_ai_score"] for s in student_scores if s["avg_ai_score"] > 0]
    class_avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    submit_count = sum(s["submission_count"] for s in student_scores)

    return {
        "success": True,
        "data": {
            "class_avg": class_avg,
            "total_students": len(student_scores),
            "total_submissions": submit_count,
            "students": student_scores
        }
    }


@router.get("/class/{class_id}/ranking")
def get_class_ranking(class_id: int, student_id: int = 0, db: Session = Depends(get_db)):
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()

    all_member_pks = [m.student_id for m in members if m.student_id]
    pk_to_acc = _batch_student_pk_to_account(db, all_member_pks)

    stu_rows = db.query(Student).filter(Student.id.in_(all_member_pks)).all() if all_member_pks else []
    stu_info = {r.id: r.real_name for r in stu_rows}

    # 传入的 student_id 是 login_accounts.id，需要找到对应 student_pk 用来比对
    my_student_pk = None
    if student_id and student_id > 0:
        my_student_pk = _account_to_student_id(db, student_id)

    student_scores = []
    for m in members:
        spk = m.student_id
        account_id = pk_to_acc.get(spk) if spk else None

        evals = db.query(Evaluation.total_score).join(
            Submission, Evaluation.submission_id == Submission.id
        ).filter(Submission.student_id == spk, Evaluation.evaluator_type == "ai").all()
        scores = [float(e.total_score) for e in evals if e.total_score]
        avg = round(sum(scores) / len(scores), 1) if scores else 0

        student_name = m.student_name or stu_info.get(spk, "") or ""
        # 返回 student_id 用 login_accounts.id
        out_student_id = account_id if account_id is not None else (spk or 0)
        student_scores.append({
            "student_id": out_student_id,
            "student_name": student_name,
            "avg_score": avg,
            "submit_count": len(scores)
        })

    student_scores.sort(key=lambda x: x["avg_score"], reverse=True)

    # my_rank 对比也按 student_pk → account_id 转后再比
    my_account_id_for_compare = None
    if my_student_pk:
        my_account_id_for_compare = pk_to_acc.get(my_student_pk)

    my_rank = 0
    my_avg = 0
    for i, s in enumerate(student_scores):
        if my_account_id_for_compare is not None and s["student_id"] == my_account_id_for_compare:
            my_rank = i + 1
            my_avg = s["avg_score"]
            break
        # 兼容未转换时按原始 student_id 直比（避免老数据）
        if my_account_id_for_compare is None and student_id and s["student_id"] == student_id:
            my_rank = i + 1
            my_avg = s["avg_score"]
            break

    class_avg = round(sum(s["avg_score"] for s in student_scores if s["avg_score"]) / max(1, len([s for s in student_scores if s["avg_score"]])), 1)

    return {
        "success": True,
        "data": {
            "ranking": student_scores[:10],
            "my_rank": my_rank,
            "my_avg": my_avg,
            "class_avg": class_avg,
            "total_students": len(student_scores)
        }
    }


@router.get("/notifications/{student_id}")
def get_notifications(student_id: int, db: Session = Depends(get_db)):
    student_pk = _account_to_student_id(db, student_id)
    if not student_pk:
        return {
            "success": True,
            "data": {
                "has_notification": False,
                "evaluated_count": 0,
                "total_count": 0,
                "message": ""
            }
        }

    teacher_evals = db.query(Evaluation.submission_id).join(
        Submission, Evaluation.submission_id == Submission.id
    ).filter(Submission.student_id == student_pk, Evaluation.evaluator_type == "teacher").all()
    evaluated_ids = [e.submission_id for e in teacher_evals]
    all_ids = [s.id for s in db.query(Submission.id).filter(Submission.student_id == student_pk).all()]
    evaluated_count = len(set(evaluated_ids) & set(all_ids))

    return {
        "success": True,
        "data": {
            "has_notification": evaluated_count > 0,
            "evaluated_count": evaluated_count,
            "total_count": len(all_ids),
            "message": f"你有 {evaluated_count} 份作业已被教师评分" if evaluated_count > 0 else ""
        }
    }


@router.get("/job-match/{student_id}")
def get_job_match(student_id: int, db: Session = Depends(get_db)):
    """AI 岗位匹配推荐"""
    student_pk = _account_to_student_id(db, student_id)
    if not student_pk:
        return {"success": False, "error": "暂无评价数据"}

    submissions = db.query(
        Evaluation.dimension_scores, Evaluation.total_score
    ).join(Submission, Evaluation.submission_id == Submission.id).filter(
        Submission.student_id == student_pk,
        Evaluation.evaluator_type == "ai"
    ).all()

    if not submissions:
        return {"success": False, "error": "暂无评价数据"}

    dim_totals, dim_counts = {}, {}
    total_scores = []
    for scores, total in submissions:
        total_scores.append(float(total) if total else 0)
        if scores:
            for item in scores:
                name = item.get("name", "")
                score = item.get("score", 0)
                dim_totals[name] = dim_totals.get(name, 0) + score
                dim_counts[name] = dim_counts.get(name, 0) + 1

    dim_avg = {name: round(dim_totals[name] / dim_counts[name], 1) for name in dim_totals}
    overall_avg = round(sum(total_scores) / len(total_scores), 1)

    dim_text = "、".join([f"{k} {v}分" for k, v in dim_avg.items()])
    prompt = f"""你是职业规划专家。根据以下学生的实训成绩，推荐最适合的岗位方向：

学生情况：
- 提交次数：{len(submissions)}次
- 平均分：{overall_avg}
- 各维度平均分：{dim_text}

请返回JSON：
{{
    "job": "推荐岗位名称",
    "match": 匹配度百分比,
    "requirements": [
        {{"skill": "技能名", "level": "要求等级", "student_level": "学生当前等级", "gap": "差距描述"}}
    ],
    "advice": "针对性学习建议"
}}
只返回JSON。"""

    try:
        from app.utils.ai_evaluator import deepseek_client as client
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        result = response.choices[0].message.content
        if "```" in result:
            result = result.split("```")[1].split("```")[0]
        if result.startswith("json"):
            result = result[4:]
        import json
        data = json.loads(result.strip())
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}




@router.get("/teaching-advice")
def get_teaching_advice(class_id: int = 0, db: Session = Depends(get_db)):
        """AI 教学建议"""
        # 收集数据
        if class_id > 0:
            sub_ids = db.query(Submission.id).filter(Submission.class_id.like(f"%{class_id}%")).all()
            sub_id_list = [s[0] for s in sub_ids]
            if sub_id_list:
                avg_score = db.query(func.avg(Evaluation.total_score)).filter(
                    Evaluation.evaluator_type == "ai",
                    Evaluation.submission_id.in_(sub_id_list)
                ).scalar() or 0
                total_subs = len(sub_id_list)
                evals = db.query(Evaluation.dimension_scores).filter(
                    Evaluation.evaluator_type == "ai",
                    Evaluation.submission_id.in_(sub_id_list)
                ).all()
            else:
                return {"success": False, "error": "暂无数据"}
        else:
            avg_score = db.query(func.avg(Evaluation.total_score)).filter(
                Evaluation.evaluator_type == "ai").scalar() or 0
            total_subs = db.query(func.count(Submission.id)).scalar() or 0
            evals = db.query(Evaluation.dimension_scores).filter(Evaluation.evaluator_type == "ai").all()

        # 各维度平均分
        dim_totals, dim_counts = {}, {}
        for (scores,) in evals:
            if scores:
                for item in scores:
                    name = item.get("name", "")
                    score = item.get("score", 0)
                    dim_totals[name] = dim_totals.get(name, 0) + score
                    dim_counts[name] = dim_counts.get(name, 0) + 1

        dim_text = "、".join([f"{k} {round(v / dim_counts[k], 1)}分" for k, v in dim_totals.items()])

        prompt = f"""你是实训教学顾问。根据以下数据给出教学改进建议：

    总体情况：平均分 {round(float(avg_score), 1)}，共 {total_subs} 份提交
    各维度平均分：{dim_text}

    请返回JSON：
    {{"advice": "教学改进建议，100字以内，直击要点"}}
    只返回JSON。"""

        try:
            from app.utils.ai_evaluator import deepseek_client as client
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            result = response.choices[0].message.content
            if "```" in result:
                result = result.split("```")[1].split("```")[0]
            if result.startswith("json"):
                result = result[4:]
            import json
            data = json.loads(result.strip())
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

@router.get("/courses")
def get_courses(db: Session = Depends(get_db)):
    """获取所有已发布任务的课程名称"""
    courses = db.query(Task.title).filter(Task.status == "published").distinct().all()
    return {
        "success": True,
        "data": [{"name": c[0]} for c in courses if c[0]]
    }

@router.get("/student/{student_id}/growth")
def get_student_growth(student_id: int, db: Session = Depends(get_db)):
    """学生能力成长报告"""
    student_pk = _account_to_student_id(db, student_id)
    if not student_pk:
        return {"success": False, "error": "学生不存在或提交次数不足"}

    submissions = db.query(
        Evaluation.total_score, Evaluation.dimension_scores, Evaluation.comment,
        Submission.created_at
    ).join(Submission, Evaluation.submission_id == Submission.id).filter(
        Submission.student_id == student_pk,
        Evaluation.evaluator_type == "ai"
    ).order_by(Submission.created_at.asc()).all()

    if len(submissions) < 2:
        return {"success": False, "error": "提交次数不足，至少需要2次提交才能生成成长报告"}

    first = submissions[0]
    latest = submissions[-1]

    first_scores = {s["name"]: s["score"] for s in (first.dimension_scores or [])}
    latest_scores = {s["name"]: s["score"] for s in (latest.dimension_scores or [])}

    all_dims = set(list(first_scores.keys()) + list(latest_scores.keys()))

    changes = []
    for dim in all_dims:
        f_score = first_scores.get(dim, 0)
        l_score = latest_scores.get(dim, 0)
        changes.append({
            "name": dim,
            "first_score": f_score,
            "latest_score": l_score,
            "change": round(l_score - f_score, 1)
        })

    changes.sort(key=lambda x: x["change"], reverse=True)

    best_dim = changes[0] if changes else None
    worst_dim = changes[-1] if changes else None

    # AI 生成成长评语
    if best_dim and worst_dim:
        dim_text = "、".join([f"{c['name']}首次{c['first_score']}→最新{c['latest_score']}({'+' if c['change']>=0 else ''}{c['change']})" for c in changes])
        prompt = f"""你是实训学习顾问。根据学生能力成长数据给出鼓励性评语（80字以内）。

首次均分：{round(float(first.total_score),1)}，最新均分：{round(float(latest.total_score),1)}，提升{round(float(latest.total_score)-float(first.total_score),1)}分
各维度变化：{dim_text}
进步最大：{best_dim['name']}(+{best_dim['change']})，需加强：{worst_dim['name']}({'+' if worst_dim['change']>=0 else ''}{worst_dim['change']})
请返回JSON：{{"advice":"评语"}}只返回JSON。"""

        try:
            from app.utils.ai_evaluator import deepseek_client as client
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            result = response.choices[0].message.content
            if "```" in result: result = result.split("```")[1].split("```")[0]
            if result.startswith("json"): result = result[4:]
            import json as j
            ai_advice = j.loads(result.strip()).get("advice", "继续努力，每次提交都在进步！")
        except:
            ai_advice = "继续努力，每次提交都在进步！"
    else:
        ai_advice = "继续努力，每次提交都在进步！"

    return {
        "success": True,
        "data": {
            "first": {
                "total": round(float(first.total_score), 1),
                "scores": first_scores,
                "time": first.created_at.strftime("%Y-%m-%d %H:%M") if first.created_at else ""
            },
            "latest": {
                "total": round(float(latest.total_score), 1),
                "scores": latest_scores,
                "time": latest.created_at.strftime("%Y-%m-%d %H:%M") if latest.created_at else ""
            },
            "changes": changes,
            "best_dim": best_dim,
            "worst_dim": worst_dim,
            "total_change": round(float(latest.total_score) - float(first.total_score), 1),
            "total_count": len(submissions),
            "advice": ai_advice
        }
    }


@router.get("/student/{student_id}/summary")
def get_student_summary(student_id: int, db: Session = Depends(get_db)):
    """获取学生成绩汇总（用于班级成绩总览弹窗）"""
    # 原代码：db.query(User).filter(User.id == student_id).first()
    student_account_id = int(student_id)
    account = db.query(LoginAccount).filter(LoginAccount.id == student_account_id).first()
    student_row = db.query(Student).filter(Student.account_id == student_account_id).first()
    if not account or not student_row:
        return {"success": False, "error": "学生不存在"}
    student_pk = student_row.id

    submissions = db.query(Submission).filter(
        Submission.student_id == student_pk
    ).order_by(Submission.created_at.desc()).all()

    records = []
    ai_scores = []
    for sub in submissions:
        task = db.query(Task).filter(Task.id == sub.task_id).first()
        ai_eval = db.query(Evaluation).filter(
            Evaluation.submission_id == sub.id,
            Evaluation.evaluator_type == "ai"
        ).first()
        teacher_eval = db.query(Evaluation).filter(
            Evaluation.submission_id == sub.id,
            Evaluation.evaluator_type == "teacher"
        ).first()

        first_filename = sub.filename.split(',')[0] if sub.filename else ''

        records.append({
            "submission_id": sub.id,
            "task_title": task.title if task else "未知任务",
            "filename": first_filename,
            "time": sub.created_at.strftime("%Y-%m-%d %H:%M") if sub.created_at else "",
            "ai_score": float(ai_eval.total_score) if ai_eval else None,
            "teacher_score": float(teacher_eval.total_score) if teacher_eval else None,
        })

        if ai_eval:
            ai_scores.append(float(ai_eval.total_score))

    avg_ai = round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else 0

    # 维度聚合
    dim_totals = {}
    dim_counts = {}
    all_evals = db.query(Evaluation.dimension_scores, Evaluation.total_score).join(
        Submission, Evaluation.submission_id == Submission.id
    ).filter(Submission.student_id == student_pk, Evaluation.evaluator_type == "ai").all()

    for scores, total in all_evals:
        if scores:
            for item in scores:
                name = item.get("name", "")
                score = item.get("score", 0)
                dim_totals[name] = dim_totals.get(name, 0) + score
                dim_counts[name] = dim_counts.get(name, 0) + 1

    dim_text = "、".join([f"{k} {round(dim_totals[k]/dim_counts[k],1)}分" for k in dim_totals]) if dim_totals else "暂无数据"
    total_avg = round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else 0

    # 调用 AI 生成简短评语
    prompt = f"""你是教学助手。根据以下学生数据给出简短评价（50字内）：
提交次数：{len(ai_scores)}，AI平均分：{total_avg}，各维度均分：{dim_text}。
请返回JSON：{{"comment":"评语"}}只返回JSON。"""

    try:
        from app.utils.ai_evaluator import deepseek_client as client
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        result = response.choices[0].message.content
        if "```" in result:
            result = result.split("```")[1].split("```")[0]
        if result.startswith("json"):
            result = result[4:]
        import json
        ai_comment = json.loads(result.strip()).get("comment", "该生学习态度认真，继续努力！")
    except:
        ai_comment = "该生学习态度认真，继续努力！"

    # 返回 student_name / student_number：从 Student 表取
    student_name_out = student_row.real_name or account.username or ""
    student_number_out = student_row.student_no or ""

    return {
        "success": True,
        "data": {
            "student_name": student_name_out,
            "student_number": student_number_out,
            "records": records,
            "submit_count": len(submissions),
            "ai_avg": avg_ai,
            "ai_comment": ai_comment
        }
    }

@router.get("/activities")
def get_recent_activities(db: Session = Depends(get_db)):
    """获取最近动态（含学生、班级、任务、教师信息）"""
    activities = []

    # 最近5条提交记录
    # 旧：join(User, Submission.student_id == User.id)
    # 新：join(Student, Student.id == Submission.student_id)，然后 Student.account_id → LoginAccount
    submissions = db.query(
        Submission.id, Submission.filename, Submission.created_at,
        Submission.student_id, Submission.task_id, Submission.class_id,
        LoginAccount.real_name, Task.title
    ).join(Student, Student.id == Submission.student_id
    ).join(LoginAccount, LoginAccount.id == Student.account_id
    ).join(Task, Submission.task_id == Task.id
    ).order_by(Submission.created_at.desc()).limit(5).all()

    for s in submissions:
        class_name = "未知班级"
        if s.class_id:
            try:
                cids = [int(cid.strip()) for cid in str(s.class_id).split(',') if cid.strip()]
                if cids:
                    classes = db.query(Class).filter(Class.id.in_(cids)).all()
                    class_name = "、".join([c.name for c in classes]) or "未知班级"
            except:
                pass

        activities.append({
            "id": f"sub_{s.id}",
            "type": "submission",
            "student_name": s.real_name or "未知学生",
            "class_name": class_name,
            "task_title": s.title or "未知任务",
            "filename": s.filename.split(',')[0] if s.filename else '',
            "time": s.created_at.strftime("%m-%d %H:%M") if s.created_at else ""
        })

    # 最近3条任务发布记录
    # 旧：join(User, Task.created_by == User.id)
    # 新：join(Teacher, Teacher.id == Task.created_by)，然后 Teacher.account_id → LoginAccount
    tasks = db.query(
        Task.id, Task.title, Task.created_at, Task.created_by,
        LoginAccount.real_name
    ).join(Teacher, Teacher.id == Task.created_by
    ).join(LoginAccount, LoginAccount.id == Teacher.account_id
    ).order_by(Task.created_at.desc()).limit(3).all()

    for t in tasks:
        activities.append({
            "id": f"task_{t.id}",
            "type": "task_publish",
            "teacher_name": t.real_name or "未知教师",
            "task_title": t.title,
            "time": t.created_at.strftime("%m-%d %H:%M") if t.created_at else ""
        })

    # 按时间排序，取最近5条
    activities.sort(key=lambda x: x["time"], reverse=True)
    activities = activities[:5]

    return {"success": True, "data": activities}
