from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
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
from app.models.tables import Task, Submission, Evaluation
import os, uuid, re
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

    submission = Submission(
        task_id=task_obj.id,
        student_id=student_id if student_id > 0 else None,
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
    all_files: list = []  # 累积所有代码包解析后的 files[] 项
    all_images: List[Dict[str, Any]] = []  # D2：累积 zip 内混的图片（步骤截图）
    filenames = []
    save_paths = []  # 可能多个上传文件；返回时取最后一个
    last_parse = None

    for file in files:
        raw_name = file.filename or "upload"
        ext = os.path.splitext(raw_name)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 保留原文件名关键词（01_登录.png / 注册.png）供 step_extractor 识别步骤编号和关键词
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
        # D2：收集 zip 里/单独上传的图片
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

    # 代码静态分析
    code_input = [(f.get("filename") or f"file_{i+1}", f.get("content") or "")
                  for i, f in enumerate(all_files)]
    archive = analyze_code_files(code_input)
    sm = archive.get("summary_metrics") or {}

    # 抄袭检测：同任务的其他 code 提交（仅当 task_id > 0 且 check_plagiarism=True）
    top_pair = None
    if check_plagiarism and task_id > 0:
        others: dict = {}
        other_subs = (
            db.query(Submission)
            .filter(Submission.task_id == task_id)
            .filter(Submission.id != 0)  # 后续会排除自己
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
                # 历史提交有任何解析异常就跳过，避免影响当前学生提交
                continue
        # 加上当前学生，取 1 对对比（后续再 commit submission.id 后再排除自己）
        current_id_placeholder = f"stu_{student_id or 'current'}"
        all_for_detect = dict(others)
        all_for_detect[current_id_placeholder] = archive
        plag = detect_plagiarism(all_for_detect, threshold=0.85)
        # 找到包含当前学生的首对，作为 top_pair（展示给当前学生看）
        if plag:
            top_pair = None
            for p in plag:
                a, b = str(p.get("student_id_a", "")), str(p.get("student_id_b", ""))
                if current_id_placeholder in (a, b):
                    other_id = b if a == current_id_placeholder else a
                    # 克隆一份，把占位符替换成更友好的 "当前提交"
                    tp = dict(p)
                    if str(tp.get("student_id_a")) == current_id_placeholder:
                        tp["student_id_a"] = f"当前提交"
                        tp["student_id_b"] = other_id
                    else:
                        tp["student_id_a"] = other_id
                        tp["student_id_b"] = f"当前提交"
                    top_pair = tp
                    break
            if top_pair is None and plag:
                # 没匹配到当前提交也无妨，用最高那对提示"班内有雷同"
                p = plag[0]
                top_pair = {
                    "student_id_a": p.get("student_id_a"),
                    "student_id_b": p.get("student_id_b"),
                    "similarity": p.get("similarity"),
                    "severity": p.get("severity"),
                    "note": "(同任务其他提交对) " + str(p.get("note", "")),
                }

    # 对齐 ai_evaluator.evaluate / check_completeness 的返回
    eval_result = to_evaluation_dimensions(archive, top_pair=top_pair)
    issues = to_logic_issues(archive, top_pair=top_pair)
    steps = _code_files_to_steps(all_files)

    # D2：如果 zip 里带了步骤截图图片 → 调用 step_extractor 算步骤进度（任何异常不阻断代码主链路，只记录 warnings）
    step_progress: Optional[Dict[str, Any]] = None
    if all_images:
        try:
            step_progress = extract_step_progress(task_requirements or "", all_images)
            # 融合到 steps（覆盖 / 叠加到 code_files_to_steps 后面，按 index 对齐去重）
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
            # 不抛：避免 OCR 异常让整个代码评测失败
            issues.append({
                "type": "step_progress_error",
                "title": "步骤进度解析异常（不影响代码得分）",
                "detail": f"{type(_e_d2).__name__}: {_e_d2}",
            })

    # task / submission / evaluation 入库（和原 / 端点逻辑一致，保证 DB 兼容性）
    class_id = None
    if task_id > 0:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            if task.criteria:
                # criteria 仅用于展示，不覆盖 code 链路固定 4 维度
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

    save_path = save_paths[-1] if save_paths else ""
    combined_text = last_parse.get("text", "") if last_parse else ""
    submission = Submission(
        task_id=task_obj.id,
        student_id=student_id if student_id > 0 else None,
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
        # 最常见：student_id 外键约束失败（users 表没有该 student_id）。
        # 这里不抛异常：student_id 置 NULL 重新落库，保证 submission/evaluation 仍有记录。
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

    # 排除自己：如果 top_pair 里有 submission.id（之前的 others 可能已经包含本提交的老版本），删掉
    if top_pair and ("当前提交" not in str(top_pair.get("student_id_a", "")) +
                     str(top_pair.get("student_id_b", ""))):
        sid = str(submission.id)
        if str(top_pair.get("student_id_a")) == sid or str(top_pair.get("student_id_b")) == sid:
            # 避免"我抄我自己"的假阳性
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
        # D1 新增：前端雷达表 / 代码页要直接展示静态指标和雷同对
        # D2 新增：code_analysis 追加 step_progress（含 total_steps/percent/source/steps）
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
    """E1：分步实训提交端点。
    参数：
      - step_index：本次是第几步（必填且>=1）；若 step_index<=0 视为"一次性整包模式"，退化为 /code 端点等价逻辑
      - step_text：学生对该步的文字描述（可选）
      - submission_id：之前 /step 已创建的 submission.id，可传；不传就创建新的
      - files：该步的证据文件（可传 0~N 个：代码、zip、截图 png/jpg/jpeg、文档 .md/.txt 等）
    返回：
      submission_id / evaluation / step_evidences / code_analysis（形状和 /code 对齐）
    """
    if step_index and step_index < 0:
        step_index = 0

    # ========== 1) 解析/存盘上传的 files（和 /code 同样的流程，但累積到当前 step） ==========
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
            # 图片解析失败是常事（没 PaddleOCR），只要存盘就继续
            if not parse_result.get("success"):
                if ext.lower() not in _IMG_EXTS and _looks_like_code(raw_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"证据文件解析失败: {parse_result.get('error') or '未知原因'}",
                    )
                # 对图片/无法解析的文件，手动塞一条 images 记录（至少有 path/filename）
                if ext.lower() in _IMG_EXTS:
                    all_images.append({"filename": raw_name, "path": save_path, "name": raw_name})
                # 无法解析但非图片的，跳过
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

    # ========== 2) 校验 step_index / task_obj / submission 选择 ==========
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
        # 没有 task_id 也无妨，先建一个兜底 Task
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

    # 取/建 submission：
    #   - submission_id 已给：直接取；没取到再新建
    #   - 否则新建一个
    submission: Optional[Submission] = None
    if submission_id and submission_id > 0:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission is None:
        combined_text_init = (last_parse or {}).get("text", "") or ""
        submission = Submission(
            task_id=task_obj.id,
            student_id=student_id if student_id > 0 else None,
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

    # ========== 3) 合并 step_evidences：取 DB 里老的 + 本次 step_index 更新/追加 ==========
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

    # 本次 step 的证据（哪怕 step_index=0 也给一个 step_index=0 作为"综合补充"的兜底索引）
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
        # D2 兼容：如果 step_extractor 已经在 parse 里塞了 OCR 文本，也带上
        ocr = img.get("ocr_text") or img.get("text")
        if ocr:
            merged_ocr_texts.append(str(ocr)[:2000])

    # 先把 merged_files 全部去重（按 filename+path）
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
    # 同时更新 filename / content / file_path 给前端/DB 展示
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
        # submission 级别的 commit 失败也尽量继续，不抛异常

    # ========== 4) 代码静态分析（如果该步有 any 代码文件） + 抄袭检测（可选） ==========
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

    # ========== 5) AI step 模式评价（按新 submission.step_evidences 全部步骤一起评价） ==========
    # 如果 step_index=0（一次整包）且 steps_def 为空 → evaluate_step_mode 会兜底回 evaluate()
    step_eval = evaluate_step_mode(
        task_obj,
        submission.step_evidences or [],
        criteria=criteria_list,
        task_requirements_text=task_requirements,
    )
    step_results = step_eval.get("steps") or []

    # ========== 6) step_completeness（对齐 /code 的形状：按 index 排序） ==========
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
        # 找该步有多少文件/图片证据
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
    # completeness_steps 里没出现的其他 evidence step_index（比如 step_index=0 的综合补充包）也挂上去
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

    # D2：如果本次 all_images 非空，仍调用一次 extract_step_progress 做对比（不阻断）
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

    # logic_issues：代码静态问题 + D2 step_progress 问题
    issues: List[Dict[str, Any]] = list(extra_issues)
    if archive:
        issues.extend(to_logic_issues(archive, top_pair=top_pair))
    # 分步模式里把 step_results 里未通过的也记一条 issue，方便前端直接展示
    for sr in step_results:
        if not sr.get("passed"):
            issues.append({
                "type": "step_not_passed",
                "title": f"步骤 {sr.get('index')} 未通过",
                "severity": "高",
                "description": sr.get("reason") or "",
            })

    # ========== 7) 存 Evaluation（每条 submission 对应一条 AI Evaluation；如果该 submission 已有就更新，避免同一 submission 多条 evaluation） ==========
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

    # ========== 8) 返回：形状尽量对齐 /code 端点 ==========
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
