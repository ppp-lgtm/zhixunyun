import io
import os
import tempfile
from datetime import datetime
from collections import defaultdict, Counter

try:
    from openpyxl import Workbook  # type: ignore
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side  # type: ignore
    from openpyxl.chart import BarChart, Reference, LineChart, RadarChart  # type: ignore
    from openpyxl.chart.label import DataLabelList  # type: ignore
    from openpyxl.drawing.image import Image as XlImage  # type: ignore
    _HAS_OPENPYXL = True
except Exception:  # pragma: no cover
    Workbook = None  # type: ignore
    Font = Alignment = PatternFill = Border = Side = BarChart = Reference = None  # type: ignore
    LineChart = RadarChart = DataLabelList = XlImage = None  # type: ignore
    _HAS_OPENPYXL = False

try:
    from docx import Document  # type: ignore
    from docx.shared import Pt, Inches  # type: ignore
    _HAS_DOCX = True
except Exception:  # pragma: no cover
    Document = None  # type: ignore
    Pt = Inches = None  # type: ignore
    _HAS_DOCX = False

try:
    from fpdf import FPDF  # type: ignore
    _HAS_FPDF = True
except Exception:  # pragma: no cover
    FPDF = None  # type: ignore
    _HAS_FPDF = False

try:
    import matplotlib  # type: ignore
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore
    import numpy as np  # type: ignore
    from matplotlib import font_manager as fm  # type: ignore
    _HAS_MPL = True
except Exception:  # pragma: no cover
    matplotlib = None
    plt = None
    np = None
    fm = None
    _HAS_MPL = False

_MPL_CN_FONT = None  # lazy init


def _ensure_cn_font() -> bool:
    """Configure matplotlib to use a Chinese font. Returns True if OK."""
    global _MPL_CN_FONT
    if not _HAS_MPL:
        return False
    if _MPL_CN_FONT is not None:
        return _MPL_CN_FONT
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    found = None
    for c in candidates:
        if os.path.exists(c):
            found = c
            break
    if found:
        try:
            fm.fontManager.addfont(found)
            prop = fm.FontProperties(fname=found)
            family = prop.get_name()
            plt.rcParams["font.sans-serif"] = [family] + plt.rcParams.get("font.sans-serif", [])
            plt.rcParams["axes.unicode_minus"] = False
            _MPL_CN_FONT = True
        except Exception:
            _MPL_CN_FONT = False
    else:
        _MPL_CN_FONT = False
    return _MPL_CN_FONT


def _mpl_bar(data: dict | list, title: str, xlabel: str = "", ylabel: str = "",
             horizontal: bool = False, color: str = "#409EFF") -> bytes | None:
    """Render a bar chart as PNG bytes via matplotlib. Returns None if unavailable."""
    if not _HAS_MPL or not _ensure_cn_font():
        return None
    try:
        if isinstance(data, dict):
            labels = list(data.keys())
            values = [float(v) for v in data.values()]
        else:
            labels = [str(x[0]) for x in data]
            values = [float(x[1]) for x in data]
        fig, ax = plt.subplots(figsize=(7, 4.2), dpi=120)
        if horizontal:
            y_pos = list(range(len(labels)))
            bars = ax.barh(y_pos, values, color=color, edgecolor="white", height=0.6)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9)
            ax.invert_yaxis()
            for bar, v in zip(bars, values):
                ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                        f"{v:.1f}", va="center", fontsize=8, color="#333")
        else:
            x_pos = list(range(len(labels)))
            bars = ax.bar(x_pos, values, color=color, edgecolor="white", width=0.65)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, fontsize=9, rotation=15 if len(labels) > 5 else 0)
            for bar, v in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                        f"{v:.1f}", ha="center", fontsize=8, color="#333")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10)
        ax.grid(axis="y" if not horizontal else "x", linestyle="--", alpha=0.3)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def _mpl_hist(values: list, bins: int = 10, title: str = "",
              xlabel: str = "分数", color: str = "#67C23A") -> bytes | None:
    if not _HAS_MPL or not _ensure_cn_font():
        return None
    try:
        vals = [float(v) for v in values if v is not None]
        if not vals:
            return None
        fig, ax = plt.subplots(figsize=(7, 4.2), dpi=120)
        n, bins_arr, patches = ax.hist(vals, bins=bins, color=color, edgecolor="white", alpha=0.92)
        for cnt, p in zip(n, patches):
            if cnt > 0:
                ax.text(p.get_x() + p.get_width() / 2, p.get_height() + max(n) * 0.015,
                        f"{int(cnt)}", ha="center", fontsize=8, color="#333")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel("人数", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def _mpl_radar(dimension_scores: dict, title: str = "维度掌握率雷达图",
               score_range=(0, 100)) -> bytes | None:
    if not _HAS_MPL or not _ensure_cn_font():
        return None
    try:
        labels = list(dimension_scores.keys())
        values = [float(v) for v in dimension_scores.values()]
        if not labels:
            return None
        N = len(labels)
        angles = [n / float(N) * 2 * 3.14159265 for n in range(N)]
        angles += angles[:1]
        values += values[:1]
        fig, ax = plt.subplots(figsize=(6, 5.5), dpi=120, subplot_kw=dict(polar=True))
        ax.plot(angles, values, color="#E6A23C", linewidth=2, linestyle="solid")
        ax.fill(angles, values, color="#E6A23C", alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=10)
        ax.set_ylim(*score_range)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=24)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color="#999")
        ax.grid(alpha=0.4)
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def _mpl_heatmap(data: dict[tuple, float], row_labels: list, col_labels: list,
                 title: str = "维度均分热力图") -> bytes | None:
    """data: dict[(row_idx, col_idx)] -> score"""
    if not _HAS_MPL or not _ensure_cn_font():
        return None
    try:
        R, C = len(row_labels), len(col_labels)
        if R == 0 or C == 0:
            return None
        mat = np.full((R, C), np.nan, dtype=float)
        for (r, c), v in data.items():
            if 0 <= r < R and 0 <= c < C:
                mat[r, c] = float(v)
        fig, ax = plt.subplots(figsize=(max(6.5, C * 0.9), max(4.0, R * 0.55)),
                               dpi=120)
        im = ax.imshow(mat, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(C))
        ax.set_yticks(range(R))
        ax.set_xticklabels(col_labels, fontsize=9, rotation=20 if C > 5 else 0)
        ax.set_yticklabels(row_labels, fontsize=9)
        cbar = fig.colorbar(im, ax=ax, shrink=0.85)
        cbar.set_label("均分", fontsize=9)
        for r in range(R):
            for c in range(C):
                v = mat[r, c]
                if not np.isnan(v):
                    ax.text(c, r, f"{v:.0f}", ha="center", va="center",
                            fontsize=8,
                            color="white" if v > 70 else "#333")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def _save_png_tmp(png_bytes: bytes, suffix: str = "") -> str | None:
    """Save PNG bytes to a temp file. Caller responsible for cleanup if desired."""
    if not png_bytes:
        return None
    try:
        fd, path = tempfile.mkstemp(prefix="f1_", suffix=f"_{suffix}.png")
        with os.fdopen(fd, "wb") as f:
            f.write(png_bytes)
        return path
    except Exception:
        return None


