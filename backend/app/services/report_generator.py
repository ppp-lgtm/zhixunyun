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

# ============================================================
#  Shared palette (match job_match report palette)
# ============================================================
RGB_SEAL = (255, 90, 31)       # 印章红：主标题、装饰条
RGB_AMBER = (244, 183, 64)     # 琥珀金：副装饰
RGB_JADE = (29, 185, 85)       # 翡翠：亮点/通过
RGB_COBALT = (61, 90, 254)     # 钴蓝：标题 2 级
RGB_INK = (44, 36, 24)         # 正文墨色
RGB_INK_3 = (115, 109, 96)     # 次级文字
RGB_PAPER = (246, 243, 236)    # 纸底
RGB_LINE = (222, 214, 199)     # 分隔线

# Excel-compatible ARGB (no #)
HEX_SEAL = "FF5A1F"
HEX_AMBER = "F4B740"
HEX_JADE = "1DB955"
HEX_COBALT = "3D5AFE"
HEX_INK = "2C2418"
HEX_INK_3 = "736D60"
HEX_PAPER = "F6F3EC"
HEX_ZEBRA = "FAF7F0"
HEX_WHITE = "FFFFFF"


def _rgb_to_hex(rgb: tuple) -> str:
    return "".join(f"{int(v):02X}" for v in rgb)


def _score_level(total: float) -> tuple[str, str, str]:
    """Return (label, PDF color hex tuple, Excel hex) for a score level."""
    if total >= 90:
        return "优秀", RGB_SEAL, HEX_SEAL
    if total >= 80:
        return "良好", RGB_COBALT, HEX_COBALT
    if total >= 70:
        return "中等", RGB_JADE, HEX_JADE
    if total >= 60:
        return "及格", RGB_AMBER, HEX_AMBER
    return "需改进", RGB_INK, HEX_INK_3


def _level_star(total: float) -> str:
    if total >= 95:
        return "★★★★★"
    if total >= 85:
        return "★★★★☆"
    if total >= 75:
        return "★★★☆☆"
    if total >= 65:
        return "★★☆☆☆"
    return "★☆☆☆☆"



