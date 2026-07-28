import os
from datetime import datetime

try:
    from openpyxl import Workbook  # type: ignore
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side  # type: ignore
    from openpyxl.chart import BarChart, Reference  # type: ignore
    _HAS_OPENPYXL = True
except Exception:  # pragma: no cover
    Workbook = None  # type: ignore
    Font = Alignment = PatternFill = Border = Side = BarChart = Reference = None  # type: ignore
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