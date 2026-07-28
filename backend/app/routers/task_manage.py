import json
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.database import SessionLocal
from app.models.tables import Task, Submission, Evaluation, User
from app.models.class_models import ClassMember
from app.utils.ai_evaluator import deepseek_client as client
from app.models.class_models import ClassMember, Class

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])

UPLOAD_DIR = "uploads/templates"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class GenerateRequest(BaseModel):
    title: str
    difficulty: str = "普通"


class TaskCreate(BaseModel):
    title: str
    requirements: str
    criteria: str = "代码质量,功能完整性,文档规范性,界面设计"
    criteria_weights: str = "25,25,25,25"
    template_content: str = ""
    class_id: str = ""
    total_score: int = 100
    deadline: Optional[str] = None
    teacher_id: int = 0


@router.post("/generate")
def generate_task(req: GenerateRequest):
    difficulty_map = {
        "简单": "3个评分维度，权重偏功能完整性，实训要求200字左右，模板包含4个章节：一、项目概述 / 二、功能实现 / 三、核心代码 / 四、测试说明",
        "普通": "4个评分维度，权重均匀，实训要求250字左右，模板包含5个章节：一、项目概述 / 二、需求分析 / 三、功能实现 / 四、核心代码 / 五、测试用例",
        "困难": "5-6个评分维度，权重偏代码质量和算法，实训要求300字左右，模板包含6个章节：一、需求分析 / 二、技术方案 / 三、功能清单 / 四、核心代码 / 五、测试用例 / 六、总结展望"
    }

    prompt = f"""你是软件实训课程设计专家。请根据以下信息生成实训任务：

任务标题：{req.title}
难度等级：{req.difficulty}
{difficulty_map.get(req.difficulty, difficulty_map["普通"])}

请严格按JSON格式返回，必须包含 template 字段：
{{
    "requirements": "详细的实训要求，包含具体技术点、功能点、验收标准",
    "criteria": [
        {{"name": "维度名", "weight": 权重(百分比数字)}}
    ],
    "template": "成果物提交模板，每个章节用 ## 开头，如 ## 一、项目概述\\n请描述...\\n\\n## 二、功能实现\\n请列出..."
}}

只返回JSON，不要任何解释。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        result = response.choices[0].message.content

        if "```" in result:
            result = result.split("```")[1].split("```")[0]
        if result.startswith("json"):
            result = result[4:]
        result = result.strip()

        data = json.loads(result)

        if not data.get("template") or len(data.get("template", "").strip()) < 10:
            data["template"] = f"""## 一、项目概述
请简要描述项目背景、目标和整体架构

## 二、需求分析
请分析项目功能需求和技术要点

## 三、功能实现
请详细列出实现的功能点，每个功能附上关键代码片段

## 四、核心代码说明
请粘贴核心代码并添加注释说明