def _ensure_xlsx():
    if not _HAS_OPENPYXL:
        raise RuntimeError("缺少依赖 openpyxl，请先安装 backend/requirements.txt")


def _ensure_docx():
    if not _HAS_DOCX:
        raise RuntimeError("缺少依赖 python-docx，请先安装 backend/requirements.txt")


def _ensure_fpdf():
    if not _HAS_FPDF:
        raise RuntimeError("缺少依赖 fpdf2，请先安装 backend/requirements.txt")


REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def generate_excel(filename, task_requirements, evaluation):
    """生成含图表的 Excel 评价报告"""
    _ensure_xlsx()
    wb = Workbook()
    ws = wb.active
    ws.title = "评价总览"

    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # 标题
    ws.merge_cells('A1:D1')
    ws['A1'] = "实训评价报告"
    ws['A1'].font = Font(size=16, bold=True, color="1F4E79")
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:D2')
    ws['A2'] = f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws['A2'].alignment = Alignment(horizontal='center')

    # 总分
    ws.merge_cells('A4:D4')
    ws['A4'] = f"综合评分：{evaluation['total']} 分"
    ws['A4'].font = Font(size=24, bold=True, color="409EFF")
    ws['A4'].alignment = Alignment(horizontal='center')

    level = "优秀" if evaluation['total'] >= 80 else "良好" if evaluation['total'] >= 60 else "需改进"
    ws.merge_cells('A5:D5')
    ws['A5'] = f"等级：{level}"
    ws['A5'].font = Font(size=14)
    ws['A5'].alignment = Alignment(horizontal='center')

    # 表头
    for col, val in zip(['A7', 'B7', 'C7', 'D7'], ['评价维度', '得分', '满分', '评分理由']):
        ws[col] = val
        ws[col].font = Font(size=12, bold=True, color="FFFFFF")
        ws[col].fill = PatternFill(start_color="409EFF", end_color="409EFF", fill_type="solid")
        ws[col].alignment = Alignment(horizontal='center')
        ws[col].border = thin_border

    # 数据行
    for i, score in enumerate(evaluation['scores']):
        row = 8 + i
        ws[f'A{row}'] = score['name']
        ws[f'B{row}'] = score['score']
        ws[f'C{row}'] = 100
        ws[f'D{row}'] = score['reason']
        for col in ['A', 'B', 'C', 'D']:
            ws[f'{col}{row}'].border = thin_border
            ws[f'{col}{row}'].alignment = Alignment(vertical='center', wrap_text=True)

    # 柱状图
    last_row = 8 + len(evaluation['scores']) - 1
    chart = BarChart()
    chart.type = "col"
    chart.title = "各维度评分对比"
    chart.y_axis.title = "分数"
    chart.style = 10
    chart.width = 18
    chart.height = 12

    data = Reference(ws, min_col=2, min_row=7, max_row=last_row, max_col=2)
    cats = Reference(ws, min_col=1, min_row=8, max_row=last_row)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)

    ws.add_chart(chart, f"A{last_row + 3}")

    # 总评
    cr = last_row + 20
    ws.merge_cells(f'A{cr}:D{cr}')
    ws[f'A{cr}'] = "AI 总评"
    ws[f'A{cr}'].font = Font(size=12, bold=True)
    ws.merge_cells(f'A{cr+1}:D{cr+3}')
    ws[f'A{cr+1}'] = evaluation['comment']
    ws[f'A{cr+1}'].alignment = Alignment(wrap_text=True, vertical='top')

    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 45

    filepath = os.path.join(REPORT_DIR, filename)
    wb.save(filepath)
    return filepath


