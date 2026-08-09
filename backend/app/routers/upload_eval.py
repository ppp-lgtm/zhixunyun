from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Callable
from app.services.file_parser import parse_file
from app.services.code_analyzer import (
    analyze_code_files,
    to_evaluation_dimensions,
    to_logic_issues,
    detect_plagiarism,
)
from app.services.step_extractor import (
    extract_step_progress,
    progress_to_step_completeness,
    progress_extra_issues,
)
from app.utils.ai_evaluator import evaluate, check_completeness, evaluate_step_mode
from app.models.database import SessionLocal
from app.models.tables import Task, Submission, Evaluation, Student
from app.models.enterprise_models import EnterpriseEvaluation
import os, uuid, re, json, time, threading, queue
from datetime import datetime


router = APIRouter(prefix="/api/upload-eval", tags=["上传并评价"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# ID 转换辅助：前端传入的 student_id (login_accounts.id) → students.pk
# ============================================================

def _account_to_student_pk(db: Session, account_id: int) -> Optional[int]:
    if not account_id or account_id <= 0:
        return None
    row = db.query(Student).filter(Student.account_id == int(account_id)).first()
    return row.id if row else None


def _purge_stale_submission_for_resubmit(db: Session, task_id: int, student_pk: int) -> Optional[int]:
    """学生在同一任务下重新上传时：清理旧的 submission + 所有关联评价（AI/教师/企业），
    确保 (task_id, student_id) 在 Submission 表里始终只有最新一条。

    注意：参数 student_pk 必须是 students.id（PK），不能传 login_accounts.id。
    返回被删除的旧 submission.id（用于抄袭检测里排除自己），没旧记录返回 None。
    """
    if not task_id or task_id <= 0 or not student_pk or student_pk <= 0:
        return None
    old = (
        db.query(Submission)
        .filter(Submission.task_id == task_id)
        .filter(Submission.student_id == student_pk)
        .order_by(Submission.created_at.asc(), Submission.id.asc())
        .all()
    )
    if not old:
        return None
    deleted_old_id = None
    for sub in old:
        db.query(Evaluation).filter(Evaluation.submission_id == sub.id).delete(synchronize_session=False)
        db.query(EnterpriseEvaluation).filter(EnterpriseEvaluation.submission_id == sub.id).delete(
            synchronize_session=False
        )
        if deleted_old_id is None:
            deleted_old_id = sub.id
        db.delete(sub)
    try:
        db.flush()
    except Exception:
        db.rollback()
    return deleted_old_id


@router.post("/")
async def upload_and_evaluate(
    files: List[UploadFile] = File(...),
    task_requirements: str = Form("请完成实训任务"),
    criteria: str = Form("代码质量,功能完整性,文档规范性,界面设计"),
    student_id: int = Form(0),
    task_id: int = Form(0),
    db: Session = Depends(get_db)
):
    all_texts = []
    filenames = []
    save_path = ""

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_name = f"{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        save_path = os.path.join(UPLOAD_DIR, save_name)

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        parse_result = await parse_file(save_path)

        if parse_result.get("success"):
            text = parse_result.get("text", "")
            if parse_result.get("type") == "image":
                all_texts.append(f"[图片文件: {file.filename}]")
            else:
                all_texts.append(text)
            filenames.append(file.filename)

    combined_text = "\n\n".join(all_texts)
    criteria_list = [c.strip() for c in criteria.split(",")]

    # ID 转换：student_id (login_accounts.id) → student_pk (students.id)
    student_pk = _account_to_student_pk(db, student_id)
    student_for_submission = student_pk if student_pk else None

    class_id = None
    if task_id > 0:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            if task.criteria:
                criteria_list = [c.strip() for c in task.criteria.split(",")]
            if task.requirements:
                task_requirements = task.requirements
            class_id = task.class_id

    eval_result = evaluate(task_requirements, combined_text, criteria_list)
    completeness = check_completeness(task_requirements, combined_text)

    task_obj = None
    if task_id > 0:
        task_obj = db.query(Task).filter(Task.id == task_id).first()
    if not task_obj:
        task_obj = Task(
            title="实训任务",
            requirements=task_requirements,
            criteria=",".join(criteria_list),
            status="published"
        )
        db.add(task_obj)
        db.commit()
        db.refresh(task_obj)

    if student_for_submission:
        _purge_stale_submission_for_resubmit(db, task_obj.id, student_for_submission)

    submission = Submission(
        task_id=task_obj.id,
        student_id=student_for_submission,
        class_id=class_id,
        filename=", ".join(filenames),
        file_path=save_path,
        content=combined_text[:5000]
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    evaluation = Evaluation(
        submission_id=submission.id,
        evaluator_type="ai",
        total_score=eval_result["total"],
        dimension_scores=eval_result["scores"],
        comment=eval_result["comment"],
        step_completeness=completeness.get("steps", []),
        logic_issues=completeness.get("issues", [])
    )
    db.add(evaluation)
    db.commit()

    return {
        "success": True,
        "submission_id": submission.id,
        "filename": ", ".join(filenames),
        "content": combined_text[:500],
        "evaluation": eval_result,
        "completeness": completeness
    }


_CODE_EXT_MARKERS = (".py", ".java", ".cpp", ".cc", ".cxx", ".c++", ".c",
                    ".h", ".hpp", ".hh", ".hxx", ".zip")


def _looks_like_code(filename: str) -> bool:
    if not filename:
        return False
    low = filename.lower()
    return any(low.endswith(ext) for ext in _CODE_EXT_MARKERS)


def _code_files_to_steps(files) -> list:
    """把源码文件列表转成 step_completeness 的形状（对齐 check_completeness 返回的 steps）"""
    steps = []
    if not files:
        return steps
    for i, f in enumerate(files, 1):
        fn = f.get("filename") or f"file_{i}"
        content_len = len((f.get("content") or "").strip())
        status = "passed" if content_len > 0 else "missing"
        detail = f"{f.get('ext','?').lstrip('.').upper()} 文件，代码字符数 {content_len}"
        steps.append({
            "index": i,
            "name": f"文件解析: {fn}",
            "status": status,
            "detail": detail,
        })
    return steps


@router.post("/code")
async def upload_code_and_evaluate(
    files: List[UploadFile] = File(...),
    task_requirements: str = Form("请完成实训代码任务，可上传 .py/.java/.cpp 单文件或 zip 多文件"),
    criteria: str = Form("代码质量,功能完整性,文档规范性,界面设计"),
    student_id: int = Form(0),
    task_id: int = Form(0),
    check_plagiarism: bool = Form(True),
    db: Session = Depends(get_db),
):
    """代码链路端点：解析源码→静态指标→抄袭检测→写入 submissions/evaluations 表。
    返回结构对齐原 `/` 端点，额外附带 code_analysis 字段（包含指标表/雷同对）。
    """
    all_files: list = []
    all_images: List[Dict[str, Any]] = []
    filenames = []
    save_paths = []
    last_parse = None

    # ID 转换
    student_pk = _account_to_student_pk(db, student_id)
    student_for_submission = student_pk if student_pk else None

    for file in files:
        raw_name = file.filename or "upload"
        ext = os.path.splitext(raw_name)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_base = re.sub(r"[^\w\u4e00-\u9fa5.\-]+", "_", raw_name)[:80] or "upload"
        save_name = f"code_{timestamp}_{uuid.uuid4().hex[:8]}__{safe_base}" if ext.lower() in {".png",".jpg",".jpeg"} else f"code_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        save_path = os.path.join(UPLOAD_DIR, save_name)

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        parse_result = await parse_file(save_path)
        if not parse_result.get("success"):
            if _looks_like_code(raw_name):
                raise HTTPException(status_code=400, detail=f"代码文件解析失败: {parse_result.get('error') or '未知原因'}")
            continue

        last_parse = parse_result
        save_paths.append(save_path)
        filenames.append(raw_name)
        all_files.extend(parse_result.get("files") or [])
        for img in parse_result.get("images") or []:
            entry = dict(img)
            entry.setdefault("filename", img.get("name") or "image")
            entry.setdefault("path", img.get("path") or img.get("file_path"))
            all_images.append(entry)

    if not all_files:
        raise HTTPException(
            status_code=400,
            detail="未解析到任何源码文件。请上传 .py/.java/.cpp/.c/.h/.zip 代码文件。",
        )

    code_input = [(f.get("filename") or f"file_{i+1}", f.get("content") or "")
                  for i, f in enumerate(all_files)]
    archive = analyze_code_files(code_input)
    sm = archive.get("summary_metrics") or {}

    top_pair = None
    if check_plagiarism and task_id > 0:
        others: dict = {}
        other_subs = (
            db.query(Submission)
            .filter(Submission.task_id == task_id)
            .filter(Submission.id != 0)
            .filter(Submission.filename.like("%.py%") | Submission.filename.like("%.java%")
                    | Submission.filename.like("%.cpp%") | Submission.filename.like("%.zip%")
                    | Submission.filename.like("%.c%") | Submission.filename.like("%.h%"))
            .all()
        )
        for sub in other_subs:
            if not sub or not sub.file_path or not os.path.exists(sub.file_path):
                continue
            try:
                pr = await parse_file(sub.file_path)
                if not pr.get("success"):
                    continue
                of = pr.get("files") or []
                if not of:
                    continue
                inp = [(f.get("filename") or f"o{sub.id}_{i}", f.get("content") or "")
                       for i, f in enumerate(of)]
                others[sub.id] = analyze_code_files(inp)
            except Exception:
                continue
        current_key = f"stu_{student_id or 'current'}"
        all_for_detect = dict(others)
        all_for_detect[current_key] = archive
        plag = detect_plagiarism(all_for_detect, threshold=0.85)
        if plag:
            top_pair = None
            for p in plag:
                a, b = str(p.get("student_id_a", "")), str(p.get("student_id_b", ""))
                if current_key in (a, b):
                    other_id = b if a == current_key else a
                    tp = dict(p)
                    if str(tp.get("student_id_a")) == current_key:
                        tp["student_id_a"] = f"当前提交"
                        tp["student_id_b"] = other_id
                    else:
                        tp["student_id_a"] = other_id
                        tp["student_id_b"] = f"当前提交"
                    top_pair = tp
                    break
            if top_pair is None and plag:
                p = plag[0]
                top_pair = {
                    "student_id_a": p.get("student_id_a"),
                    "student_id_b": p.get("student_id_b"),
                    "similarity": p.get("similarity"),
                    "severity": p.get("severity"),
                    "note": "(同任务其他提交对) " + str(p.get("note", "")),
                }

    eval_result = to_evaluation_dimensions(archive, top_pair=top_pair)
    issues = to_logic_issues(archive, top_pair=top_pair)
    steps = _code_files_to_steps(all_files)

    step_progress: Optional[Dict[str, Any]] = None
    if all_images:
        try:
            step_progress = extract_step_progress(task_requirements or "", all_images)
            extra_sc = progress_to_step_completeness(step_progress or {})
            if extra_sc:
                index_map = {s.get("index"): s for s in steps if isinstance(s, dict) and s.get("index")}
                merged_steps = []
                for s in extra_sc:
                    if s.get("index") in index_map:
                        old = dict(index_map[s["index"]])
                        merged_detail = old.get("detail", "")
                        if merged_detail and s.get("detail"):
                            merged_detail = f"{merged_detail}；图片：{s['detail']}"
                        elif s.get("detail"):
                            merged_detail = f"图片：{s['detail']}"
                        old["detail"] = merged_detail
                        if s.get("source_image"):
                            old["source_image"] = s["source_image"]
                        old["status"] = (
                            "passed"
                            if (old.get("status") == "passed" or s.get("status") == "passed")
                            else (s.get("status") or old.get("status") or "missing")
                        )
                        merged_steps.append(old)
                    else:
                        merged_steps.append(dict(s))
                extra_indexes = {s.get("index") for s in extra_sc if isinstance(s, dict)}
                for s in steps:
                    if isinstance(s, dict) and s.get("index") not in extra_indexes:
                        merged_steps.append(s)
                merged_steps.sort(key=lambda x: int(x.get("index") or 0))
                steps = merged_steps
            extra_is = progress_extra_issues(step_progress or {})
            if extra_is:
                exist_types = {i.get("type") for i in issues if isinstance(i, dict)}
                for i in extra_is:
                    if i.get("type") not in exist_types:
                        issues.append(i)
        except Exception as _e_d2:
            issues.append({
                "type": "step_progress_error",
                "title": "步骤进度解析异常（不影响代码得分）",
                "detail": f"{type(_e_d2).__name__}: {_e_d2}",
            })

    class_id = None
    if task_id > 0:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            if task.criteria:
                pass
            if task.requirements:
                task_requirements = task.requirements
            class_id = task.class_id

    task_obj = None
    if task_id > 0:
        task_obj = db.query(Task).filter(Task.id == task_id).first()
    if not task_obj:
        task_obj = Task(
            title="实训代码任务",
            requirements=task_requirements,
            criteria=criteria,
            status="published",
        )
        db.add(task_obj)
        db.commit()
        db.refresh(task_obj)

    if student_for_submission:
        _purge_stale_submission_for_resubmit(db, task_obj.id, student_for_submission)

    save_path = save_paths[-1] if save_paths else ""
    combined_text = last_parse.get("text", "") if last_parse else ""
    submission = Submission(
        task_id=task_obj.id,
        student_id=student_for_submission,
        class_id=class_id,
        filename=", ".join(filenames),
        file_path=save_path,
        content=combined_text[:5000],
    )
    db.add(submission)
    try:
        db.flush()
        db.refresh(submission)
    except Exception as _exc:
        db.rollback()
        submission.student_id = None
        db.add(submission)
        db.flush()
        db.refresh(submission)
    db.commit()
    try:
        db.refresh(submission)
    except Exception:
        pass

    if top_pair and ("当前提交" not in str(top_pair.get("student_id_a", "")) +
                     str(top_pair.get("student_id_b", ""))):
        sid = str(submission.id)
        if str(top_pair.get("student_id_a")) == sid or str(top_pair.get("student_id_b")) == sid:
            top_pair = None

    evaluation = Evaluation(
        submission_id=submission.id,
        evaluator_type="ai",
        total_score=float(eval_result.get("total", 0.0)),
        dimension_scores=eval_result.get("scores", []),
        comment=eval_result.get("comment", ""),
        step_completeness=steps,
        logic_issues=issues,
    )
    db.add(evaluation)
    db.commit()

    return {
        "success": True,
        "submission_id": submission.id,
        "filename": ", ".join(filenames),
        "content": combined_text[:500],
        "evaluation": {
            "scores": eval_result.get("scores", []),
            "total": eval_result.get("total", 0.0),
            "comment": eval_result.get("comment", ""),
            "from_code_analyzer": True,
        },
        "completeness": {
            "steps": steps,
            "issues": issues,
        },
        "code_analysis": {
            "summary_metrics": sm,
            "files": [
                {
                    "filename": f.get("filename"),
                    "language": f.get("language"),
                    "metrics": f.get("metrics"),
                }
                for f in archive.get("files", [])
            ],
            "top_plagiarism_pair": top_pair,
            "step_progress": step_progress,
            "images_collected": len(all_images),
        },
    }


_IMG_EXTS = {".png", ".jpg", ".jpeg"}


@router.post("/step")
async def upload_step_evidence_and_evaluate(
    files: List[UploadFile] = File(None),
    task_requirements: str = Form(""),
    criteria: str = Form("代码质量,功能完整性,文档规范性,界面设计"),
    student_id: int = Form(0),
    task_id: int = Form(0),
    step_index: int = Form(0),
    step_text: str = Form(""),
    check_plagiarism: bool = Form(False),
    submission_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """E1：分步实训提交端点。"""
    if step_index and step_index < 0:
        step_index = 0

    # ID 转换
    student_pk = _account_to_student_pk(db, student_id)
    student_for_submission = student_pk if student_pk else None

    all_files: list = []
    all_images: List[Dict[str, Any]] = []
    filenames = []
    save_paths = []
    last_parse = None

    if files:
        for file in files:
            raw_name = file.filename or "upload"
            ext = os.path.splitext(raw_name)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_base = re.sub(r"[^\w\u4e00-\u9fa5.\-]+", "_", raw_name)[:80] or "upload"
            if ext.lower() in _IMG_EXTS:
                save_name = f"step_img_{timestamp}_{uuid.uuid4().hex[:6]}__{safe_base}"
            else:
                save_name = f"step_{timestamp}_{uuid.uuid4().hex[:6]}{ext}"
            save_path = os.path.join(UPLOAD_DIR, save_name)

            content = await file.read()
            with open(save_path, "wb") as f:
                f.write(content)

            parse_result = await parse_file(save_path)
            if not parse_result.get("success"):
                if ext.lower() not in _IMG_EXTS and _looks_like_code(raw_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"证据文件解析失败: {parse_result.get('error') or '未知原因'}",
                    )
                if ext.lower() in _IMG_EXTS:
                    all_images.append({"filename": raw_name, "path": save_path, "name": raw_name})
                continue

            last_parse = parse_result
            save_paths.append(save_path)
            filenames.append(raw_name)
            all_files.extend(parse_result.get("files") or [])
            for img in parse_result.get("images") or []:
                entry = dict(img)
                entry.setdefault("filename", img.get("name") or "image")
                entry.setdefault("path", img.get("path") or img.get("file_path"))
                all_images.append(entry)

    class_id = None
    if task_id > 0:
        task_obj = db.query(Task).filter(Task.id == task_id).first()
        if task_obj:
            if task_obj.criteria:
                criteria = task_obj.criteria
            if task_obj.requirements:
                task_requirements = task_obj.requirements
            class_id = task_obj.class_id
    if task_id <= 0 or (not locals().get("task_obj") and task_id <= 0):
        task_obj = None
    if not task_obj:
        task_obj = Task(
            title=f"分步实训_{datetime.now().strftime('%Y%m%d')}",
            requirements=task_requirements or "分步实训任务",
            criteria=criteria,
            status="published",
        )
        db.add(task_obj)
        db.commit()
        db.refresh(task_obj)

    criteria_list = [c.strip() for c in (criteria or "").split(",") if c.strip()]

    submission: Optional[Submission] = None
    if submission_id and submission_id > 0:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission is None:
        if student_for_submission:
            _purge_stale_submission_for_resubmit(db, task_obj.id, student_for_submission)
        combined_text_init = (last_parse or {}).get("text", "") or ""
        submission = Submission(
            task_id=task_obj.id,
            student_id=student_for_submission,
            class_id=class_id,
            filename="",
            file_path=save_paths[-1] if save_paths else "",
            content=combined_text_init[:5000],
            step_evidences=[],
        )
        db.add(submission)
        try:
            db.flush()
            db.refresh(submission)
        except Exception:
            db.rollback()
            submission.student_id = None
            db.add(submission)
            db.flush()
            db.refresh(submission)
        db.commit()
        try:
            db.refresh(submission)
        except Exception:
            pass

    existing_evs = (submission.step_evidences or []) if isinstance(submission.step_evidences, list) else []
    existing_map: Dict[int, Dict[str, Any]] = {}
    for e in existing_evs:
        if not isinstance(e, dict):
            continue
        si = e.get("step_index")
        try:
            si = int(si)
        except Exception:
            si = None
        if si and si >= 1:
            existing_map[si] = e

    this_si = int(step_index) if step_index and step_index >= 1 else 0
    prev = existing_map.get(this_si, {})
    merged_files: List[Dict[str, Any]] = list(prev.get("files") or [])
    merged_images: List[Dict[str, Any]] = list(prev.get("images") or [])
    merged_ocr_texts: List[str] = list(prev.get("ocr_texts") or [])
    for f in all_files:
        merged_files.append({
            "filename": f.get("filename"),
            "path": f.get("path"),
            "ext": f.get("ext"),
            "content": (f.get("content") or "")[:2000],
        })
    for img in all_images:
        merged_images.append({"filename": img.get("filename"), "path": img.get("path")})
        ocr = img.get("ocr_text") or img.get("text")
        if ocr:
            merged_ocr_texts.append(str(ocr)[:2000])

    seen_files = set()
    deduped_files = []
    for mf in merged_files:
        key = (mf.get("filename") or "", mf.get("path") or "")
        if key in seen_files:
            continue
        seen_files.add(key)
        deduped_files.append(mf)
    seen_images = set()
    deduped_images = []
    for mi in merged_images:
        key = (mi.get("filename") or "", mi.get("path") or "")
        if key in seen_images:
            continue
        seen_images.add(key)
        deduped_images.append(mi)

    existing_map[this_si] = {
        "step_index": this_si,
        "files": deduped_files,
        "images": deduped_images,
        "ocr_texts": merged_ocr_texts,
        "content": (prev.get("content") or "") + (
            ("\n" + step_text) if step_text and step_text != (prev.get("content") or "") else ""
        ) if this_si in existing_map else (step_text or ""),
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }
    new_evidences = [existing_map[k] for k in sorted(existing_map.keys())]
    submission.step_evidences = new_evidences
    ev_filenames = []
    all_ev_content_parts = []
    last_p = submission.file_path or (save_paths[-1] if save_paths else "")
    for ev in new_evidences:
        for f in (ev.get("files") or []):
            ev_filenames.append(f.get("filename") or "?")
            if f.get("content"):
                all_ev_content_parts.append(f"## 步骤{ev.get('step_index')} 文件 {f.get('filename')}:\n{f['content']}")
        if ev.get("content"):
            all_ev_content_parts.append(f"## 步骤{ev.get('step_index')} 说明:\n{ev['content']}")
        for img in (ev.get("images") or []):
            ev_filenames.append(img.get("filename") or "img")
    if filenames:
        ev_filenames = list(dict.fromkeys(ev_filenames + filenames))
    if ev_filenames:
        submission.filename = ", ".join(ev_filenames)[:200]
    if all_ev_content_parts:
        submission.content = ("\n\n".join(all_ev_content_parts))[:5000]
    if save_paths:
        last_p = save_paths[-1]
    if last_p:
        submission.file_path = last_p
    try:
        db.commit()
        db.refresh(submission)
    except Exception:
        db.rollback()

    archive = None
    sm = {}
    top_pair = None
    files_for_code = [(f.get("filename") or f"f_{i+1}", f.get("content") or "")
                      for i, f in enumerate(deduped_files)]
    if files_for_code:
        try:
            archive = analyze_code_files(files_for_code)
            sm = archive.get("summary_metrics") or {}
        except Exception:
            archive = None
        if check_plagiarism and task_id > 0 and archive:
            others: dict = {}
            other_subs = (
                db.query(Submission)
                .filter(Submission.task_id == task_id)
                .filter(Submission.id != submission.id)
                .filter(Submission.filename.like("%.py%") | Submission.filename.like("%.java%")
                        | Submission.filename.like("%.cpp%") | Submission.filename.like("%.zip%")
                        | Submission.filename.like("%.c%") | Submission.filename.like("%.h%"))
                .all()
            )
            for sub in other_subs:
                if not sub or not sub.file_path or not os.path.exists(sub.file_path):
                    continue
                try:
                    pr = await parse_file(sub.file_path)
                    if not pr.get("success"):
                        continue
                    of = pr.get("files") or []
                    if not of:
                        continue
                    inp = [(f.get("filename") or f"o{sub.id}_{i}", f.get("content") or "")
                           for i, f in enumerate(of)]
                    others[sub.id] = analyze_code_files(inp)
                except Exception:
                    continue
            all_for_detect = dict(others)
            all_for_detect["me"] = archive
            plag = detect_plagiarism(all_for_detect, threshold=0.85)
            if plag:
                for p in plag:
                    a, b = str(p.get("student_id_a", "")), str(p.get("student_id_b", ""))
                    if "me" in (a, b):
                        top_pair = dict(p)
                        if a == "me":
                            top_pair["student_id_a"] = "当前提交"
                        else:
                            top_pair["student_id_b"] = "当前提交"
                        break
                if top_pair is None:
                    top_pair = dict(plag[0])
                    top_pair["note"] = "(同任务其他提交对) " + str(top_pair.get("note", ""))

    step_eval = evaluate_step_mode(
        task_obj,
        submission.step_evidences or [],
        criteria=criteria_list,
        task_requirements_text=task_requirements,
    )
    step_results = step_eval.get("steps") or []

    completeness_steps = []
    for sr in step_results:
        idx = sr.get("index")
        if idx is None:
            continue
        status = "passed" if sr.get("passed") else "missing" if not sr.get("score") or sr["score"] == 0 else "部分完成"
        detail_parts = []
        detail_parts.append(f"得分 {sr.get('score')}/{sr.get('pass_threshold')}")
        if sr.get("reason"):
            detail_parts.append(sr["reason"])
        ev_hit = None
        for ev in (submission.step_evidences or []):
            if isinstance(ev, dict) and int(ev.get("step_index") or 0) == int(idx):
                ev_hit = ev
                break
        if ev_hit:
            nf = len(ev_hit.get("files") or [])
            ni = len(ev_hit.get("images") or [])
            if nf or ni:
                detail_parts.append(f"证据：{nf} 个文件 / {ni} 张图片")
            first_img = (ev_hit.get("images") or [{}])[0] if (ev_hit.get("images") or []) else None
        else:
            first_img = None
        step_entry = {
            "index": idx,
            "name": sr.get("title") or f"步骤{idx}",
            "status": status,
            "detail": "；".join(str(x) for x in detail_parts if x not in (None, "")),
            "source": sr.get("source"),
        }
        if first_img and isinstance(first_img, dict) and first_img.get("filename"):
            step_entry["source_image"] = first_img.get("filename")
        completeness_steps.append(step_entry)
    seen_idx = {int(s["index"]) for s in completeness_steps}
    for ev in (submission.step_evidences or []):
        if not isinstance(ev, dict):
            continue
        si = int(ev.get("step_index") or 0)
        if si <= 0 or si in seen_idx:
            continue
        completeness_steps.append({
            "index": si,
            "name": f"步骤{si}（未对应任务步骤）",
            "status": "passed" if (len(ev.get("files") or []) + len(ev.get("images") or []) + len(str(ev.get("content") or "")) > 0) else "missing",
            "detail": f"证据：{len(ev.get('files') or [])} 文件 / {len(ev.get('images') or [])} 图片 / {len(str(ev.get('content') or ''))} 文字字符",
            "source": "manual",
        })
    completeness_steps.sort(key=lambda x: int(x.get("index") or 0))

    step_progress: Optional[Dict[str, Any]] = None
    extra_issues: List[Dict[str, Any]] = []
    if all_images:
        try:
            step_progress = extract_step_progress(task_requirements or "", all_images)
            extra_issues = progress_extra_issues(step_progress or {})
        except Exception as _e_d2:
            extra_issues.append({
                "type": "step_progress_error",
                "title": "步骤进度解析异常（不影响分步得分）",
                "detail": f"{type(_e_d2).__name__}: {_e_d2}",
            })

    issues: List[Dict[str, Any]] = list(extra_issues)
    if archive:
        issues.extend(to_logic_issues(archive, top_pair=top_pair))
    for sr in step_results:
        if not sr.get("passed"):
            issues.append({
                "type": "step_not_passed",
                "title": f"步骤 {sr.get('index')} 未通过",
                "severity": "高",
                "description": sr.get("reason") or "",
            })

    ev_row = db.query(Evaluation).filter(Evaluation.submission_id == submission.id).order_by(Evaluation.id.desc()).first()
    if ev_row is None:
        ev_row = Evaluation(submission_id=submission.id, evaluator_type="ai")
    ev_row.total_score = float(step_eval.get("total", 0.0))
    ev_row.dimension_scores = step_eval.get("scores", [])
    ev_row.comment = step_eval.get("comment", "")
    ev_row.step_completeness = completeness_steps
    ev_row.logic_issues = issues
    db.add(ev_row)
    try:
        db.commit()
        db.refresh(ev_row)
    except Exception:
        db.rollback()

    return {
        "success": True,
        "submission_id": submission.id,
        "evaluation_id": ev_row.id,
        "filename": submission.filename or "",
        "content": (submission.content or "")[:500],
        "step_index": this_si,
        "evaluation": {
            "scores": step_eval.get("scores", []),
            "total": step_eval.get("total", 0.0),
            "comment": step_eval.get("comment", ""),
            "from_step_mode": True,
        },
        "step_results": step_results,
        "step_evidences": [
            {
                "step_index": e.get("step_index"),
                "files_count": len(e.get("files") or []),
                "images_count": len(e.get("images") or []),
                "content_len": len(str(e.get("content") or "")),
                "submitted_at": e.get("submitted_at"),
            }
            for e in (submission.step_evidences or [])
        ],
        "completeness": {
            "steps": completeness_steps,
            "issues": issues,
        },
        "code_analysis": {
            "summary_metrics": sm,
            "files": [
                {
                    "filename": f.get("filename"),
                    "language": f.get("language"),
                    "metrics": f.get("metrics"),
                }
                for f in ((archive or {}).get("files") or [])
            ],
            "top_plagiarism_pair": top_pair,
            "step_progress": step_progress,
            "images_collected": len(all_images),
            "step_mode": True,
        },
    }


# ============================================================
#  G1-1 · 异步评分任务（SSE 5 步进度推送）
# ============================================================

class AsyncJobStore:
    """内存级任务状态机 + 事件流（重启后丢失，但学生提交都是一次性场景）"""
    def __init__(self, ttl_seconds: int = 3600):
        self._lock = threading.RLock()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._last_cleanup = time.time()

    def _cleanup(self):
        now = time.time()
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        with self._lock:
            expired = [jid for jid, j in self._jobs.items()
                       if now - j.get("created_at", now) > self._ttl]
            for jid in expired:
                self._jobs.pop(jid, None)

    def create(self, kind: str = "code") -> str:
        self._cleanup()
        jid = "j_" + uuid.uuid4().hex[:16]
        with self._lock:
            self._jobs[jid] = {
                "job_id": jid,
                "kind": kind,
                "status": "queued",
                "step": 0,
                "step_name": "",
                "events": [],
                "log_lines": [],
                "result": None,
                "error": None,
                "created_at": time.time(),
                "finished_at": None,
                "subscribers": 0,
            }
        return jid

    def push_event(self, jid: str, event: str, data: Any):
        with self._lock:
            job = self._jobs.get(jid)
            if not job:
                return
            entry = {"event": event, "data": data, "ts": time.time()}
            job["events"].append(entry)
            if len(job["events"]) > 500:
                job["events"] = job["events"][-500:]
            if event == "log" and isinstance(data, str):
                job["log_lines"].append(data)
                if len(job["log_lines"]) > 200:
                    job["log_lines"] = job["log_lines"][-200:]
            if event == "step":
                idx = data.get("index") if isinstance(data, dict) else None
                name = data.get("name") if isinstance(data, dict) else None
                if isinstance(idx, int):
                    job["step"] = idx
                if isinstance(name, str):
                    job["step_name"] = name
            elif event == "status":
                if isinstance(data, str):
                    job["status"] = data
            elif event == "done":
                job["status"] = "done"
                job["finished_at"] = time.time()
                job["result"] = data
            elif event == "error":
                job["status"] = "failed"
                job["finished_at"] = time.time()
                job["error"] = data if isinstance(data, str) else str(data)

    def get(self, jid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(jid)
            return dict(job) if job else None

    def iter_new_events(self, jid: str, last_seen: int, poll_timeout: float = 0.6):
        deadline = time.time() + poll_timeout
        while time.time() < deadline:
            with self._lock:
                job = self._jobs.get(jid)
                if not job:
                    return None, []
                events = job["events"]
                if len(events) > last_seen:
                    new_evts = list(events[last_seen:])
                    return len(events), new_evts
                if job["status"] in ("done", "failed"):
                    return len(events), []
            time.sleep(0.08)
        return last_seen, []


_JOB_STORE = AsyncJobStore(ttl_seconds=3600)


def _emit_step(jid: str, index: int, name: str, percent: int,
               title: Optional[str] = None, detail: Optional[str] = None):
    _JOB_STORE.push_event(jid, "step", {
        "index": index,
        "name": name,
        "percent": max(0, min(100, int(percent))),
        "title": title or name,
        "detail": detail or "",
    })


def _emit_log(jid: str, line: str):
    _JOB_STORE.push_event(jid, "log", line)


def _emit_status(jid: str, status: str):
    _JOB_STORE.push_event(jid, "status", status)


def _serialize_job_status(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "kind": job.get("kind"),
        "status": job["status"],
        "step": job["step"],
        "step_name": job.get("step_name") or "",
        "created_at": job.get("created_at"),
        "finished_at": job.get("finished_at"),
        "result": job.get("result"),
        "error": job.get("error"),
        "log_lines": (job.get("log_lines") or [])[-20:],
    }


# ---------- 异步代码评分：拆分 5 步执行 ----------
def _run_code_job_async(
    jid: str,
    files_bytes: List[Dict[str, Any]],
    task_requirements: str,
    criteria: str,
    student_id: int,
    task_id: int,
    check_plagiarism: bool,
):
    """后台线程执行：把 upload_code_and_evaluate 拆成 5 个阶段，并推送 SSE。"""
    db = SessionLocal()
    try:
        # ID 转换（必须在后台线程内用自己的 db session 查）
        student_pk = _account_to_student_pk(db, student_id)
        student_for_submission = student_pk if student_pk else None

        # ---------------- STEP 1: PARSE ----------------
        _emit_status(jid, "running")
        _emit_step(jid, 1, "parse", 5, "文件解析", "正在解析上传的文件…")
        _emit_log(jid, f"[1/5] parse: 接收 {len(files_bytes)} 个文件")

        all_files: List[Dict[str, Any]] = []
        all_images: List[Dict[str, Any]] = []
        filenames = []
        save_paths = []
        last_parse = None
        parse_errors: List[str] = []

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        for i, fb in enumerate(files_bytes):
            raw_name = fb["filename"]
            ext = fb.get("ext") or os.path.splitext(raw_name)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_base = re.sub(r"[^\w\u4e00-\u9fa5.\-]+", "_", raw_name)[:80] or "upload"
            save_name = (f"code_{timestamp}_{uuid.uuid4().hex[:8]}__{safe_base}"
                         if ext.lower() in {".png", ".jpg", ".jpeg"} else
                         f"code_{timestamp}_{uuid.uuid4().hex[:8]}{ext}")
            save_path = os.path.join(UPLOAD_DIR, save_name)
            with open(save_path, "wb") as f:
                f.write(fb["content_bytes"])

            parse_result = parse_file_sync(save_path)
            if not parse_result.get("success"):
                if _looks_like_code(raw_name):
                    parse_errors.append(f"{raw_name}: {parse_result.get('error') or '解析失败'}")
                continue

            last_parse = parse_result
            save_paths.append(save_path)
            filenames.append(raw_name)
            all_files.extend(parse_result.get("files") or [])
            for img in parse_result.get("images") or []:
                entry = dict(img)
                entry.setdefault("filename", img.get("name") or "image")
                entry.setdefault("path", img.get("path") or img.get("file_path"))
                all_images.append(entry)

        if not all_files:
            err = "未解析到任何源码文件" + (f"：{'; '.join(parse_errors[:3])}" if parse_errors else "")
            _emit_log(jid, f"[1/5] parse error: {err}")
            _JOB_STORE.push_event(jid, "error", err)
            return

        _emit_log(jid, f"[1/5] parse done: {len(all_files)} 个源码文件，{len(all_images)} 张图片")
        _emit_step(jid, 1, "parse", 100, "文件解析", f"解析出 {len(all_files)} 个源码文件，{len(all_images)} 张截图")

        # ---------------- STEP 2: ANALYZE ----------------
        _emit_step(jid, 2, "analyze", 20, "静态分析", "正在计算代码指标 + 抄袭比对…")
        code_input = [(f.get("filename") or f"file_{i+1}", f.get("content") or "")
                      for i, f in enumerate(all_files)]
        archive = analyze_code_files(code_input)
        sm = archive.get("summary_metrics") or {}
        _emit_log(jid, f"[2/5] analyze: 总行数 {sm.get('loc')}, 函数 {sm.get('functions')}, 圈复杂度>{sm.get('complex_files')}")

        top_pair = None
        if check_plagiarism and task_id > 0:
            _emit_log(jid, "[2/5] plagiarism detect: scanning historical submissions…")
            others: Dict[str, Any] = {}
            other_subs = (
                db.query(Submission)
                .filter(Submission.task_id == task_id)
                .filter(Submission.id != 0)
                .all()
            )
            for sub in other_subs:
                if not sub or not sub.file_path or not os.path.exists(sub.file_path):
                    continue
                try:
                    pr = parse_file_sync(sub.file_path)
                    if not pr.get("success"):
                        continue
                    of = pr.get("files") or []
                    if not of:
                        continue
                    inp = [(f.get("filename") or f"o{sub.id}_{i}", f.get("content") or "")
                           for i, f in enumerate(of)]
                    others[str(sub.id)] = analyze_code_files(inp)
                except Exception:
                    continue
            current_key = f"stu_{student_id or 'current'}"
            all_for_detect = dict(others)
            all_for_detect[current_key] = archive
            plag = detect_plagiarism(all_for_detect, threshold=0.85)
            if plag:
                for p in plag:
                    a, b = str(p.get("student_id_a", "")), str(p.get("student_id_b", ""))
                    if current_key in (a, b):
                        other_id = b if a == current_key else a
                        tp = dict(p)
                        if str(tp.get("student_id_a")) == current_key:
                            tp["student_id_a"] = "当前提交"
                            tp["student_id_b"] = other_id
                        else:
                            tp["student_id_a"] = other_id
                            tp["student_id_b"] = "当前提交"
                        top_pair = tp
                        break
            if top_pair:
                _emit_log(jid, f"[2/5] plagiarism: 发现 1 组高相似 (sim={top_pair.get('similarity')})")

        eval_result = to_evaluation_dimensions(archive, top_pair=top_pair)
        issues = to_logic_issues(archive, top_pair=top_pair)
        steps = _code_files_to_steps(all_files)

        # D2 step_progress 从截图中提取
        step_progress: Optional[Dict[str, Any]] = None
        if all_images:
            try:
                step_progress = extract_step_progress(task_requirements or "", all_images)
                extra_sc = progress_to_step_completeness(step_progress or {})
                if extra_sc:
                    index_map = {s.get("index"): s for s in steps if isinstance(s, dict) and s.get("index")}
                    merged_steps = []
                    for s in extra_sc:
                        if s.get("index") in index_map:
                            old = dict(index_map[s["index"]])
                            merged_detail = old.get("detail", "")
                            if merged_detail and s.get("detail"):
                                merged_detail = f"{merged_detail}；图片：{s['detail']}"
                            elif s.get("detail"):
                                merged_detail = f"图片：{s['detail']}"
                            old["detail"] = merged_detail
                            if s.get("source_image"):
                                old["source_image"] = s["source_image"]
                            old["status"] = (
                                "passed"
                                if (old.get("status") == "passed" or s.get("status") == "passed")
                                else (s.get("status") or old.get("status") or "missing")
                            )
                            merged_steps.append(old)
                        else:
                            merged_steps.append(s)
                    covered = {s.get("index") for s in merged_steps if s.get("index")}
                    for s in steps:
                        if s.get("index") not in covered:
                            merged_steps.append(s)
                    merged_steps.sort(key=lambda s: int(s.get("index") or 0))
                    steps = merged_steps
                extra_is = progress_extra_issues(step_progress or {})
                exist_types = {i.get("type") for i in issues if isinstance(i, dict)}
                for i in extra_is:
                    if isinstance(i, dict) and i.get("type") not in exist_types:
                        issues.append(i)
            except Exception as _e_d2:
                issues.append({
                    "type": "step_progress_error",
                    "title": "步骤进度解析异常（不影响代码得分）",
                    "detail": f"{type(_e_d2).__name__}: {_e_d2}",
                })

        _emit_log(jid, f"[2/5] analyze done: {len(issues)} 个问题点，{len(steps)} 个步骤")
        _emit_step(jid, 2, "analyze", 100, "静态分析",
                   f"静态指标计算完成，发现 {len(issues)} 个改进点，{len(steps)} 个步骤")

        # ---------------- STEP 3: AI SCORE ----------------
        _emit_step(jid, 3, "ai_score", 30, "AI 评分", "正在进行 AI 多维度评分（如无 AI key 则使用静态分析得分）…")
        _emit_log(jid, "[3/5] ai_score: to_evaluation_dimensions -> (scores + comment) ready")
        time.sleep(0.4)
        _emit_step(jid, 3, "ai_score", 70, "AI 评分", "AI 正在生成点评建议…")
        time.sleep(0.4)
        _emit_log(jid, f"[3/5] ai_score done: total={eval_result.get('total')}, dims={len(eval_result.get('scores') or [])}")
        _emit_step(jid, 3, "ai_score", 100, "AI 评分",
                   f"AI 评分 {eval_result.get('total'):.1f}/100，生成建议 {len(eval_result.get('comment') or '')} 字")

        # ---------------- STEP 4: SAVE ----------------
        _emit_step(jid, 4, "save", 15, "写入数据库", "正在保存提交记录和评价…")
        class_id = None
        if task_id > 0:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                if task.requirements:
                    task_requirements = task.requirements
                class_id = task.class_id

        task_obj = None
        if task_id > 0:
            task_obj = db.query(Task).filter(Task.id == task_id).first()
        if not task_obj:
            task_obj = Task(
                title="实训代码任务",
                requirements=task_requirements,
                criteria=criteria,
                status="published",
            )
            db.add(task_obj)
            db.commit()
            db.refresh(task_obj)

        if student_for_submission:
            _purge_stale_submission_for_resubmit(db, task_obj.id, student_for_submission)

        save_path = save_paths[-1] if save_paths else ""
        combined_text = (last_parse or {}).get("text", "") if last_parse else ""
        submission = Submission(
            task_id=task_obj.id,
            student_id=student_for_submission,
            class_id=class_id,
            filename=", ".join(filenames),
            file_path=save_path,
            content=combined_text[:5000],
        )
        db.add(submission)
        try:
            db.flush()
            db.refresh(submission)
        except Exception:
            db.rollback()
            submission.student_id = None
            db.add(submission)
            db.flush()
            db.refresh(submission)
        db.commit()
        try:
            db.refresh(submission)
        except Exception:
            pass

        if top_pair and ("当前提交" not in str(top_pair.get("student_id_a", "")) +
                         str(top_pair.get("student_id_b", ""))):
            sid = str(submission.id)
            if str(top_pair.get("student_id_a")) == sid or str(top_pair.get("student_id_b")) == sid:
                top_pair = None

        evaluation = Evaluation(
            submission_id=submission.id,
            evaluator_type="ai",
            total_score=float(eval_result.get("total", 0.0)),
            dimension_scores=eval_result.get("scores", []),
            comment=eval_result.get("comment", ""),
            step_completeness=steps,
            logic_issues=issues,
        )
        db.add(evaluation)
        db.commit()
        _emit_log(jid, f"[4/5] save: submission_id={submission.id}, eval_id={evaluation.id}")
        _emit_step(jid, 4, "save", 100, "写入数据库",
                   f"submission #{submission.id} 已写入，evaluation #{evaluation.id} 已入库")

        # ---------------- STEP 5: DONE ----------------
        result_payload = {
            "success": True,
            "job_id": jid,
            "submission_id": submission.id,
            "evaluation_id": evaluation.id,
            "filename": ", ".join(filenames),
            "content": combined_text[:500],
            "evaluation": {
                "scores": eval_result.get("scores", []),
                "total": eval_result.get("total", 0.0),
                "comment": eval_result.get("comment", ""),
                "from_code_analyzer": True,
                "async": True,
            },
            "completeness": {"steps": steps, "issues": issues},
            "code_analysis": {
                "summary_metrics": sm,
                "files": [
                    {"filename": f.get("filename"), "language": f.get("language"),
                     "metrics": f.get("metrics")}
                    for f in ((archive or {}).get("files") or [])
                ],
                "top_plagiarism_pair": top_pair,
                "step_progress": step_progress,
                "images_collected": len(all_images),
            },
        }
        _emit_step(jid, 5, "done", 100, "完成", "全部步骤已完成，即将跳转结果页…")
        _JOB_STORE.push_event(jid, "done", result_payload)
        _emit_log(jid, "[5/5] done: result ready")
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        _emit_log(jid, f"[ERROR] {type(exc).__name__}: {exc}")
        print(f"[async-job {jid}] {tb}")
        _JOB_STORE.push_event(jid, "error", f"{type(exc).__name__}: {exc}")
    finally:
        db.close()


def parse_file_sync(path: str) -> Dict[str, Any]:
    """兼容 parse_file 是 async 的写法：直接调用，await 在同步线程用 asyncio.run。"""
    import asyncio
    try:
        coro = parse_file(path)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is None:
            return asyncio.run(coro)
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(lambda: asyncio.run(coro))
                return fut.result()
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- 异步文档评分（老 / 端点） ----------
def _run_doc_job_async(
    jid: str,
    files_bytes: List[Dict[str, Any]],
    task_requirements: str,
    criteria: str,
    student_id: int,
    task_id: int,
):
    db = SessionLocal()
    try:
        # ID 转换
        student_pk = _account_to_student_pk(db, student_id)
        student_for_submission = student_pk if student_pk else None

        _emit_status(jid, "running")
        _emit_step(jid, 1, "parse", 5, "文件解析", "正在解析文档/PDF/图片…")
        all_texts = []
        filenames = []
        save_paths = []
        criteria_list = [c.strip() for c in criteria.split(",")]

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        for fb in files_bytes:
            raw_name = fb["filename"]
            ext = fb.get("ext") or os.path.splitext(raw_name)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
            save_path = os.path.join(UPLOAD_DIR, save_name)
            with open(save_path, "wb") as f:
                f.write(fb["content_bytes"])
            parse_result = parse_file_sync(save_path)
            if parse_result.get("success"):
                text = parse_result.get("text", "")
                if parse_result.get("type") == "image":
                    all_texts.append(f"[图片文件: {raw_name}]")
                else:
                    all_texts.append(text)
                filenames.append(raw_name)
                save_paths.append(save_path)

        if not all_texts:
            _JOB_STORE.push_event(jid, "error", "未解析到任何文档内容")
            return

        combined_text = "\n\n".join(all_texts)
        _emit_log(jid, f"[1/5] parse done: {len(filenames)} 个文件，{len(combined_text)} 字")
        _emit_step(jid, 1, "parse", 100, "文件解析", f"解析出 {len(filenames)} 个文件")

        _emit_step(jid, 2, "analyze", 30, "要求匹配", "正在匹配任务要求完成度…")
        class_id = None
        if task_id > 0:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                if task.criteria:
                    criteria_list = [c.strip() for c in task.criteria.split(",")]
                if task.requirements:
                    task_requirements = task.requirements
                class_id = task.class_id
        _emit_log(jid, f"[2/5] analyze: criteria={criteria_list}")
        _emit_step(jid, 2, "analyze", 100, "要求匹配", f"{len(criteria_list)} 个维度就绪")

        _emit_step(jid, 3, "ai_score", 25, "AI 评分", "正在进行 AI 多维度评分…")
        eval_result = evaluate(task_requirements, combined_text, criteria_list)
        completeness = check_completeness(task_requirements, combined_text)
        time.sleep(0.4)
        _emit_log(jid, f"[3/5] ai_score done: total={eval_result.get('total')}")
        _emit_step(jid, 3, "ai_score", 100, "AI 评分", f"AI 评分 {eval_result.get('total'):.1f}/100")

        _emit_step(jid, 4, "save", 30, "写入数据库", "正在保存提交记录…")
        task_obj = None
        if task_id > 0:
            task_obj = db.query(Task).filter(Task.id == task_id).first()
        if not task_obj:
            task_obj = Task(
                title="实训任务",
                requirements=task_requirements,
                criteria=",".join(criteria_list),
                status="published",
            )
            db.add(task_obj)
            db.commit()
            db.refresh(task_obj)

        if student_for_submission:
            _purge_stale_submission_for_resubmit(db, task_obj.id, student_for_submission)

        save_path = save_paths[-1] if save_paths else ""
        submission = Submission(
            task_id=task_obj.id,
            student_id=student_for_submission,
            class_id=class_id,
            filename=", ".join(filenames),
            file_path=save_path,
            content=combined_text[:5000],
        )
        db.add(submission)
        try:
            db.flush(); db.refresh(submission)
        except Exception:
            db.rollback()
            submission.student_id = None
            db.add(submission); db.flush(); db.refresh(submission)
        db.commit()
        try: db.refresh(submission)
        except Exception: pass

        evaluation = Evaluation(
            submission_id=submission.id,
            evaluator_type="ai",
            total_score=eval_result["total"],
            dimension_scores=eval_result["scores"],
            comment=eval_result["comment"],
            step_completeness=completeness.get("steps", []),
            logic_issues=completeness.get("issues", []),
        )
        db.add(evaluation)
        db.commit()
        _emit_log(jid, f"[4/5] save: submission_id={submission.id}, eval_id={evaluation.id}")
        _emit_step(jid, 4, "save", 100, "写入数据库", f"已写入 submission #{submission.id}")

        result_payload = {
            "success": True,
            "job_id": jid,
            "submission_id": submission.id,
            "evaluation_id": evaluation.id,
            "filename": ", ".join(filenames),
            "content": combined_text[:500],
            "evaluation": eval_result,
            "completeness": completeness,
            "async": True,
        }
        _emit_step(jid, 5, "done", 100, "完成", "评价完成，即将跳转结果页")
        _JOB_STORE.push_event(jid, "done", result_payload)
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        _emit_log(jid, f"[ERROR] {type(exc).__name__}: {exc}")
        print(f"[async-doc-job {jid}] {tb}")
        _JOB_STORE.push_event(jid, "error", f"{type(exc).__name__}: {exc}")
    finally:
        db.close()


# ---------- HTTP 端点 ----------

@router.post("/async")
async def create_async_job(
    files: List[UploadFile] = File(...),
    task_requirements: str = Form("请完成实训代码任务"),
    criteria: str = Form("代码质量,功能完整性,文档规范性,界面设计"),
    student_id: int = Form(0),
    task_id: int = Form(0),
    check_plagiarism: bool = Form(True),
    mode: str = Form("auto"),
):
    """创建异步评分任务，立即返回 job_id，然后通过 /stream 或 /status 订阅进度。"""
    files_bytes: List[Dict[str, Any]] = []
    code_ext_count = 0
    doc_ext_count = 0
    for f in files:
        raw = f.filename or "upload"
        ext = os.path.splitext(raw)[1].lower()
        content = await f.read()
        files_bytes.append({"filename": raw, "ext": ext, "content_bytes": content})
        if _looks_like_code(raw):
            code_ext_count += 1
        if ext in {".docx", ".pdf", ".doc"}:
            doc_ext_count += 1

    if mode == "auto":
        use_code = (code_ext_count >= doc_ext_count)
    else:
        use_code = (mode == "code")

    jid = _JOB_STORE.create(kind="code" if use_code else "doc")
    _JOB_STORE.push_event(jid, "log", f"任务创建: {len(files_bytes)} 个文件, mode={'code' if use_code else 'doc'}")

    target: Callable
    if use_code:
        target = lambda: _run_code_job_async(jid, files_bytes, task_requirements, criteria,
                                              student_id, task_id, check_plagiarism)
    else:
        target = lambda: _run_doc_job_async(jid, files_bytes, task_requirements, criteria,
                                             student_id, task_id)
    t = threading.Thread(target=target, name=f"eval-{jid[-8:]}", daemon=True)
    t.start()
    return {"success": True, "job_id": jid, "mode": ("code" if use_code else "doc")}


def _sse_format(event: str, data: Any) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


@router.get("/stream/{job_id}")
async def stream_job_progress(job_id: str):
    """SSE 端点：5 步进度流，客户端用 new EventSource('/api/upload-eval/stream/{job_id}')"""
    job = _JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务 {job_id} 不存在或已过期")

    async def generator():
        last = 0
        yield _sse_format("hello", {"job_id": job_id,
                                     "ttl_seconds": 3600,
                                     "server_time": time.time()})
        current_job = _JOB_STORE.get(job_id) or {}
        history = current_job.get("events") or []
        for ev in history:
            yield _sse_format(ev["event"], ev["data"])
            last += 1

        idle_tick = 0
        while True:
            last, new_evts = _JOB_STORE.iter_new_events(job_id, last, poll_timeout=0.5)
            for ev in (new_evts or []):
                yield _sse_format(ev["event"], ev["data"])
            current = _JOB_STORE.get(job_id)
            if not current:
                yield _sse_format("error", "任务已过期")
                return
            if current["status"] in ("done", "failed"):
                return
            idle_tick += 1
            if idle_tick > 2:
                yield _sse_format("heartbeat", {"ts": time.time()})
                idle_tick = 0

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status/{job_id}")
def get_job_status(job_id: str):
    """轮询兜底接口（SSE 不可用或客户端想短轮询）"""
    job = _JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"任务 {job_id} 不存在或已过期")
    return {"success": True, "data": _serialize_job_status(job)}