## 五、测试说明
请描述测试方法、测试用例和测试结果"""

        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/")
def create_task(req: TaskCreate, db: Session = Depends(get_db)):
    deadline = None
    if req.deadline and req.deadline != "string" and req.deadline.strip():
        try:
            deadline = datetime.strptime(req.deadline, "%Y-%m-%d %H:%M")
        except:
            try:
                deadline = datetime.strptime(req.deadline, "%Y-%m-%dT%H:%M:%S")
            except:
                pass

    template_path = None
    if req.template_content and req.template_content.strip():
        from docx import Document
        doc = Document()
        doc.add_heading(f"实训成果物 - {req.title}", 0)
        for line in req.template_content.split('\n'):
            line = line.strip()
            if line.startswith('## ') or line.startswith('# '):
                doc.add_heading(line.replace('#', '').strip(), level=2)
            elif line.startswith('- ') or line.startswith('* '):
                doc.add_paragraph(line, style='List Bullet')
            elif line:
                doc.add_paragraph(line)

        filename = f"task_template_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
        filepath = os.path.join(UPLOAD_DIR, filename)
        doc.save(filepath)
        template_path = filename

    task = Task(
        title=req.title,
        requirements=req.requirements,
        criteria=req.criteria,
        criteria_weights=req.criteria_weights,
        template_path=template_path,
        class_id=req.class_id if req.class_id and req.class_id.strip() else None,
        total_score=req.total_score,
        deadline=deadline,
        status="published",
        created_by=req.teacher_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"success": True, "data": {"id": task.id, "title": task.title}}


@router.get("/{task_id}/template")
def download_template(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.template_path:
        raise HTTPException(404, "该任务没有模板")

    filepath = os.path.join(UPLOAD_DIR, task.template_path)
    if not os.path.exists(filepath):
        raise HTTPException(404, "模板文件不存在")

    return FileResponse(
        filepath,
        filename=f"{task.title}_提交模板.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/my")
def get_my_tasks(teacher_id: int = 0, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.created_by == teacher_id).order_by(Task.created_at.desc()).all()
    all_class_ids = set()
    for t in tasks:
        if t.class_id:
            for cid in str(t.class_id).split(','):
                if cid.strip():
                    all_class_ids.add(int(cid.strip()))

    if all_class_ids:
        classes = db.query(Class).filter(Class.id.in_(all_class_ids)).all()
        class_map = {c.id: c.name for c in classes}
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "title": t.title,
                "requirements": t.requirements,
                "criteria": t.criteria,
                "criteria_weights": t.criteria_weights or "",
                "template_path": t.template_path,
                "class_names": ", ".join([class_map.get(int(cid.strip()), str(cid)) for cid in str(t.class_id).split(',') if cid.strip()]) if t.class_id else "不限",
                "total_score": t.total_score,
                "status": t.status,
                "deadline": str(t.deadline) if t.deadline else "",
                "created_at": str(t.created_at)
            }
            for t in tasks
        ]
    }


@router.get("/pending")
def get_pending_tasks(student_id: int = 0, db: Session = Depends(get_db)):
    members = db.query(ClassMember).filter(ClassMember.student_id == student_id).all()
    class_ids = [m.class_id for m in members]

    if not class_ids:
        return {"success": True, "data": []}

    all_tasks = db.query(Task).filter(Task.status == "published").order_by(Task.created_at.desc()).all()

    result = []
    for t in all_tasks:
        # 检查该任务是否关联了学生所在的班级
        if t.class_id:
            task_class_ids = [int(c.strip()) for c in str(t.class_id).split(',') if c.strip()]
            if not any(c in class_ids for c in task_class_ids):
                continue

        submitted = db.query(Submission).filter(
            Submission.task_id == t.id,
            Submission.student_id == student_id
        ).first()

        result.append({
            "id": t.id,
            "title": t.title,
            "requirements": t.requirements,
            "criteria": t.criteria,
            "criteria_weights": t.criteria_weights or "",
            "template_path": t.template_path,
            "class_id": t.class_id,
            "total_score": t.total_score,
            "deadline": str(t.deadline) if t.deadline else "",
            "submitted": submitted is not None,
            "submission_id": submitted.id if submitted else None,
            "created_at": str(t.created_at) if t.created_at else ""
        })

    return {"success": True, "data": result}

@router.get("/{task_id}/detail")
def task_detail(task_id: int, db: Session = Depends(get_db)):
    from app.models.class_models import Class

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")

    submissions = db.query(Submission).filter(Submission.task_id == task_id).all()

    all_class_ids = set()
    for sub in submissions:
        if sub.class_id:
            for cid in str(sub.class_id).split(','):
                if cid.strip():
                    all_class_ids.add(int(cid.strip()))

    class_map = {}
    if all_class_ids:
        classes = db.query(Class).filter(Class.id.in_(all_class_ids)).all()
        class_map = {c.id: c.name for c in classes}

    student_list = []
    for sub in submissions:
        ai_eval = db.query(Evaluation).filter(
            Evaluation.submission_id == sub.id,
            Evaluation.evaluator_type == "ai"
        ).first()
        teacher_eval = db.query(Evaluation).filter(
            Evaluation.submission_id == sub.id,
            Evaluation.evaluator_type == "teacher"
        ).first()
        student = db.query(User).filter(User.id == sub.student_id).first()

        class_names = "不限"
        if student:
            memberships = db.query(ClassMember).filter(ClassMember.student_id == student.id).all()
            if memberships:
                member_class_ids = [m.class_id for m in memberships]
                student_classes = db.query(Class).filter(Class.id.in_(member_class_ids)).all()
                class_names = "、".join([c.name for c in student_classes]) or "不限"

        student_list.append({
            "submission_id": sub.id,
            "student_id": sub.student_id,
            "student_name": student.real_name if student else "未知",
            "student_number": student.user_number if student else "",
            "filename": sub.filename,
            "submitted_at": str(sub.created_at) if sub.created_at else "",
            "class_name": class_names,
            "ai_score": float(ai_eval.total_score) if ai_eval else None,
            "ai_scores": ai_eval.dimension_scores if ai_eval else None,
            "ai_comment": ai_eval.comment if ai_eval else None,
            "ai_steps": ai_eval.step_completeness if ai_eval else None,
            "ai_issues": ai_eval.logic_issues if ai_eval else None,
            "teacher_score": float(teacher_eval.total_score) if teacher_eval else None,
            "is_scored": teacher_eval is not None,
        })

    # 统计放在循环外面
    unscored_count = sum(1 for s in student_list if not s["is_scored"])
    next_unscored_id = None
    for s in student_list:
        if not s["is_scored"]:
            next_unscored_id = s["submission_id"]
            break

    return {
        "success": True,
        "data": {
            "task": {
                "id": task.id,
                "title": task.title,
                "requirements": task.requirements,
                "criteria": task.criteria,
                "criteria_weights": task.criteria_weights or "",
                "template_path": task.template_path
            },
            "submissions": student_list,
            "unscored_count": unscored_count,
            "next_unscored_id": next_unscored_id
        }
    }


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    submissions = db.query(Submission).filter(Submission.task_id == task_id).all()
    for sub in submissions:
        db.query(Evaluation).filter(Evaluation.submission_id == sub.id).delete()
        db.delete(sub)
    db.delete(task)
    db.commit()
    return {"success": True, "message": "任务已删除"}

@router.get("/download/{submission_id}")
def download_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "提交记录不存在")
    if not submission.file_path or not os.path.exists(submission.file_path):
        raise HTTPException(404, "文件不存在")

    return FileResponse(
        submission.file_path,
        filename=submission.filename,
        media_type="application/octet-stream"
    )