def generate_word(filename, task_requirements, evaluation, student_name="学生"):
    """生成 Word 评价报告"""
    _ensure_docx()
    doc = Document()

    # 标题
    doc.add_heading('实训评价报告', 0)

    # 基本信息
    doc.add_paragraph(f'学生姓名：{student_name}')
    doc.add_paragraph(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    doc.add_paragraph('')

    # 总分
    doc.add_paragraph(f'综合评分：{evaluation["total"]} 分', style='Intense Quote')
    level = "优秀" if evaluation['total'] >= 80 else "良好" if evaluation['total'] >= 60 else "需改进"
    doc.add_paragraph(f'评价等级：{level}')
    doc.add_paragraph('')

    # 各维度评分
    doc.add_heading('各维度详细评分', level=1)

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = '评价维度'
    hdr[1].text = '得分'
    hdr[2].text = '评分理由'

    for s in evaluation['scores']:
        row = table.add_row().cells
        row[0].text = s['name']
        row[1].text = f"{s['score']}分"
        row[2].text = s['reason']

    doc.add_paragraph('')

    # 总评
    doc.add_heading('AI 综合评价', level=1)
    doc.add_paragraph(evaluation['comment'])

    doc.add_paragraph('')

    # 实训要求
    doc.add_heading('实训要求', level=1)
    doc.add_paragraph(task_requirements)

    filepath = os.path.join(REPORT_DIR, filename)
    doc.save(filepath)
    return filepath


def generate_pdf(filename, task_requirements, evaluation, student_name="学生"):
    _ensure_fpdf()
    pdf = FPDF()
    pdf.add_page()

    # 注册中文字体
    font_path = "C:/Windows/Fonts/simsun.ttc"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/msyh.ttc"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/simhei.ttf"

    pdf.add_font("CN", "", font_path, uni=True)
    pdf.add_font("CN", "B", font_path, uni=True)

    filepath = os.path.join(REPORT_DIR, filename)

    # 标题
    pdf.set_font("CN", "B", 22)
    pdf.cell(0, 15, "实训评价报告", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 基本信息
    pdf.set_font("CN", "", 11)
    pdf.cell(0, 8, f"学生：{student_name}    生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # 总分
    pdf.set_font("CN", "B", 48)
    pdf.cell(0, 20, f"{evaluation['total']}分", align="C", new_x="LMARGIN", new_y="NEXT")

    level = "优秀" if evaluation['total'] >= 80 else "良好" if evaluation['total'] >= 60 else "需改进"
    pdf.set_font("CN", "B", 16)
    pdf.cell(0, 12, level, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # 各维度评分
    pdf.set_font("CN", "B", 14)
    pdf.cell(0, 10, "各维度详细评分", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    for s in evaluation.get("scores", []):
        pdf.set_font("CN", "B", 12)
        pdf.cell(0, 8, f"{s['name']}：{s['score']}分", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("CN", "", 10)
        pdf.multi_cell(0, 6, s.get("reason", ""))
        pdf.ln(3)

    # 总评
    pdf.ln(3)
    pdf.set_font("CN", "B", 14)
    pdf.cell(0, 10, "AI 综合评价", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("CN", "", 11)
    pdf.multi_cell(0, 7, evaluation.get("comment", ""))

    # 实训要求
    pdf.ln(5)
    pdf.set_font("CN", "B", 14)
    pdf.cell(0, 10, "实训要求", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("CN", "", 10)
    pdf.multi_cell(0, 6, task_requirements)

    pdf.output(filepath)
    return filepath

def generate_batch_excel(filename, req, db):
    """生成全班成绩汇总Excel"""
    _ensure_xlsx()
    from app.models.tables import User
    from app.models.class_models import ClassMember
    from app.models.tables import Evaluation, Submission
    from app.models.class_models import ClassMember

    class_id = req.get("class_id")
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "班级成绩汇总"

    # 标题
    ws.merge_cells('A1:F1')
    ws['A1'] = "班级成绩汇总表"
    ws['A1'].font = Font(size=16, bold=True, color="1F4E79")
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:F2')
    ws['A2'] = f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws['A2'].alignment = Alignment(horizontal='center')

    # 表头
    headers = ['排名', '学号', '姓名', '提交次数', 'AI平均分', '教师平均分']
    header_fill = PatternFill(start_color="409EFF", end_color="409EFF", fill_type="solid")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                         top=Side(style='thin'), bottom=Side(style='thin'))

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = Font(size=12, bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    # 数据行
    student_data = []
    for m in members:
        evals = db.query(Evaluation.total_score, Evaluation.evaluator_type).join(
            Submission, Evaluation.submission_id == Submission.id
        ).filter(Submission.student_id == m.student_id).all()

        ai_scores = [float(e.total_score) for e in evals if e.evaluator_type == "ai"]
        teacher_scores = [float(e.total_score) for e in evals if e.evaluator_type == "teacher"]

        student_data.append({
            "name": m.student_name,
            "number": m.student_number or "",
            "submit_count": len(ai_scores),
            "avg_ai": round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else 0,
            "avg_teacher": round(sum(teacher_scores) / len(teacher_scores), 1) if teacher_scores else 0
        })

    student_data.sort(key=lambda x: x["avg_ai"], reverse=True)

    for i, s in enumerate(student_data):
        row = 5 + i
        values = [i + 1, s["number"], s["name"], s["submit_count"], s["avg_ai"], s["avg_teacher"]]
        for col, v in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')

    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 16
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 14

    filepath = os.path.join(REPORT_DIR, filename)
    wb.save(filepath)
    return filepath


# ============================================================
#  F1: Data collection layer
# ============================================================
def _collect_class_stats(class_id: int, db):
    """Build a large stats dict for class report generation.

    Returns dict with keys:
      class_info, members, tasks, per_student (student_id -> {...}),
      per_task (task_id -> {...}), all_totals (list[float]),
      dim_overall_avg (dict dim->avg), task_dim_heatmap {...},
      top_students (list[student_id]), bottom_students (list[student_id]),
      weak_dims (list[(dim, avg, warn)]), submit_stats (submitted, missing)
    """
    from app.models.class_models import Class, ClassMember
    from app.models.tables import Submission, Evaluation, Task, User

    cls = db.query(Class).filter(Class.id == class_id).first()
    if cls is None:
        raise ValueError(f"class_id={class_id} not found")
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()
    student_ids = [m.student_id for m in members]
    id_to_member = {m.student_id: m for m in members}

    # Map class_id (INT) to Task.class_id (CSV of ints as VARCHAR)
    cid_str = str(class_id)
    tasks_raw = db.query(Task).all()
    tasks = [t for t in tasks_raw if t.class_id and (
        t.class_id == cid_str or
        (cid_str in set(x.strip() for x in str(t.class_id).split(",")))
    )]
    task_ids = [t.id for t in tasks]

    per_student = {}
    for sid in student_ids:
        per_student[sid] = {
            "student_id": sid,
            "name": id_to_member[sid].student_name or f"学号{sid}",
            "number": id_to_member[sid].student_number or "",
            "submissions": [],
            "task_totals": {},
            "task_eval_ai": {},
            "task_eval_teacher": {},
            "dims_raw": defaultdict(list),
            "last_n_total": [],
        }

    all_totals: list[float] = []
    task_eval_map: dict[int, dict] = {t.id: {"subs": [], "ai_totals": [], "teacher_totals": [],
                                              "dim_scores": defaultdict(list)}
                                     for t in tasks}
    submit_count = 0

    for t in tasks:
        subs = db.query(Submission).filter(
            Submission.task_id == t.id,
            Submission.student_id.in_(student_ids)
        ).all()
        for s in subs:
            ps = per_student.get(s.student_id)
            if ps is None:
                continue
            ps["submissions"].append(s.id)
            evals = db.query(Evaluation).filter(Evaluation.submission_id == s.id).all()
            ev_ai = next((e for e in evals if e.evaluator_type == "ai"), None)
            ev_teacher = next((e for e in evals if e.evaluator_type == "teacher"), None)
            chosen = ev_teacher or ev_ai
            chosen_score = float(chosen.total_score) if (chosen and chosen.total_score is not None) else None
            if chosen_score is not None:
                ps["task_totals"][t.id] = chosen_score
                ps["last_n_total"].append(chosen_score)
                all_totals.append(chosen_score)
                task_eval_map[t.id]["subs"].append(s.id)
                dims = chosen.dimension_scores or {}
                if isinstance(dims, dict):
                    for name, score in dims.items():
                        try:
                            fscore = float(score["score"] if isinstance(score, dict) else score)
                        except Exception:
                            continue
                        ps["dims_raw"][name].append(fscore)
                        task_eval_map[t.id]["dim_scores"][name].append(fscore)
                if ev_ai and ev_ai.total_score is not None:
                    task_eval_map[t.id]["ai_totals"].append(float(ev_ai.total_score))
                if ev_teacher and ev_teacher.total_score is not None:
                    task_eval_map[t.id]["teacher_totals"].append(float(ev_teacher.total_score))
            if ev_ai:
                ps["task_eval_ai"][t.id] = ev_ai.id
            if ev_teacher:
                ps["task_eval_teacher"][t.id] = ev_teacher.id
            submit_count += 1

    for sid, ps in per_student.items():
        ps["dim_avg"] = {d: round(sum(vs) / len(vs), 2)
                         for d, vs in ps["dims_raw"].items() if vs}
        ps["overall_avg"] = round(sum(ps["task_totals"].values()) / len(ps["task_totals"]), 2) \
            if ps["task_totals"] else 0.0
        ps["submit_count"] = len(ps["task_totals"])

    dim_bucket: dict[str, list[float]] = defaultdict(list)
    for ps in per_student.values():
        for d, vs in ps["dims_raw"].items():
            dim_bucket[d].extend(vs)
    dim_overall_avg = {d: round(sum(vs) / len(vs), 2) for d, vs in dim_bucket.items() if vs}

    all_dim_names = sorted(dim_overall_avg.keys())
    task_dim_heatmap = {"row_labels": [], "col_labels": all_dim_names, "values": {}}
    for ti, t in enumerate(tasks):
        task_dim_heatmap["row_labels"].append(
            t.title[:18] + ("..." if len(t.title) > 18 else ""))
        ts = task_eval_map.get(t.id, {}).get("dim_scores", {})
        for di, d in enumerate(all_dim_names):
            vs = ts.get(d)
            if vs:
                task_dim_heatmap["values"][(ti, di)] = round(sum(vs) / len(vs), 2)

    ranked = sorted(per_student.values(), key=lambda p: p["overall_avg"], reverse=True)
    top_students = [x["student_id"] for x in ranked[:5] if x["submit_count"] > 0]
    bottom_students = [x["student_id"] for x in ranked[-5:] if x["submit_count"] > 0]

    weak_dims = []
    for d, avg in dim_overall_avg.items():
        flag = "严重" if avg < 60 else ("警告" if avg < 70 else "正常")
        if flag != "正常":
            weak_dims.append((d, avg, flag))
    weak_dims.sort(key=lambda x: x[1])

    expected_submits = len(student_ids) * len(tasks)
    submit_stats = {
        "total_students": len(student_ids),
        "total_tasks": len(tasks),
        "expected_submits": expected_submits,
        "actual_submits": submit_count,
        "completion_rate": round(submit_count * 100.0 / expected_submits, 2) if expected_submits else 0.0,
        "class_overall_avg": round(sum(all_totals) / len(all_totals), 2) if all_totals else 0.0,
        "pass_rate": round(sum(1 for x in all_totals if x >= 60) * 100.0 / len(all_totals), 2) if all_totals else 0.0,
    }

    per_task_out = {}
    for t in tasks:
        tm = task_eval_map[t.id]
        totals_all = tm["teacher_totals"] or tm["ai_totals"]
        per_task_out[t.id] = {
            "task_id": t.id,
            "title": t.title,
            "count": len(totals_all),
            "avg": round(sum(totals_all) / len(totals_all), 2) if totals_all else 0.0,
            "max": round(max(totals_all), 2) if totals_all else 0.0,
            "min": round(min(totals_all), 2) if totals_all else 0.0,
            "dim_avg": {d: round(sum(vs) / len(vs), 2) for d, vs in tm["dim_scores"].items() if vs},
        }

    return {
        "class_info": {
            "id": cls.id, "name": cls.name, "grade": cls.grade or "",
            "major": cls.major or "", "course_name": cls.course_name or "",
            "semester": cls.semester or "", "teacher_name": cls.teacher_name or "",
            "student_count": len(student_ids),
        },
        "members": members,
        "tasks": tasks,
        "per_student": per_student,
        "per_task": per_task_out,
        "all_totals": all_totals,
        "dim_overall_avg": dim_overall_avg,
        "task_dim_heatmap": task_dim_heatmap,
        "top_students": top_students,
        "bottom_students": bottom_students,
        "weak_dims": weak_dims,
        "submit_stats": submit_stats,
    }


def _collect_school_stats(db):
    """Collect stats across all classes = 'school overview'."""
    from app.models.class_models import Class

    classes = db.query(Class).filter(Class.status == "active").all()
    per_class = {}
    dim_bucket: dict[str, list[float]] = defaultdict(list)
    teacher_raw: dict[str, dict] = defaultdict(
        lambda: {"class_count": 0, "scores": [], "students": 0})
    course_raw: dict[str, dict] = defaultdict(
        lambda: {"class_count": 0, "scores": [], "cls_ids": set()})
    all_scores: list[float] = []

    for cls in classes:
        cs = _collect_class_stats(cls.id, db)
        ss = cs["submit_stats"]
        per_class[cls.id] = {
            "id": cls.id,
            "name": cls.name,
            "course": cls.course_name or "未命名课程",
            "teacher": cls.teacher_name or f"教师{cls.teacher_id}",
            "student_count": ss["total_students"],
            "task_count": ss["total_tasks"],
            "overall_avg": ss["class_overall_avg"],
            "pass_rate": ss["pass_rate"],
            "completion_rate": ss["completion_rate"],
            "weak_dims": [d for d, _, _ in cs["weak_dims"]],
        }
        for d, avg in cs["dim_overall_avg"].items():
            dim_bucket[d].append(avg)
        tn = cls.teacher_name or f"教师{cls.teacher_id}"
        if cs["all_totals"]:
            teacher_raw[tn]["class_count"] += 1
            teacher_raw[tn]["scores"].extend(cs["all_totals"])
            all_scores.extend(cs["all_totals"])
        teacher_raw[tn]["students"] += ss["total_students"]
        course_name = cls.course_name or "未命名课程"
        if cs["all_totals"]:
            course_raw[course_name]["class_count"] += 1
            course_raw[course_name]["scores"].extend(cs["all_totals"])
        course_raw[course_name]["cls_ids"].add(cls.id)

    dim_overall_avg = {d: round(sum(vs) / len(vs), 2) for d, vs in dim_bucket.items() if vs}

    teacher_stats = {}
    for tn, v in teacher_raw.items():
        scores = v["scores"]
        teacher_stats[tn] = {
            "name": tn,
            "class_count": v["class_count"],
            "student_count": v["students"],
            "overall_avg": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "pass_rate": round(sum(1 for x in scores if x >= 60) * 100.0 / len(scores), 2) if scores else 0.0,
        }

    course_stats = {}
    for cn, v in course_raw.items():
        scores = v["scores"]
        course_stats[cn] = {
            "course": cn,
            "class_count": len(v["cls_ids"]),
            "overall_avg": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "pass_rate": round(sum(1 for x in scores if x >= 60) * 100.0 / len(scores), 2) if scores else 0.0,
        }

    school_level = {
        "class_count": len(classes),
        "student_count": sum(p["student_count"] for p in per_class.values()),
        "overall_avg": round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0,
        "pass_rate": round(sum(1 for x in all_scores if x >= 60) * 100.0 / len(all_scores), 2) if all_scores else 0.0,
        "submission_count": len(all_scores),
    }

    return {
        "classes": classes,
        "per_class": per_class,
        "dim_overall_avg": dim_overall_avg,
        "teacher_stats": teacher_stats,
        "course_stats": course_stats,
        "school_level": school_level,
    }


# ============================================================
#  F1: Class report (PDF + Excel)
# ============================================================
def _register_cn_fonts(pdf) -> tuple[str, str]:
    """Register Chinese fonts with fpdf2; fallback to Helvetica."""
    font_path = None
    for c in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc",
              "C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(c):
            font_path = c
            break
    if font_path is None:
        for c in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]:
            if os.path.exists(c):
                font_path = c
                break
    try:
        pdf.add_font("CN", "", font_path, uni=True)
        pdf.add_font("CN", "B", font_path, uni=True)
        return "CN", "CN"
    except Exception:
        return "Helvetica", "Helvetica"


def _safe_cn(text, limit: int | None = None) -> str:
    if text is None:
        return ""
    s = str(text)
    if limit and len(s) > limit:
        s = s[:limit] + "..."
    return s


def _pdf_add_image_if(pdf, png_bytes: bytes, w: int = 180, h: int | None = None,
                      cleanup_paths: list | None = None) -> bool:
    if not png_bytes:
        return False
    path = _save_png_tmp(
        png_bytes, suffix=hex(abs(hash(datetime.now().timestamp())))[:8])
    if not path:
        return False
    try:
        if h:
            pdf.image(path, w=w, h=h)
        else:
            pdf.image(path, w=w)
        if cleanup_paths is not None:
            cleanup_paths.append(path)
        return True
    except Exception:
        return False


def generate_class_report_pdf(filename: str, class_id: int, db) -> str:
    _ensure_fpdf()
    stats = _collect_class_stats(class_id, db)
    ci = stats["class_info"]
    ss = stats["submit_stats"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    fn, fnb = _register_cn_fonts(pdf)
    pdf.add_page()
    tmp_files: list[str] = []

    pdf.set_font(fn, "B", 20)
    pdf.cell(0, 14, _safe_cn(f"{ci['name']} - 班级教学质量画像报告"), align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fn, "", 11)
    pdf.cell(0, 7, _safe_cn(
        f"课程：{ci['course_name']}   专业：{ci['major']}   年级：{ci['grade']}   "
        f"学期：{ci['semester']}   教师：{ci['teacher_name']}"),
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_cn(
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}   "
        f"学生数：{ss['total_students']} 人   任务数：{ss['total_tasks']} 个"),
        align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font(fn, "B", 12)
    pdf.cell(0, 7, "核心指标概览", new_x="LMARGIN", new_y="NEXT")
    cards = [
        ("班级均分", f"{ss['class_overall_avg']:.2f} 分"),
        ("及格率", f"{ss['pass_rate']:.2f} %"),
        ("提交完成率", f"{ss['completion_rate']:.2f} %"),
        ("累计提交数", f"{ss['actual_submits']} / {ss['expected_submits']}"),
    ]
    col_w = pdf.epw / 4
    pdf.set_font(fn, "B", 13)
    for (k, v) in cards:
        pdf.cell(col_w, 9, _safe_cn(v), border=1, align="C",
                 new_x="RIGHT", new_y="TOP")
    pdf.ln(10)
    pdf.set_font(fn, "", 10)
    for (k, v) in cards:
        pdf.cell(col_w, 6, _safe_cn(k), align="C", new_x="RIGHT", new_y="TOP")
    pdf.ln(12)

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "一、全班综合成绩分布", new_x="LMARGIN", new_y="NEXT")
    hist_png = _mpl_hist(
        stats["all_totals"], bins=10,
        title=f"{_safe_cn(ci['name'])} 综合成绩分布直方图")
    if _pdf_add_image_if(pdf, hist_png, w=175, cleanup_paths=tmp_files):
        pdf.ln(8)
    else:
        pdf.set_font(fn, "", 10)
        pdf.multi_cell(0, 6, "  （图表组件不可用：请 pip install matplotlib）")
        pdf.ln(4)

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "二、各评价维度掌握情况（全班均分）", new_x="LMARGIN", new_y="NEXT")
    dim_avg_sorted = dict(sorted(stats["dim_overall_avg"].items(), key=lambda kv: kv[1]))
    bar_png = _mpl_bar(dim_avg_sorted, title="班级各维度均分排行",
                       xlabel="均分", ylabel="评价维度", horizontal=True, color="#67C23A")
    if _pdf_add_image_if(pdf, bar_png, w=175, cleanup_paths=tmp_files):
        pdf.ln(8)
    else:
        pdf.set_font(fn, "", 10)
        for d, v in dim_avg_sorted.items():
            pdf.cell(0, 6, _safe_cn(f"  · {d}：{v:.2f}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    pdf.add_page()
    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "三、任务 × 维度均分热力图", new_x="LMARGIN", new_y="NEXT")
    hm = stats["task_dim_heatmap"]
    hm_png = _mpl_heatmap(
        hm["values"], hm["row_labels"], hm["col_labels"],
        title="任务 × 维度均分热力图（颜色越深掌握越好）")
    if _pdf_add_image_if(pdf, hm_png, w=180, cleanup_paths=tmp_files):
        pdf.ln(8)

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "四、全班维度掌握雷达图", new_x="LMARGIN", new_y="NEXT")
    rd_png = _mpl_radar(stats["dim_overall_avg"],
                        title=f"{_safe_cn(ci['name'])} 维度掌握雷达图")
    if _pdf_add_image_if(pdf, rd_png, w=150, cleanup_paths=tmp_files):
        pdf.ln(8)

    pdf.add_page()
    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "五、Top 5 / 待关注 Bottom 5", new_x="LMARGIN", new_y="NEXT")

    def _rank_block(title: str, ids: list):
        pdf.set_font(fn, "B", 11)
        pdf.cell(0, 7, _safe_cn(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(fn, "", 10)
        if not ids:
            pdf.cell(0, 6, "  暂无足够数据", new_x="LMARGIN", new_y="NEXT")
            return
        rows = []
        for sid in ids:
            ps = stats["per_student"][sid]
            rows.append((ps["name"], ps["number"], ps["overall_avg"], ps["submit_count"]))
        pdf.set_font(fn, "B", 10)
        header = ["排名", "姓名", "学号", "均分", "提交次数"]
        ws = [14, 40, 42, 30, 30]
        for w, h in zip(ws, header):
            pdf.cell(w, 7, _safe_cn(h), border=1, align="C",
                     new_x="RIGHT", new_y="TOP")
        pdf.ln(7)
        pdf.set_font(fn, "", 10)
        for i, (nm, nb, sc, cnt) in enumerate(rows, 1):
            vals = [str(i), _safe_cn(nm, 10), _safe_cn(nb, 14), f"{sc:.2f}", str(cnt)]
            for w, v in zip(ws, vals):
                pdf.cell(w, 7, _safe_cn(v), border=1, align="C",
                         new_x="RIGHT", new_y="TOP")
            pdf.ln(7)
        pdf.ln(4)

    _rank_block("5.1 班级 Top 5（均分由高到低）", stats["top_students"])
    _rank_block("5.2 班级 Bottom 5（待关注）", stats["bottom_students"])

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "六、薄弱维度预警（均分 < 70）", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fn, "", 10)
    if not stats["weak_dims"]:
        pdf.cell(0, 6, "  暂无预警，所有维度均分 >= 70，班级掌握情况良好。",
                 new_x="LMARGIN", new_y="NEXT")
    else:
        header = ["维度名", "均分", "预警等级"]
        ws = [70, 50, 50]
        pdf.set_font(fn, "B", 10)
        for w, h in zip(ws, header):
            pdf.cell(w, 7, _safe_cn(h), border=1, align="C",
                     new_x="RIGHT", new_y="TOP")
        pdf.ln(7)
        pdf.set_font(fn, "", 10)
        for d, avg, flag in stats["weak_dims"]:
            vals = [_safe_cn(d, 20), f"{avg:.2f}", flag]
            for w, v in zip(ws, vals):
                pdf.cell(w, 7, _safe_cn(v), border=1, align="C",
                         new_x="RIGHT", new_y="TOP")
            pdf.ln(7)
        pdf.ln(3)
        pdf.cell(0, 6,
                 "  建议：教师可针对上述薄弱维度，补充专项讲解、布置针对性练习、或一对一辅导。",
                 new_x="LMARGIN", new_y="NEXT")

    filepath = os.path.join(REPORT_DIR, filename)
    pdf.output(filepath)
    for p in tmp_files:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    return filepath


def generate_class_report_excel(filename: str, class_id: int, db) -> str:
    _ensure_xlsx()
    stats = _collect_class_stats(class_id, db)
    ci = stats["class_info"]
    ss = stats["submit_stats"]
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'))
    hdr_fill = PatternFill(start_color="409EFF", end_color="409EFF", fill_type="solid")
    hdr_font = Font(size=11, bold=True, color="FFFFFF")
    warn_fill = PatternFill(start_color="FFECEC", end_color="FFECEC", fill_type="solid")

    wb = Workbook()

    ws = wb.active
    ws.title = "班级概览"
    ws.merge_cells('A1:G1')
    ws['A1'] = f"{ci['name']} - 班级教学质量画像报告"
    ws['A1'].font = Font(size=16, bold=True, color="1F4E79")
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.merge_cells('A2:G2')
    ws['A2'] = (f"课程：{ci['course_name']}  专业：{ci['major']}  年级：{ci['grade']}  "
                f"学期：{ci['semester']}  教师：{ci['teacher_name']}  "
                f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    ws['A2'].alignment = Alignment(horizontal='center', wrap_text=True)

    for col, (k, v) in enumerate([
        ("班级均分", f"{ss['class_overall_avg']:.2f}"),
        ("及格率", f"{ss['pass_rate']:.2f}%"),
        ("提交完成率", f"{ss['completion_rate']:.2f}%"),
        ("累计提交数", f"{ss['actual_submits']}/{ss['expected_submits']}"),
    ], start=1):
        c1 = ws.cell(row=4, column=col, value=f"{k}: {v}")
        c1.font = Font(size=12, bold=True, color="1F4E79")

    r = 7
    ws.cell(row=r, column=1, value="Top 5 学生").font = Font(size=12, bold=True)
    r += 1
    headers = ["排名", "姓名", "学号", "均分", "提交次数"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    r += 1
    for i, sid in enumerate(stats["top_students"], 1):
        ps = stats["per_student"][sid]
        row_data = [i, ps["name"], ps["number"], ps["overall_avg"], ps["submit_count"]]
        for c, v in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Bottom 5 待关注").font = Font(size=12, bold=True)
    r += 1
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    r += 1
    for i, sid in enumerate(stats["bottom_students"], 1):
        ps = stats["per_student"][sid]
        row_data = [i, ps["name"], ps["number"], ps["overall_avg"], ps["submit_count"]]
        for c, v in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
            cell.fill = warn_fill
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="薄弱维度预警").font = Font(size=12, bold=True)
    r += 1
    hdrs2 = ["维度", "均分", "预警等级"]
    for c, h in enumerate(hdrs2, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    r += 1
    for d, avg, flag in stats["weak_dims"]:
        for c, v in enumerate([d, avg, flag], 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
            if flag == "严重":
                cell.fill = warn_fill
        r += 1

    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 22
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 18

    ws2 = wb.create_sheet("各维度均分")
    dim_sorted = sorted(stats["dim_overall_avg"].items(), key=lambda x: x[1], reverse=True)
    ws2.cell(row=1, column=1, value="维度名").fill = hdr_fill
    ws2.cell(row=1, column=1).font = hdr_font
    ws2.cell(row=1, column=2, value="均分").fill = hdr_fill
    ws2.cell(row=1, column=2).font = hdr_font
    for i, (d, v) in enumerate(dim_sorted, 2):
        ws2.cell(row=i, column=1, value=d).border = thin_border
        ws2.cell(row=i, column=2, value=v).border = thin_border
    if dim_sorted:
        chart = BarChart()
        chart.type = "col"
        chart.title = "全班各维度均分"
        chart.y_axis.title = "分数"
        chart.style = 10
        chart.width = 18
        chart.height = 12
        data_ref = Reference(ws2, min_col=2, min_row=1, max_row=1 + len(dim_sorted))
        cat_ref = Reference(ws2, min_col=1, min_row=2, max_row=1 + len(dim_sorted))
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cat_ref)
        ws2.add_chart(chart, "D2")

    ws3 = wb.create_sheet("任务均分明细")
    task_rows = []
    for t in stats["tasks"]:
        o = stats["per_task"].get(t.id, {})
        task_rows.append((t.title, o.get("count", 0), o.get("avg", 0),
                          o.get("max", 0), o.get("min", 0)))
    hdrs3 = ["任务名", "提交数", "均分", "最高分", "最低分"]
    for c, h in enumerate(hdrs3, 1):
        cell = ws3.cell(row=1, column=c, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    for i, row in enumerate(task_rows, 2):
        for c, v in enumerate(row, 1):
            cell = ws3.cell(row=i, column=c, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
    if task_rows:
        chart = BarChart()
        chart.type = "col"
        chart.title = "各任务均分对比"
        chart.y_axis.title = "均分"
        chart.width = 18
        chart.height = 12
        data_ref = Reference(ws3, min_col=3, min_row=1, max_row=1 + len(task_rows))
        cat_ref = Reference(ws3, min_col=1, min_row=2, max_row=1 + len(task_rows))
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cat_ref)
        ws3.add_chart(chart, "G2")

    ws2.column_dimensions['A'].width = 22
    ws2.column_dimensions['B'].width = 12
    ws3.column_dimensions['A'].width = 40
    ws3.column_dimensions['B'].width = 12
    ws3.column_dimensions['C'].width = 12
    ws3.column_dimensions['D'].width = 12
    ws3.column_dimensions['E'].width = 12

    filepath = os.path.join(REPORT_DIR, filename)
    wb.save(filepath)
    return filepath


def generate_class_report(filename: str, class_id: int, db, fmt: str = "pdf") -> str:
    fmt = (fmt or "pdf").lower()
    if fmt in ("xlsx", "excel"):
        return generate_class_report_excel(filename, class_id, db)
    return generate_class_report_pdf(filename, class_id, db)


# ============================================================
#  F1: School overview report (PDF + Excel)
# ============================================================
def generate_school_report_pdf(filename: str, db) -> str:
    _ensure_fpdf()
    stats = _collect_school_stats(db)
    sl = stats["school_level"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    fn, fnb = _register_cn_fonts(pdf)
    pdf.add_page()
    tmp_files: list[str] = []

    pdf.set_font(fn, "B", 20)
    pdf.cell(0, 14, "校级教学质量总览报告", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fn, "", 11)
    pdf.cell(0, 7, f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}   "
             f"报告层级：校级（全校所有活跃班级聚合）",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font(fn, "B", 12)
    pdf.cell(0, 7, "校级核心指标", new_x="LMARGIN", new_y="NEXT")
    cards = [
        ("班级数", f"{sl['class_count']} 个"),
        ("覆盖学生数", f"{sl['student_count']} 人"),
        ("全校均分", f"{sl['overall_avg']:.2f} 分"),
        ("全校及格率", f"{sl['pass_rate']:.2f} %"),
    ]
    col_w = pdf.epw / 4
    pdf.set_font(fn, "B", 13)
    for (k, v) in cards:
        pdf.cell(col_w, 9, _safe_cn(v), border=1, align="C", new_x="RIGHT", new_y="TOP")
    pdf.ln(10)
    pdf.set_font(fn, "", 10)
    for (k, v) in cards:
        pdf.cell(col_w, 6, _safe_cn(k), align="C", new_x="RIGHT", new_y="TOP")
    pdf.ln(14)

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "一、各课程横向均分对比", new_x="LMARGIN", new_y="NEXT")
    cs = sorted(stats["course_stats"].items(), key=lambda x: x[1]["overall_avg"])
    course_avg = {cn: d["overall_avg"] for cn, d in cs if d["overall_avg"] > 0}
    p1 = _mpl_bar(course_avg, title="各课程横向均分对比",
                  xlabel="均分", ylabel="课程", horizontal=True, color="#409EFF")
    if _pdf_add_image_if(pdf, p1, w=175, cleanup_paths=tmp_files):
        pdf.ln(8)

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "二、教师教学质量排名（按均分）", new_x="LMARGIN", new_y="NEXT")
    ts_sorted = sorted(stats["teacher_stats"].items(), key=lambda x: x[1]["overall_avg"])
    teacher_avg = {tn: d["overall_avg"] for tn, d in ts_sorted if d["overall_avg"] > 0}
    p2 = _mpl_bar(teacher_avg, title="教师教学质量排名",
                  xlabel="均分", ylabel="教师", horizontal=True, color="#E6A23C")
    if _pdf_add_image_if(pdf, p2, w=175, cleanup_paths=tmp_files):
        pdf.ln(8)

    pdf.add_page()
    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "三、全校维度掌握率雷达图", new_x="LMARGIN", new_y="NEXT")
    rd = _mpl_radar(stats["dim_overall_avg"], title="全校维度掌握率雷达图")
    if _pdf_add_image_if(pdf, rd, w=150, cleanup_paths=tmp_files):
        pdf.ln(8)

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "四、各班级及格率对比", new_x="LMARGIN", new_y="NEXT")
    pc_sorted = sorted(stats["per_class"].items(), key=lambda x: x[1]["pass_rate"], reverse=True)
    cls_passrate = {}
    for cid, pc in pc_sorted:
        label = pc["name"]
        cls_passrate[label[:22] + ("..." if len(label) > 22 else "")] = pc["pass_rate"]
    p3 = _mpl_bar(cls_passrate, title="各班级及格率对比 (%)",
                  xlabel="班级", ylabel="及格率 %", horizontal=False, color="#67C23A")
    if _pdf_add_image_if(pdf, p3, w=180, cleanup_paths=tmp_files):
        pdf.ln(8)

    pdf.set_font(fn, "B", 13)
    pdf.cell(0, 9, "五、各班级汇总表", new_x="LMARGIN", new_y="NEXT")
    hdr = ["班级名", "课程", "教师", "学生数", "均分", "及格率", "完成率"]
    widths = [50, 42, 32, 18, 22, 24, 24]
    pdf.set_font(fn, "B", 9)
    for w, h in zip(widths, hdr):
        pdf.cell(w, 7, _safe_cn(h), border=1, align="C", new_x="RIGHT", new_y="TOP")
    pdf.ln(7)
    pdf.set_font(fn, "", 8)
    for cid, pc in pc_sorted:
        row = [pc["name"], pc["course"], pc["teacher"],
               str(pc["student_count"]), f"{pc['overall_avg']:.2f}",
               f"{pc['pass_rate']:.2f}%", f"{pc['completion_rate']:.2f}%"]
        for w, v in zip(widths, row):
            pdf.cell(w, 6, _safe_cn(v, 20), border=1, align="C", new_x="RIGHT", new_y="TOP")
        pdf.ln(6)

    filepath = os.path.join(REPORT_DIR, filename)
    pdf.output(filepath)
    for p in tmp_files:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    return filepath


def generate_school_report_excel(filename: str, db) -> str:
    _ensure_xlsx()
    stats = _collect_school_stats(db)
    sl = stats["school_level"]
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'))
    hdr_fill = PatternFill(start_color="409EFF", end_color="409EFF", fill_type="solid")
    hdr_font = Font(size=11, bold=True, color="FFFFFF")

    wb = Workbook()
    ws = wb.active
    ws.title = "校级总览"
    ws.merge_cells('A1:G1')
    ws['A1'] = "校级教学质量总览报告"
    ws['A1'].font = Font(size=16, bold=True, color="1F4E79")
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.merge_cells('A2:G2')
    ws['A2'] = (f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}   "
                f"报告维度：全校所有活跃班级聚合")
    ws['A2'].alignment = Alignment(horizontal='center')

    cards = [("班级数", sl["class_count"]),
             ("覆盖学生数", sl["student_count"]),
             ("全校均分", f"{sl['overall_avg']:.2f}"),
             ("全校及格率", f"{sl['pass_rate']:.2f}%"),
             ("累计评价数", sl["submission_count"])]
    for col, (k, v) in enumerate(cards, 1):
        cell = ws.cell(row=4, column=col, value=f"{k}: {v}")
        cell.font = Font(size=12, bold=True, color="1F4E79")

    ws2 = wb.create_sheet("课程横向对比")
    cs_sorted = sorted(stats["course_stats"].items(), key=lambda x: x[1]["overall_avg"], reverse=True)
    hdrs2 = ["课程名", "班级数", "均分", "及格率"]
    for c, h in enumerate(hdrs2, 1):
        cell = ws2.cell(row=1, column=c, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    for i, (cn, d) in enumerate(cs_sorted, 2):
        for c, v in enumerate([cn, d["class_count"], round(d["overall_avg"], 2),
                              f"{d['pass_rate']:.2f}%"], 1):
            cell = ws2.cell(row=i, column=c, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
    if cs_sorted:
        chart = BarChart()
        chart.type = "bar"
        chart.title = "各课程横向均分对比"
        chart.style = 10
        chart.width = 18
        chart.height = max(10, min(18, 6 + int(len(cs_sorted) * 0.7)))
        data_ref = Reference(ws2, min_col=3, min_row=1, max_row=1 + len(cs_sorted))
        cat_ref = Reference(ws2, min_col=1, min_row=2, max_row=1 + len(cs_sorted))
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cat_ref)
        ws2.add_chart(chart, "F2")

    ws3 = wb.create_sheet("教师教学质量排名")
    ts_sorted = sorted(stats["teacher_stats"].items(), key=lambda x: x[1]["overall_avg"], reverse=True)
    hdrs3 = ["排名", "教师", "带教班级数", "覆盖学生数", "均分", "及格率"]
    for c, h in enumerate(hdrs3, 1):
        cell = ws3.cell(row=1, column=c, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    for i, (tn, d) in enumerate(ts_sorted, 2):
        row_vals = [i - 1, tn, d["class_count"], d["student_count"],
                    round(d["overall_avg"], 2), f"{d['pass_rate']:.2f}%"]
        for c, v in enumerate(row_vals, 1):
            cell = ws3.cell(row=i, column=c, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
    if ts_sorted:
        chart = BarChart()
        chart.type = "col"
        chart.title = "教师均分排名"
        chart.y_axis.title = "均分"
        chart.style = 10
        chart.width = 18
        chart.height = 12
        data_ref = Reference(ws3, min_col=5, min_row=1, max_row=1 + len(ts_sorted))
        cat_ref = Reference(ws3, min_col=2, min_row=2, max_row=1 + len(ts_sorted))
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cat_ref)
        ws3.add_chart(chart, "H2")

    ws4 = wb.create_sheet("班级汇总")
    hdrs4 = ["班级", "课程", "教师", "学生数", "任务数",
             "均分", "及格率", "提交完成率", "薄弱维度数"]
    for c, h in enumerate(hdrs4, 1):
        cell = ws4.cell(row=1, column=c, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    pc_sorted = sorted(stats["per_class"].items(), key=lambda x: x[1]["overall_avg"], reverse=True)
    for i, (cid, pc) in enumerate(pc_sorted, 2):
        row_vals = [pc["name"], pc["course"], pc["teacher"], pc["student_count"],
                    pc["task_count"], round(pc["overall_avg"], 2),
                    f"{pc['pass_rate']:.2f}%", f"{pc['completion_rate']:.2f}%",
                    len(pc["weak_dims"])]
        for c, v in enumerate(row_vals, 1):
            cell = ws4.cell(row=i, column=c, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')
    if pc_sorted:
        chart = BarChart()
        chart.type = "col"
        chart.title = "各班级均分对比"
        chart.y_axis.title = "均分"
        chart.width = 20
        chart.height = 12
        data_ref = Reference(ws4, min_col=6, min_row=1, max_row=1 + len(pc_sorted))
        cat_ref = Reference(ws4, min_col=1, min_row=2, max_row=1 + len(pc_sorted))
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cat_ref)
        ws4.add_chart(chart, "K2")

    ws.column_dimensions['A'].width = 18
    ws2.column_dimensions['A'].width = 28
    ws3.column_dimensions['B'].width = 20
    ws4.column_dimensions['A'].width = 28
    ws4.column_dimensions['B'].width = 24
    ws4.column_dimensions['C'].width = 18

    filepath = os.path.join(REPORT_DIR, filename)
    wb.save(filepath)
    return filepath


def generate_school_report(filename: str, db, fmt: str = "pdf") -> str:
    fmt = (fmt or "pdf").lower()
    if fmt in ("xlsx", "excel"):
        return generate_school_report_excel(filename, db)
    return generate_school_report_pdf(filename, db)