def generate_excel(filename, task_requirements, evaluation, student_name="学生"):
    """生成含美化格式 + 双图（柱状 + 雷达）+ 分 Sheet 的 Excel 评价报告。"""
    _ensure_xlsx()
    from openpyxl.utils import get_column_letter
    from openpyxl.chart.series import DataPoint
    from openpyxl.styles.numbers import FORMAT_PERCENTAGE_00

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "评价总览"

    # --- 边框 / 辅助 ---
    thin = Side(style='thin', color='BFB59A')
    medium = Side(style='medium', color='8A7A5B')
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    border_header = Border(left=medium, right=medium, top=medium, bottom=medium)

    header_fill = PatternFill(start_color=HEX_COBALT, end_color=HEX_COBALT, fill_type="solid")
    zebra_fill = PatternFill(start_color=HEX_ZEBRA, end_color=HEX_ZEBRA, fill_type="solid")
    seal_fill = PatternFill(start_color=HEX_SEAL, end_color=HEX_SEAL, fill_type="solid")
    amber_fill = PatternFill(start_color=HEX_AMBER + "33", end_color=HEX_AMBER + "33", fill_type="solid")
    paper_fill = PatternFill(start_color=HEX_PAPER, end_color=HEX_PAPER, fill_type="solid")
    jade_fill = PatternFill(start_color="D6F5E1", end_color="D6F5E1", fill_type="solid")
    cobalt_light = PatternFill(start_color="E6EAFF", end_color="E6EAFF", fill_type="solid")

    total = float(evaluation.get("total") or 0)
    scores = evaluation.get("scores", []) or []
    level, _, _hex_lvl = _score_level(total)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_id = "R" + datetime.now().strftime("%Y%m%d%H%M%S")

    # ---------- Sheet 1: 评价总览 ----------
    # 整页背景
    max_col_total = 6
    for r in range(1, 80):
        for c in range(1, max_col_total + 1):
            ws1.cell(row=r, column=c).fill = paper_fill

    # 顶部装饰条（印章红横条 + 琥珀金横条）
    ws1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col_total)
    c = ws1.cell(row=1, column=1, value="")
    c.fill = seal_fill
    ws1.row_dimensions[1].height = 6
    ws1.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max_col_total)
    c = ws1.cell(row=2, column=1, value="")
    c.fill = PatternFill(start_color=HEX_AMBER, end_color=HEX_AMBER, fill_type="solid")
    ws1.row_dimensions[2].height = 3

    # 标题行（合并）
    ws1.merge_cells(start_row=3, start_column=1, end_row=4, end_column=max_col_total)
    tcell = ws1.cell(row=3, column=1, value="  实 训 评 价 报 告")
    tcell.font = Font(name="微软雅黑", size=22, bold=True, color=HEX_WHITE)
    tcell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    tcell.fill = PatternFill(start_color=HEX_COBALT, end_color=HEX_COBALT, fill_type="solid")
    ws1.row_dimensions[3].height = 22
    ws1.row_dimensions[4].height = 22

    # 基本信息卡（5-8 行，分 1-3 左列 / 4-6 右列）
    # 先按左右列分别合并，避免先合并整行造成内部 cell 变成 MergedCell 只读
    info_rows = [5, 6, 7, 8]
    for r in info_rows:
        # 左列 1-3 合并（统一底色）
        ws1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
        ws1.cell(row=r, column=1).fill = PatternFill(start_color="FFF5E6", end_color="FFF5E6", fill_type="solid")
        # 右列 4-6 合并
        ws1.merge_cells(start_row=r, start_column=4, end_row=r, end_column=max_col_total)
        ws1.cell(row=r, column=4).fill = PatternFill(start_color="FFF5E6", end_color="FFF5E6", fill_type="solid")
        ws1.row_dimensions[r].height = 22

    def _write_merged(ws, row, col, end_col, value, font=None, align=None, fill=None):
        """安全写入：若单元格已在合并区，就写到合并区左上 cell（合并区 top-left 是唯一可写 cell）。"""
        from openpyxl.cell.cell import MergedCell
        target = ws.cell(row=row, column=col)
        if isinstance(target, MergedCell):
            # 在已注册的 merged_cell_ranges 里找到包含该 cell 的合并块，取其左上
            for mcr in ws.merged_cells.ranges:
                if (mcr.min_row <= row <= mcr.max_row and
                        mcr.min_col <= col <= mcr.max_col):
                    target = ws.cell(row=mcr.min_row, column=mcr.min_col)
                    break
        target.value = value
        if font is not None:
            target.font = font
        if align is not None:
            target.alignment = align
        if fill is not None:
            target.fill = fill
        return target

    # 左列（1-3 合并，所以写 col=1 即可）
    lbl_font = Font(name="微软雅黑", size=11, bold=True, color=HEX_INK)
    _write_merged(ws1, 5, 1, 3,
                  f"  学生姓名：{_safe_cn(student_name)}",
                  font=lbl_font,
                  align=Alignment(horizontal='left', vertical='center', indent=1))
    # 学生姓名用钴蓝单独高亮：用同一 cell 替换字体的数字/中文后半段不现实，就直接写成 label+value 一体，末尾值高亮颜色
    # 简化方案：把整句写到 col=1 合并区，另起 col=4 合并区放颜色高亮的姓名（若要严格保持 label/value 分开色可改；现保持一体化更稳）
    # 为让 value 高亮，写为两个相邻文本用富文本：
    from openpyxl.cell.rich_text import TextBlock, CellRichText
    from openpyxl.cell.text import InlineFont
    _write_merged(ws1, 5, 1, 3, "", fill=None)  # 清空
    irl = InlineFont(rFont="微软雅黑", sz=11, b=True, color=HEX_INK)
    irv = InlineFont(rFont="微软雅黑", sz=12, b=True, color=HEX_COBALT)
    ws1.cell(row=5, column=1).value = CellRichText(
        TextBlock(irl, "  学生姓名："),
        TextBlock(irv, _safe_cn(student_name)),
    )
    ws1.cell(row=5, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)

    _write_merged(ws1, 6, 1, 3, "", fill=None)
    ir_lvl = InlineFont(rFont="微软雅黑", sz=12, b=True, color=_hex_lvl)
    ws1.cell(row=6, column=1).value = CellRichText(
        TextBlock(irl, "  评价等级："),
        TextBlock(ir_lvl, level),
    )
    ws1.cell(row=6, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)

    _write_merged(ws1, 7, 1, 3, "", fill=None)
    ir_star = InlineFont(rFont="微软雅黑", sz=12, b=True, color=HEX_AMBER)
    ws1.cell(row=7, column=1).value = CellRichText(
        TextBlock(irl, "  推荐星级："),
        TextBlock(ir_star, _level_star(total)),
    )
    ws1.cell(row=7, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)

    # 右列（4-6 合并）：报告编号 / 生成时间
    sm_font = Font(name="微软雅黑", size=10, color=HEX_INK_3)
    sm_align = Alignment(horizontal='right', vertical='center', indent=1)
    _write_merged(ws1, 5, 4, max_col_total, f"报告编号：{report_id}", font=sm_font, align=sm_align)
    _write_merged(ws1, 6, 4, max_col_total, f"生成时间：{now_str}", font=sm_font, align=sm_align)

    # 综合评分 大字卡（合并行 8，1-3 显示评分 4-6 显示满分/占比）
    ws1.merge_cells(start_row=9, start_column=1, end_row=11, end_column=3)
    sc = ws1.cell(row=9, column=1, value=f"  {total} 分")
    sc.font = Font(name="微软雅黑", size=36, bold=True, color=HEX_SEAL)
    sc.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    sc.fill = PatternFill(start_color="FFF0E6", end_color="FFF0E6", fill_type="solid")
    ws1.row_dimensions[9].height = 28
    ws1.row_dimensions[10].height = 28
    ws1.row_dimensions[11].height = 28
    # 右侧小指标（达标率、最高维度、最低维度）
    right_info = [
        ("达标维度", f"{sum(1 for s in scores if float(s.get('score', 0) or 0) >= 60)} / {len(scores)}", HEX_JADE),
        ("最高分维度", (max(scores, key=lambda s: float(s.get('score', 0) or 0))['name'] if scores else "-"), HEX_COBALT),
        ("最低分维度", (min(scores, key=lambda s: float(s.get('score', 0) or 0))['name'] if scores else "-"), HEX_AMBER),
    ]
    for i, (lbl, val, hx) in enumerate(right_info):
        rr = 9 + i
        ws1.merge_cells(start_row=rr, start_column=4, end_row=rr, end_column=max_col_total)
        c = ws1.cell(row=rr, column=4, value=f"  {lbl}：  {_safe_cn(val)}")
        c.font = Font(name="微软雅黑", size=11, bold=True, color=hx)
        c.alignment = Alignment(horizontal='left', vertical='center', indent=1)
        c.fill = PatternFill(start_color="FFFDF6", end_color="FFFDF6", fill_type="solid")

    # 空白
    ws1.cell(row=12, column=1, value="")
    ws1.row_dimensions[12].height = 8

    # 维度评分表表头（行 13 合并大标题）
    header_big_row = 13
    ws1.merge_cells(start_row=header_big_row, start_column=1, end_row=header_big_row, end_column=6)
    hc = ws1.cell(row=header_big_row, column=1, value="  各维度详细评分")
    hc.font = Font(name="微软雅黑", size=13, bold=True, color=HEX_WHITE)
    hc.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    hc.fill = PatternFill(start_color=HEX_COBALT, end_color=HEX_COBALT, fill_type="solid")
    ws1.row_dimensions[header_big_row].height = 22

    # 列名（行 14）：序号 / 评价维度 / 得分 / 满分 / 得分率 / 评分理由
    table_start = 14
    headers = ["序号", "评价维度", "得分", "满分", "得分率", "评分理由"]
    widths = [6, 22, 10, 10, 12, 55]
    for i, h in enumerate(headers, 1):
        cc = ws1.cell(row=table_start, column=i, value=h)
        cc.font = Font(name="微软雅黑", size=11, bold=True, color=HEX_WHITE)
        cc.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cc.fill = header_fill
        cc.border = border_header
    ws1.row_dimensions[table_start].height = 24
    for i, w in enumerate(widths, 1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # 数据行
    for i, s in enumerate(scores, 1):
        r = table_start + i
        sc_val = float(s.get("score", 0) or 0)
        pct = min(1.0, sc_val / 100.0) if sc_val else 0
        ws1.cell(row=r, column=1, value=i).alignment = Alignment(horizontal='center', vertical='center')
        ws1.cell(row=r, column=1).font = Font(name="微软雅黑", size=10, color=HEX_INK_3, bold=True)
        ws1.cell(row=r, column=2, value=_safe_cn(s.get("name", ""))).font = Font(name="微软雅黑", size=11, bold=True, color=HEX_INK)
        ws1.cell(row=r, column=2).alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws1.cell(row=r, column=3, value=sc_val).font = Font(name="微软雅黑", size=12, bold=True, color=(
            HEX_SEAL if sc_val >= 90 else HEX_COBALT if sc_val >= 80 else HEX_JADE if sc_val >= 70 else HEX_AMBER if sc_val >= 60 else "C62828"
        ))
        ws1.cell(row=r, column=3).alignment = Alignment(horizontal='center', vertical='center')
        ws1.cell(row=r, column=4, value=100).font = Font(name="微软雅黑", size=10, color=HEX_INK_3)
        ws1.cell(row=r, column=4).alignment = Alignment(horizontal='center', vertical='center')
        ws1.cell(row=r, column=5, value=pct).number_format = FORMAT_PERCENTAGE_00
        ws1.cell(row=r, column=5).alignment = Alignment(horizontal='center', vertical='center')
        ws1.cell(row=r, column=5).font = Font(name="微软雅黑", size=10, bold=True, color=(
            HEX_JADE if pct >= 0.8 else HEX_AMBER if pct >= 0.6 else "C62828"
        ))
        ws1.cell(row=r, column=6, value=_safe_cn(s.get("reason", ""))).font = Font(name="微软雅黑", size=10, color=HEX_INK)
        ws1.cell(row=r, column=6).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True, indent=1)

        # 边框 + 斑马纹
        for col in range(1, max_col_total + 1):
            cell = ws1.cell(row=r, column=col)
            cell.border = border_all
            if i % 2 == 0:
                cell.fill = zebra_fill

        # 条件底色：<60 琥珀底，≥90 翡翠浅底
        if sc_val < 60:
            for col in range(1, max_col_total + 1):
                ws1.cell(row=r, column=col).fill = amber_fill
        elif sc_val >= 90:
            for col in range(1, max_col_total + 1):
                ws1.cell(row=r, column=col).fill = jade_fill

        # 行高自适应（理由字数粗略估算）
        reason_len = len(s.get("reason", ""))
        h = max(24, 18 + (reason_len // 30) * 16)
        ws1.row_dimensions[r].height = h

    last_data_row = table_start + max(len(scores), 1)

    # 合计行（行 last_data_row + 1）
    sum_row = last_data_row + 1
    ws1.merge_cells(start_row=sum_row, start_column=1, end_row=sum_row, end_column=2)
    cc = ws1.cell(row=sum_row, column=1, value="  合计 / 平均")
    cc.font = Font(name="微软雅黑", size=11, bold=True, color=HEX_WHITE)
    cc.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    cc.fill = PatternFill(start_color=HEX_COBALT, end_color=HEX_COBALT, fill_type="solid")
    avg_sc = round(sum(float(s.get('score', 0) or 0) for s in scores) / len(scores), 1) if scores else 0
    avg_pct = min(1.0, avg_sc / 100.0) if avg_sc else 0
    ws1.cell(row=sum_row, column=3, value=avg_sc).font = Font(name="微软雅黑", size=12, bold=True, color=HEX_COBALT)
    ws1.cell(row=sum_row, column=3).alignment = Alignment(horizontal='center', vertical='center')
    ws1.cell(row=sum_row, column=4, value=100).font = Font(name="微软雅黑", size=10, color=HEX_INK_3)
    ws1.cell(row=sum_row, column=4).alignment = Alignment(horizontal='center', vertical='center')
    ws1.cell(row=sum_row, column=5, value=avg_pct).number_format = FORMAT_PERCENTAGE_00
    ws1.cell(row=sum_row, column=5).alignment = Alignment(horizontal='center', vertical='center')
    ws1.cell(row=sum_row, column=5).font = Font(name="微软雅黑", size=10, bold=True, color=HEX_COBALT)
    ws1.cell(row=sum_row, column=6, value=f"评价等级：{level}").font = Font(name="微软雅黑", size=10, bold=True, color=_hex_lvl)
    ws1.cell(row=sum_row, column=6).alignment = Alignment(horizontal='left', vertical='center', indent=1)
    for col in range(1, max_col_total + 1):
        ws1.cell(row=sum_row, column=col).border = border_header
    ws1.row_dimensions[sum_row].height = 26

    # 冻结窗格（冻结到表头下方）
    ws1.freeze_panes = f"A{table_start + 1}"

    # 柱状图（得分）
    try:
        chart = BarChart()
        chart.type = "col"
        chart.style = 11
        chart.title = "各维度得分对比"
        chart.y_axis.title = "分数"
        chart.y_axis.scaling.min = 0
        chart.y_axis.scaling.max = 100
        chart.x_axis.title = "维度"
        chart.width = 22
        chart.height = 12
        data = Reference(ws1, min_col=3, min_row=table_start, max_row=last_data_row, max_col=3)
        cats = Reference(ws1, min_col=2, min_row=table_start + 1, max_row=last_data_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        # 颜色：印章红柱子，数据标签
        try:
            s0 = chart.series[0]
            s0.graphicalProperties.solidFill = HEX_SEAL
            s0.graphicalProperties.line.solidFill = HEX_SEAL
            s0.dataLabels = DataLabelList()
            s0.dataLabels.showVal = True
            s0.dataLabels.showCatName = False
        except Exception:
            pass
        chart_anchor_row = sum_row + 3
        ws1.add_chart(chart, f"A{chart_anchor_row}")
    except Exception:
        chart_anchor_row = sum_row + 3
        pass

    # 雷达图（右侧）
    try:
        rc = RadarChart()
        rc.title = "维度掌握率雷达图"
        rc.style = 26
        rc.width = 16
        rc.height = 13
        rc.y_axis.scaling.min = 0
        rc.y_axis.scaling.max = 100
        rc_data = Reference(ws1, min_col=3, min_row=table_start, max_row=last_data_row, max_col=3)
        rc_cats = Reference(ws1, min_col=2, min_row=table_start + 1, max_row=last_data_row)
        rc.add_data(rc_data, titles_from_data=True)
        rc.set_categories(rc_cats)
        try:
            rs = rc.series[0]
            rs.graphicalProperties.solidFill = HEX_AMBER
            rs.graphicalProperties.line.solidFill = HEX_COBALT
        except Exception:
            pass
        ws1.add_chart(rc, f"D{chart_anchor_row}")
    except Exception:
        pass

    # AI 总评 大卡片
    comment_anchor = chart_anchor_row + 24
    ws1.merge_cells(start_row=comment_anchor, start_column=1, end_row=comment_anchor, end_column=max_col_total)
    cc = ws1.cell(row=comment_anchor, column=1, value="  AI 综合评价")
    cc.font = Font(name="微软雅黑", size=13, bold=True, color=HEX_WHITE)
    cc.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    cc.fill = PatternFill(start_color=HEX_JADE, end_color=HEX_JADE, fill_type="solid")
    ws1.row_dimensions[comment_anchor].height = 24
    ws1.merge_cells(start_row=comment_anchor + 1, start_column=1, end_row=comment_anchor + 5, end_column=max_col_total)
    cmt_cell = ws1.cell(row=comment_anchor + 1, column=1, value=_safe_cn(evaluation.get("comment", "")))
    cmt_cell.font = Font(name="微软雅黑", size=11, color=HEX_INK)
    cmt_cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True, indent=2)
    cmt_cell.fill = PatternFill(start_color="EAFBF1", end_color="EAFBF1", fill_type="solid")
    cmt_cell.border = border_all
    for rr in range(comment_anchor + 1, comment_anchor + 6):
        ws1.row_dimensions[rr].height = 22

    # 实训要求 卡片
    req_anchor = comment_anchor + 7
    ws1.merge_cells(start_row=req_anchor, start_column=1, end_row=req_anchor, end_column=max_col_total)
    cc = ws1.cell(row=req_anchor, column=1, value="  实训任务要求")
    cc.font = Font(name="微软雅黑", size=13, bold=True, color=HEX_WHITE)
    cc.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    cc.fill = PatternFill(start_color=HEX_AMBER, end_color=HEX_AMBER, fill_type="solid")
    ws1.row_dimensions[req_anchor].height = 24
    ws1.merge_cells(start_row=req_anchor + 1, start_column=1, end_row=req_anchor + 5, end_column=max_col_total)
    req_cell = ws1.cell(row=req_anchor + 1, column=1, value=_safe_cn(task_requirements))
    req_cell.font = Font(name="微软雅黑", size=11, color=HEX_INK)
    req_cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True, indent=2)
    req_cell.fill = PatternFill(start_color="FFF9EC", end_color="FFF9EC", fill_type="solid")
    req_cell.border = border_all
    for rr in range(req_anchor + 1, req_anchor + 6):
        ws1.row_dimensions[rr].height = 22

    # ---------- Sheet 2: 维度明细（长文） ----------
    ws2 = wb.create_sheet("维度明细")
    for r in range(1, 500):
        for c in range(1, 4):
            ws2.cell(row=r, column=c).fill = paper_fill
    ws2.column_dimensions['A'].width = 24
    ws2.column_dimensions['B'].width = 12
    ws2.column_dimensions['C'].width = 100

    # 顶部装饰
    ws2.merge_cells('A1:C1')
    ws2['A1'].fill = seal_fill
    ws2.row_dimensions[1].height = 6
    ws2.merge_cells('A2:C2')
    ws2['A2'].fill = PatternFill(start_color=HEX_COBALT, end_color=HEX_COBALT, fill_type="solid")
    ws2['A2'].value = "  各维度评分理由（详细版）"
    ws2['A2'].font = Font(name="微软雅黑", size=14, bold=True, color=HEX_WHITE)
    ws2.row_dimensions[2].height = 28

    # 表头
    h2 = ["评价维度", "得分", "评分理由（详细）"]
    for i, h in enumerate(h2, 1):
        cc = ws2.cell(row=3, column=i, value=h)
        cc.font = Font(name="微软雅黑", size=12, bold=True, color=HEX_WHITE)
        cc.fill = header_fill
        cc.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cc.border = border_header
    ws2.row_dimensions[3].height = 24
    ws2.freeze_panes = "A4"

    for i, s in enumerate(scores, 1):
        r = 3 + i
        sc_val = float(s.get('score', 0) or 0)
        ws2.cell(row=r, column=1, value=_safe_cn(s.get("name", ""))).font = Font(name="微软雅黑", size=11, bold=True, color=HEX_INK)
        ws2.cell(row=r, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws2.cell(row=r, column=2, value=sc_val).font = Font(name="微软雅黑", size=12, bold=True, color=(
            HEX_SEAL if sc_val >= 90 else HEX_COBALT if sc_val >= 80 else HEX_JADE if sc_val >= 70 else HEX_AMBER if sc_val >= 60 else "C62828"
        ))
        ws2.cell(row=r, column=2).alignment = Alignment(horizontal='center', vertical='center')
        ws2.cell(row=r, column=3, value=_safe_cn(s.get("reason", ""))).font = Font(name="微软雅黑", size=10.5, color=HEX_INK)
        ws2.cell(row=r, column=3).alignment = Alignment(horizontal='left', vertical='top', wrap_text=True, indent=1)
        for col in range(1, 4):
            ws2.cell(row=r, column=col).border = border_all
            if i % 2 == 0:
                ws2.cell(row=r, column=col).fill = zebra_fill
        # 行高估算
        lines = max(4, (len(s.get("reason", "")) // 55) + 2)
        ws2.row_dimensions[r].height = 16 * lines

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
    """生成排版精美的 PDF 实训评价报告：封面 + KPI 卡 + 图表 + 表格 + 总评。"""
    _ensure_fpdf()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    fn, fnb = _register_cn_fonts(pdf)
    tmp_files: list[str] = []
    pdf.add_page()
    filepath = os.path.join(REPORT_DIR, filename)

    total = float(evaluation.get("total") or 0)
    scores = evaluation.get("scores", []) or []
    level, lvl_rgb, _ = _score_level(total)
    star = _level_star(total)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_id = "R" + datetime.now().strftime("%Y%m%d%H%M%S")
    n_pass = sum(1 for s in scores if float(s.get("score", 0) or 0) >= 60)
    n_total = len(scores) or 1
    best = max(scores, key=lambda s: float(s.get("score", 0) or 0)) if scores else None
    worst = min(scores, key=lambda s: float(s.get("score", 0) or 0)) if scores else None

    # ---- 顶部装饰条：印章红 + 琥珀金 ----
    pdf.set_fill_color(*RGB_SEAL)
    pdf.rect(pdf.l_margin, 10, pdf.epw, 4, "F")
    pdf.set_fill_color(*RGB_AMBER)
    pdf.rect(pdf.l_margin, 14, pdf.epw, 2, "F")
    # 左竖装饰
    pdf.set_fill_color(*RGB_COBALT)
    pdf.rect(pdf.l_margin + 2, 22, 3, 40, "F")

    # 副标题
    pdf.set_xy(pdf.l_margin + 10, 24)
    pdf.set_font(fn, "B", 11)
    pdf.set_text_color(*RGB_COBALT)
    pdf.cell(0, 7, "ZHI XUN YUN  ·  知 训 云  ·  实 训 评 价 体 系",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 大标题
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font(fn, "B", 30)
    pdf.set_text_color(*RGB_INK)
    pdf.cell(0, 18, "实 训 评 价 报 告", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # 基本信息表（双列）
    info_rows = [
        ("学生姓名", _safe_cn(student_name, 20), "报告编号", report_id),
        ("评价等级", f"{level}  {star}", "生成时间", now_str),
    ]
    col1x = pdf.l_margin + 10
    col2x = pdf.l_margin + pdf.epw / 2 + 10
    lbl_w = 26
    val_w = pdf.epw / 2 - lbl_w - 12
    for r, (l1, v1, l2, v2) in enumerate(info_rows):
        y = pdf.get_y()
        # 左列
        pdf.set_xy(col1x, y)
        pdf.set_font(fn, "", 10)
        pdf.set_text_color(*RGB_INK_3)
        pdf.cell(lbl_w, 8, f"{l1}：", new_x="RIGHT", new_y="TOP")
        pdf.set_font(fnb, "", 12)
        pdf.set_text_color(*RGB_INK)
        if l1 == "评价等级":
            pdf.set_text_color(*lvl_rgb)
        pdf.cell(val_w, 8, _safe_cn(str(v1), 34), new_x="RIGHT", new_y="TOP")
        # 右列
        pdf.set_xy(col2x, y)
        pdf.set_font(fn, "", 10)
        pdf.set_text_color(*RGB_INK_3)
        pdf.cell(lbl_w, 8, f"{l2}：", new_x="RIGHT", new_y="TOP")
        pdf.set_font(fn, "", 10.5)
        pdf.set_text_color(*RGB_INK_3 if l2 != "评价等级" else RGB_INK)
        pdf.cell(val_w, 8, _safe_cn(str(v2), 34), new_x="RIGHT", new_y="TOP")
        pdf.set_y(y + 9)
    pdf.ln(4)

    # ---- 综合评分 大字卡 ----
    score_x1 = pdf.l_margin + 4
    score_y = pdf.get_y()
    # 底框（印章红渐变模拟：印章红大框 + 琥珀金竖条）
    pdf.set_fill_color(255, 244, 236)
    pdf.rect(score_x1, score_y, pdf.epw - 8, 38, "F")
    pdf.set_fill_color(*RGB_SEAL)
    pdf.rect(score_x1, score_y, 5, 38, "F")
    pdf.set_fill_color(*RGB_AMBER)
    pdf.rect(score_x1, score_y + 32, pdf.epw - 8, 6, "F")

    # 分数大字
    pdf.set_xy(score_x1 + 14, score_y + 3)
    pdf.set_font(fnb, "", 40)
    pdf.set_text_color(*RGB_SEAL)
    pdf.cell(60, 20, f"{total}", new_x="RIGHT", new_y="TOP")
    pdf.set_font(fn, "", 14)
    pdf.set_text_color(*RGB_SEAL)
    pdf.cell(14, 20, "分", new_x="RIGHT", new_y="TOP")
    # 等级 + 星级
    pdf.set_xy(score_x1 + 14, score_y + 24)
    pdf.set_font(fnb, "", 12)
    pdf.set_text_color(*lvl_rgb)
    pdf.cell(60, 10, f"等级：{level}    {star}", new_x="RIGHT", new_y="TOP")

    # 右侧 3 个小 KPI 条（达标维度 / 最高分维度 / 最低分维度）
    right_kpis = [
        ("达标维度", f"{n_pass} / {n_total}", RGB_JADE),
        ("最高维度", _safe_cn(best["name"], 10) if best else "-",
         RGB_COBALT),
        ("最低维度", _safe_cn(worst["name"], 10) if worst else "-",
         RGB_AMBER),
    ]
    right_x = pdf.l_margin + pdf.epw / 2 + 14
    right_w = pdf.epw / 2 - 24
    for i, (k, v, col) in enumerate(right_kpis):
        ky = score_y + 4 + i * 11
        # 左侧色标
        pdf.set_fill_color(*col)
        pdf.rect(right_x, ky, 3.5, 9, "F")
        pdf.set_xy(right_x + 6, ky)
        pdf.set_font(fn, "", 9.5)
        pdf.set_text_color(*RGB_INK_3)
        pdf.cell(20, 9, f"{k}：", new_x="RIGHT", new_y="TOP")
        pdf.set_font(fnb, "", 10.5)
        pdf.set_text_color(*col)
        pdf.cell(right_w - 26, 9, _safe_cn(str(v), 26), new_x="RIGHT", new_y="TOP")
    pdf.set_y(score_y + 46)

    # ---- 章节一：核心指标概览（4 KPI 卡 绝对 X） ----
    pdf.set_font(fnb, "", 14)
    pdf.set_text_color(*RGB_INK)
    pdf.cell(0, 10, "一 、 核 心 指 标 概 览", new_x="LMARGIN", new_y="NEXT")
    # 章节分割线
    y = pdf.get_y()
    pdf.set_draw_color(*RGB_COBALT)
    pdf.set_line_width(0.6)
    pdf.line(pdf.l_margin, y + 2, pdf.l_margin + pdf.epw, y + 2)
    pdf.ln(8)

    lm = pdf.l_margin
    epw = pdf.epw
    col_w = epw / 4
    card_top = pdf.get_y()
    kpi_cards = [
        ("综 合 评 分", f"{total}", "分", RGB_SEAL),
        ("达 标 维 度", f"{n_pass}", f"/{n_total}", RGB_COBALT),
        ("维 度 均 分", f"{round(sum(float(s.get('score',0) or 0) for s in scores)/n_total, 1)}", "分", RGB_JADE),
        ("评 价 等 级", level, "", lvl_rgb),
    ]
    for i, (k, v, u, col) in enumerate(kpi_cards):
        cx = lm + i * col_w
        # 背景
        pdf.set_fill_color(*col)
        pdf.set_xy(cx, card_top)
        pdf.cell(col_w, 40, "", border=0, fill=True, new_x="RIGHT", new_y="TOP")
        # 数字
        pdf.set_xy(cx, card_top + 7)
        pdf.set_font(fnb, "", 20)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col_w, 14, f"{v}{u}", align="C", new_x="RIGHT", new_y="TOP")
        # 标签
        pdf.set_xy(cx, card_top + 25)
        pdf.set_font(fn, "", 10)
        pdf.set_text_color(255, 245, 238)
        pdf.cell(col_w, 9, _safe_cn(k), align="C", new_x="RIGHT", new_y="TOP")
    pdf.set_y(card_top + 50)

    # ---- 图表：维度得分双图 ----
    # 横向柱状 + 雷达（雷达放右侧）
    bar_png = None
    radar_png = None
    if scores:
        dims = {_safe_cn(s["name"], 12): float(s.get("score", 0) or 0) for s in scores}
        bar_png = _mpl_bar(
            dims, title="各维度得分对比（横向）", xlabel="分数",
            horizontal=True, color="#FF5A1F")
        radar_png = _mpl_radar(dims, title="维度掌握雷达图")

    left_w = 100
    right_w = 80
    gy = pdf.get_y()
    need_page = False
    if bar_png and pdf.get_y() + 70 > pdf.h - pdf.b_margin:
        pdf.add_page()
        need_page = True
    if not need_page:
        pdf.set_font(fnb, "", 13)
        pdf.set_text_color(*RGB_INK)
        pdf.cell(0, 10, "二 、 维 度 得 分 图 表", new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        pdf.set_draw_color(*RGB_COBALT)
        pdf.line(pdf.l_margin, y + 2, pdf.l_margin + pdf.epw, y + 2)
        pdf.ln(6)

    gx = pdf.l_margin
    gy = pdf.get_y()
    # 左：柱状
    if bar_png:
        _pdf_add_image_if(pdf, bar_png, w=left_w, h=60, cleanup_paths=tmp_files)
    # 右：雷达
    if radar_png:
        pdf.set_xy(gx + left_w + 5, gy)
        _pdf_add_image_if(pdf, radar_png, w=right_w, h=60, cleanup_paths=tmp_files)
    pdf.set_y(gy + 68)

    # ---- 章节三：维度详细评分表格（支持跨页） ----
    def _section_header(title: str):
        pdf.ln(4)
        if pdf.get_y() + 18 > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.set_font(fnb, "", 13)
        pdf.set_text_color(*RGB_INK)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        pdf.set_draw_color(*RGB_COBALT)
        pdf.set_line_width(0.6)
        pdf.line(pdf.l_margin, y + 2, pdf.l_margin + pdf.epw, y + 2)
        pdf.ln(6)

    _section_header("三 、 各 维 度 详 细 评 分 表")

    # 表头
    col_widths = [12, 42, 18, 18, 24, epw - 12 - 42 - 18 - 18 - 24]  # 114 total by epw
    # 重新按比例计算 epw
    cw = [10, 38, 16, 14, 20, epw - 10 - 38 - 16 - 14 - 20]
    headers = ["#", "评价维度", "得分", "满分", "得分率", "评分理由"]
    # 表头行
    y0 = pdf.get_y()
    # 如果表头放不下开新页
    if y0 + 10 > pdf.h - pdf.b_margin:
        pdf.add_page()
        y0 = pdf.get_y()
    # 表头填充
    pdf.set_fill_color(*RGB_COBALT)
    x0 = pdf.l_margin
    pdf.set_xy(x0, y0)
    for i, h in enumerate(headers):
        pdf.cell(cw[i], 10, _safe_cn(h), border=0, fill=True,
                 align="C", new_x="RIGHT", new_y="TOP")
    pdf.set_font(fnb, "", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(x0, y0)
    for i, h in enumerate(headers):
        pdf.cell(cw[i], 10, _safe_cn(h), border=0, fill=False,
                 align="C", new_x="RIGHT", new_y="TOP")
    pdf.set_y(y0 + 10)

    # 数据行
    for i, s in enumerate(scores, 1):
        sc_val = float(s.get("score", 0) or 0)
        pct = f"{int(min(100, sc_val))}%"
        reason = _safe_cn(s.get("reason", ""), 200)
        # 按理由字数估算高度
        n_lines_reason = max(2, len(reason) // 42 + 1)
        row_h = max(14, n_lines_reason * 6 + 4)
        # 跨页判断
        if pdf.get_y() + row_h + 4 > pdf.h - pdf.b_margin:
            # 重复表头
            pdf.add_page()
            y0 = pdf.get_y()
            pdf.set_fill_color(*RGB_COBALT)
            pdf.set_xy(x0, y0)
            for j, h in enumerate(headers):
                pdf.cell(cw[j], 10, _safe_cn(h), border=0, fill=True,
                         align="C", new_x="RIGHT", new_y="TOP")
            pdf.set_font(fnb, "", 10)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(x0, y0)
            for j, h in enumerate(headers):
                pdf.cell(cw[j], 10, _safe_cn(h), border=0, fill=False,
                         align="C", new_x="RIGHT", new_y="TOP")
            pdf.set_y(y0 + 10)

        ry = pdf.get_y()
        # 斑马 / 条件底色
        is_zebra = i % 2 == 0
        cond = "none"
        if sc_val < 60:
            cond = "amber"
        elif sc_val >= 90:
            cond = "jade"
        # 绘制空背景行
        if cond == "amber":
            pdf.set_fill_color(255, 243, 220)
        elif cond == "jade":
            pdf.set_fill_color(220, 248, 232)
        elif is_zebra:
            pdf.set_fill_color(250, 247, 240)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_xy(x0, ry)
        pdf.cell(epw, row_h, "", border=0, fill=True, new_x="RIGHT", new_y="TOP")

        # 边框线（上下横线）
        pdf.set_draw_color(*RGB_LINE)
        pdf.set_line_width(0.2)
        pdf.line(x0, ry, x0 + epw, ry)
        pdf.line(x0, ry + row_h, x0 + epw, ry + row_h)

        # 序号
        pdf.set_xy(x0, ry)
        pdf.set_font(fn, "", 9.5)
        pdf.set_text_color(*RGB_INK_3)
        pdf.cell(cw[0], row_h, f"  {i}", align="L", new_x="RIGHT", new_y="TOP")
        # 维度名
        pdf.set_xy(x0 + cw[0], ry)
        pdf.set_font(fnb, "", 10.5)
        pdf.set_text_color(*RGB_INK)
        pdf.cell(cw[1], row_h, "  " + _safe_cn(s.get("name", ""), 16), align="L", new_x="RIGHT", new_y="TOP")
        # 得分（分级着色）
        sc_color = (
            RGB_SEAL if sc_val >= 90 else RGB_COBALT if sc_val >= 80
            else RGB_JADE if sc_val >= 70 else RGB_AMBER if sc_val >= 60 else (198, 40, 40)
        )
        pdf.set_xy(x0 + cw[0] + cw[1], ry)
        pdf.set_font(fnb, "", 12)
        pdf.set_text_color(*sc_color)
        pdf.cell(cw[2], row_h, f"{sc_val}", align="C", new_x="RIGHT", new_y="TOP")
        # 满分
        pdf.set_xy(x0 + cw[0] + cw[1] + cw[2], ry)
        pdf.set_font(fn, "", 10)
        pdf.set_text_color(*RGB_INK_3)
        pdf.cell(cw[3], row_h, "100", align="C", new_x="RIGHT", new_y="TOP")
        # 得分率
        pct_col = (
            RGB_JADE if sc_val >= 80 else RGB_AMBER if sc_val >= 60 else (198, 40, 40)
        )
        pdf.set_xy(x0 + cw[0] + cw[1] + cw[2] + cw[3], ry)
        pdf.set_font(fnb, "", 10)
        pdf.set_text_color(*pct_col)
        pdf.cell(cw[4], row_h, pct, align="C", new_x="RIGHT", new_y="TOP")
        # 评分理由（multi_cell 行内绘制，先移到该格位置）
        rx = x0 + cw[0] + cw[1] + cw[2] + cw[3] + cw[4]
        rw = cw[5]
        pdf.set_xy(rx, ry + 2)
        pdf.set_font(fn, "", 9.5)
        pdf.set_text_color(*RGB_INK)
        pdf.multi_cell(rw, 5.5, reason, border=0, align="L", new_x="RIGHT", new_y="NEXT")

        pdf.set_y(ry + row_h)

    pdf.ln(4)

    # ---- 章节四：AI 综合评价 ----
    _section_header("四 、 AI 综 合 评 价")
    y = pdf.get_y()
    # 翡翠底卡片
    pdf.set_fill_color(234, 251, 241)
    pdf.rect(pdf.l_margin, y, epw, 6, "F")
    pdf.set_fill_color(*RGB_JADE)
    pdf.rect(pdf.l_margin, y, 4, 6, "F")
    pdf.ln(2)
    # 卡片正文
    y = pdf.get_y()
    pdf.set_fill_color(246, 253, 248)
    # 预估需要高度
    comment = _safe_cn(evaluation.get("comment", ""), 2000)
    est_h = max(36, (len(comment) // 66 + 2) * 7 + 10)
    if y + est_h + 10 > pdf.h - pdf.b_margin:
        pdf.add_page()
        y = pdf.get_y()
    pdf.set_fill_color(246, 253, 248)
    pdf.rect(pdf.l_margin, y, epw, est_h, "F")
    pdf.set_draw_color(*RGB_JADE)
    pdf.set_line_width(0.5)
    pdf.rect(pdf.l_margin, y, epw, est_h, "D")
    pdf.set_xy(pdf.l_margin + 8, y + 6)
    pdf.set_font(fnb, "", 11.5)
    pdf.set_text_color(*RGB_JADE)
    pdf.cell(0, 7, "▎ 综合评语", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font(fn, "", 11)
    pdf.set_text_color(*RGB_INK)
    pdf.multi_cell(epw - 20, 6.5, comment, align="L")
    pdf.set_y(y + est_h + 2)

    # ---- 章节五：实训要求 ----
    _section_header("五 、 实 训 任 务 要 求")
    y = pdf.get_y()
    pdf.set_fill_color(255, 249, 236)
    pdf.rect(pdf.l_margin, y, epw, 6, "F")
    pdf.set_fill_color(*RGB_AMBER)
    pdf.rect(pdf.l_margin, y, 4, 6, "F")
    pdf.ln(2)
    y = pdf.get_y()
    req = _safe_cn(task_requirements, 5000)
    est_h = max(40, (len(req) // 66 + 2) * 6.5 + 10)
    if y + est_h + 10 > pdf.h - pdf.b_margin:
        pdf.add_page()
        y = pdf.get_y()
    pdf.set_fill_color(255, 251, 242)
    pdf.rect(pdf.l_margin, y, epw, est_h, "F")
    pdf.set_draw_color(*RGB_AMBER)
    pdf.set_line_width(0.5)
    pdf.rect(pdf.l_margin, y, epw, est_h, "D")
    pdf.set_xy(pdf.l_margin + 8, y + 6)
    pdf.set_font(fnb, "", 11.5)
    pdf.set_text_color(*RGB_AMBER)
    pdf.cell(0, 7, "▎ 任务说明", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font(fn, "", 10.5)
    pdf.set_text_color(*RGB_INK)
    pdf.multi_cell(epw - 20, 6, req, align="L")
    pdf.set_y(y + est_h + 4)

    # ---- 章末：导师签字 + 时间页脚 ----
    pdf.ln(6)
    if pdf.get_y() + 50 > pdf.h - pdf.b_margin:
        pdf.add_page()
    sign_y = pdf.get_y()
    pdf.set_draw_color(*RGB_LINE)
    pdf.set_line_width(0.3)
    # 左：导师签字
    pdf.set_font(fn, "", 10.5)
    pdf.set_text_color(*RGB_INK_3)
    pdf.set_xy(pdf.l_margin, sign_y + 24)
    pdf.line(pdf.l_margin + 20, sign_y + 22, pdf.l_margin + 70, sign_y + 22)
    pdf.cell(0, 8, "导 师 签 字 / Teacher：                  日 期 / Date：            ",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + epw, pdf.get_y())
    pdf.ln(3)
    pdf.set_font(fn, "", 9)
    pdf.set_text_color(*RGB_INK_3)
    pdf.cell(0, 5,
             f"  ZHI XUN YUN · 知训云智能实训评价平台     报告编号：{report_id}     生成时间：{now_str}     本报告由系统自动生成 · 未经授权不得外传",
             align="C", new_x="LMARGIN", new_y="NEXT")

    # 清理临时图
    for p in tmp_files:
        try:
            os.unlink(p)
        except Exception:
            pass
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