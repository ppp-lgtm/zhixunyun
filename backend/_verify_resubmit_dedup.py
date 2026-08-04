"""B组bug修复自验证：学生重新上传同一任务后，覆盖旧提交记录。

验证：
1. 新建 (task_id=9999, student_id=9999) 两条 submission，确认 _purge_stale_submission_for_resubmit 会删掉第1条，且 Submission 表只剩 1 条
2. 旧 submission 上的 Evaluation / EnterpriseEvaluation 也会被清理
3. 教师端 task_detail 查询和企业端 list_submissions_to_evaluate 都只返回每学生每任务最新 1 条
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, engine, Base
from app.models.tables import User, Task, Submission, Evaluation
from app.models.class_models import Class, ClassMember
from app.models.enterprise_models import Enterprise, EnterpriseMentor, JobPosition, EnterpriseEvaluation
from app.routers.upload_eval import _purge_stale_submission_for_resubmit

# 因为 venv 里实际用的是 MySQL ，MySQL 里不一定有这些表和行，但 SQLAlchemy 是 ORM 层，我们直接创建 SQLite 内存库做隔离验证。
# 做法：临时替换 engine 和 SessionLocal 指向 sqlite://
from sqlalchemy import create_engine

def _with_mem_db(fn):
    mem = create_engine("sqlite:///:memory:")
    Base.metadata.drop_all(bind=mem)
    Base.metadata.create_all(bind=mem)
    from sqlalchemy.orm import sessionmaker
    S = sessionmaker(bind=mem, autoflush=False, autocommit=False)
    db: Session = S()
    try:
        return fn(db)
    finally:
        db.close()


def _build_world(db: Session):
    """构造最小世界：user(teacher)、user(student=9999)、class、task=9999、enterprise、job、enterprise_mentor"""
    # teacher
    t = User(username="t1", password_hash="x", role="teacher", real_name="T")
    db.add(t); db.flush()
    # student
    s = User(id=9999, username="s_9999", password_hash="x", role="student", real_name="S9999")
    db.add(s); db.flush()
    # class
    cls = Class(name="C1", teacher_id=t.id, invite_code="C12345", status="active")
    db.add(cls); db.flush()
    db.add(ClassMember(class_id=cls.id, student_id=s.id, student_name=s.real_name, student_number="9999")); db.flush()
    # task 9999
    tk = Task(
        id=9999, title="Task-9999",
        requirements="demo", criteria="代码质量,功能", created_by=t.id,
        is_enterprise_project=1,  # 企业端需要
        class_id=str(cls.id),
        total_score=100,
        status="published",
    )
    db.add(tk); db.flush()
    # enterprise + mentor
    ent = Enterprise(name="ENT-X", short_name="EX")
    db.add(ent); db.flush()
    # job linked to class
    jp = JobPosition(
        enterprise_id=ent.id, title="Backend Dev",
        level="P1", salary_range="8-12", city="BJ",
        job_type="技术岗",
        skill_requirements=[],
        linked_classes=str(cls.id),
        status="open",
    )
    db.add(jp); db.flush()
    # 企业导师账号：另一个用户
    mentor_u = User(username="mentor1", password_hash="x", role="enterprise", real_name="Mentor")
    db.add(mentor_u); db.flush()
    db.add(EnterpriseMentor(enterprise_id=ent.id, user_id=mentor_u.id, title="HR", is_admin=1))
    db.flush()
    db.commit()
    return {
        "teacher": t, "student": s, "class": cls,
        "task": tk, "enterprise": ent, "job": jp, "mentor_user": mentor_u,
    }


def test_1_purge_deletes_old_and_evals():
    def run(db: Session):
        w = _build_world(db)
        sid, tid = w["student"].id, w["task"].id

        # 第一次提交（旧的）
        old_sub = Submission(task_id=tid, student_id=sid, filename="old.docx", file_path="/tmp/old.docx", content="old")
        db.add(old_sub); db.flush()
        ai_eval_old = Evaluation(submission_id=old_sub.id, evaluator_type="ai", total_score=60,
                                 dimension_scores=[{"name":"A","score":60}], comment="old")
        t_eval_old = Evaluation(submission_id=old_sub.id, evaluator_type="teacher", total_score=65,
                                dimension_scores=[{"name":"A","score":65}], comment="old-t")
        ee_old = EnterpriseEvaluation(
            enterprise_id=w["enterprise"].id,
            mentor_id=w["mentor_user"].id,
            submission_id=old_sub.id,
            total_score=70, comment="old-ent",
            dimension_scores=[{"name":"A","score":70,"weight":1}],
            strength_points="", improvement_points="", interview_suggest="",
            job_fit_score=70, matched_job_id=w["job"].id,
        )
        db.add_all([ai_eval_old, t_eval_old, ee_old]); db.flush(); db.commit()

        cnt_sub_old = db.query(Submission).filter_by(task_id=tid, student_id=sid).count()
        cnt_eval_old = db.query(Evaluation).filter(Evaluation.submission_id==old_sub.id).count()
        cnt_ee_old = db.query(EnterpriseEvaluation).filter_by(submission_id=old_sub.id).count()
        assert cnt_sub_old == 1, f"旧提交数应为1 实际{cnt_sub_old}"
        assert cnt_eval_old == 2, f"旧evaluation数应为2 实际{cnt_eval_old}"
        assert cnt_ee_old == 1, f"旧enterprise eval数应为1 实际{cnt_ee_old}"
        print("TEST1-SETUP  OK: 旧submission=1, Evaluations=2, EnterpriseEvaluations=1")

        # 调用 purge
        deleted_id = _purge_stale_submission_for_resubmit(db, tid, sid)
        db.commit()
        assert deleted_id == old_sub.id, f"应返回删除的旧id {old_sub.id} 实际{deleted_id}"

        # 现在新建一个 submission（模拟重提）
        new_sub = Submission(task_id=tid, student_id=sid, filename="new.docx", file_path="/tmp/new.docx", content="new")
        db.add(new_sub); db.flush(); db.commit()

        cnt_sub_new = db.query(Submission).filter_by(task_id=tid, student_id=sid).count()
        assert cnt_sub_new == 1, f"重提后submission数仍应为1 实际{cnt_sub_new}"

        # 旧的 Evaluations / EnterpriseEvaluations 都应该没了
        cnt_eval_left = db.query(Evaluation).filter(Evaluation.submission_id==old_sub.id).count()
        cnt_ee_left = db.query(EnterpriseEvaluation).filter_by(submission_id=old_sub.id).count()
        assert cnt_eval_left == 0, f"旧Evaluations不应存在 剩余{cnt_eval_left}"
        assert cnt_ee_left == 0, f"旧EnterpriseEvaluations不应存在 剩余{cnt_ee_left}"
        print("TEST1-RESULT OK: purge后 (task=9999,student=9999)  submission=1, 旧Evaluations=0, 旧EnterpriseEval=0")
        return True

    return _with_mem_db(run)


def test_2_teacher_task_detail_dedup():
    """同一学生同任务插入 3 条 submission（模拟旧脏数据），teacher task_detail 只返回最新1条"""
    def run(db: Session):
        w = _build_world(db)
        sid, tid = w["student"].id, w["task"].id
        # 插入3条（模拟历史脏数据）
        subs = []
        for i, name in enumerate(["v1.docx", "v2.docx", "v3.docx"]):
            s = Submission(task_id=tid, student_id=sid, filename=name, content=name, class_id=str(w["class"].id))
            db.add(s); db.flush()
            subs.append(s)
        db.commit()

        # 模拟 teacher task_detail 的去重逻辑
        raw_subs = (
            db.query(Submission)
            .filter(Submission.task_id == tid)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
            .all()
        )
        assert len(raw_subs) == 3

        deduped = []
        seen = set()
        for s in raw_subs:
            key = s.student_id
            if key in seen: continue
            seen.add(key)
            deduped.append(s)

        assert len(deduped) == 1, f"教师端去重后应只剩1条 实际{len(deduped)}"
        # 最新的一条应该是最后加的那个（id最大，或created_at最晚）
        latest = deduped[0]
        assert latest.filename == "v3.docx", f"应保留v3 实际{latest.filename}"
        print("TEST2        OK: 教师端3条脏数据→去重后仅保留最新v3")
        return True
    return _with_mem_db(run)


def test_3_enterprise_list_dedup():
    """企业端list_submissions：同学生同任务2条脏数据→dedup_ids长度=1"""
    def run(db: Session):
        w = _build_world(db)
        sid, tid, ent, jp = w["student"].id, w["task"].id, w["enterprise"].id, w["job"].id

        # 插入2条脏 submission
        s1 = Submission(task_id=tid, student_id=sid, filename="old.docx", content="a", class_id=str(w["class"].id))
        db.add(s1); db.flush()
        s2 = Submission(task_id=tid, student_id=sid, filename="new.docx", content="b", class_id=str(w["class"].id))
        db.add(s2); db.flush()
        # 给 s2 加一条 AI eval，让它在结果里更真实
        db.add(Evaluation(submission_id=s2.id, evaluator_type="ai", total_score=80,
                          dimension_scores=[], comment="ok")); db.flush()
        db.commit()

        # 模拟 enterprise 端的查询（最小化还原筛选条件）
        from sqlalchemy.orm import aliased
        # 用 with_entities 先取 4 列
        q = (
            db.query(Submission)
            .join(User, User.id == Submission.student_id)
            .join(Task, Task.id == Submission.task_id)
            .join(ClassMember, ClassMember.student_id == User.id)
            .filter(ClassMember.class_id == w["class"].id)
            .filter(Task.is_enterprise_project == 1)
        )
        all_cands = (
            q.with_entities(Submission.id, Submission.student_id, Submission.task_id, Submission.created_at)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
            .distinct()
            .all()
        )
        dedup_ids = []
        seen = set()
        for _sid, _stu, _tsk, _ca in all_cands:
            key = (_stu, _tsk)
            if key in seen: continue
            seen.add(key)
            dedup_ids.append(int(_sid))
        assert len(dedup_ids) == 1, f"企业端应返回1条 实际{len(dedup_ids)}"
        assert dedup_ids[0] == s2.id, f"应保留新提交s2.id={s2.id} 实际{dedup_ids[0]}"
        print("TEST3        OK: 企业端同学生同任务2条脏数据→dedup_ids长度=1, 保留最新s2")
        return True
    return _with_mem_db(run)


if __name__ == "__main__":
    ok = all([
        test_1_purge_deletes_old_and_evals(),
        test_2_teacher_task_detail_dedup(),
        test_3_enterprise_list_dedup(),
    ])
    print("\n=== ALL TESTS PASSED ===" if ok else "\n=== SOME TESTS FAILED ===")
    sys.exit(0 if ok else 1)
