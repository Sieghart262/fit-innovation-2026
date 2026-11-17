"""Phần giao diện dùng chung của dashboard: màu, kiểu chữ, thẻ số liệu, huy hiệu, kiểu biểu đồ.

Tách riêng khỏi app.py để phần "trông thế nào" nằm một chỗ, phần "hiện cái gì" nằm một chỗ.
Không tải phông chữ hay tài nguyên từ Internet: dashboard chạy được trên máy không có mạng.
"""

from __future__ import annotations

import html

import altair as alt
import pandas as pd
import streamlit as st

from gp1 import cau_hinh as ch1
from gp3 import cau_hinh as ch3

# --- Màu (bảng màu đã kiểm tra an toàn cho người mù màu) ---
MAU_TRUOC, MAU_SAU = "#2a78d6", "#eb6834"     # trước hiệu chỉnh (xanh) / sau hiệu chỉnh (cam)
MAU_CHINH = "#1c5cab"
MUC_CHU, MUC_PHU, MUC_MO, VIEN = "#1b1b1a", "#52514e", "#898781", "#e1e0d9"

# --- Tên tiếng Việt của nhãn Giải pháp 1 (mã gốc của đề vẫn hiện kèm ở nơi cần) ---
NHAN_VIET = {
    ch1.HIGH: "Lạm phát điểm",
    ch1.STEEP: "Điểm bị ép thấp",
    ch1.DIST: "Phân phối điểm bất thường",
    ch1.REVIEW: "Cần xem xét thêm",
    ch1.NORMAL: "Bình thường",
    ch1.IT_DU_LIEU: "Ít dữ liệu",
    ch1.CHUA_DU: "Dữ liệu chưa đầy đủ",
    ch1.KHONG_MOC: "Không đủ lớp để so sánh",
}
GIAI_THICH_NHAN = {
    ch1.HIGH: "Điểm lớp cao hơn hẳn các lớp tương đương, và có bằng chứng do cách chấm.",
    ch1.STEEP: "Điểm lớp thấp hơn hẳn các lớp tương đương, và có bằng chứng do cách chấm.",
    ch1.DIST: "Điểm trong lớp gần như giống nhau, hoặc điểm quá trình trùng điểm thi.",
    ch1.REVIEW: "Điểm lớp lệch nhưng chưa có bằng chứng do cách chấm. Không sửa điểm.",
    ch1.NORMAL: "Không thấy dấu hiệu bất thường.",
    ch1.IT_DU_LIEU: "Lớp có từ 5 điểm hợp lệ trở xuống. Không đánh giá, giữ nguyên điểm.",
    ch1.CHUA_DU: "Lớp chưa nhập đủ điểm (ví dụ chưa có điểm quá trình). Không đánh giá.",
    ch1.KHONG_MOC: "Không có đủ lớp cùng môn hoặc cùng nhóm môn để so sánh.",
}

# --- Mức năng lực: tên của đề + diễn giải tiếng Việt + màu huy hiệu (nền, chữ) ---
MUC_VIET = {
    "Advanced": ("Xuất sắc", "TCI từ 3,60", "#e3f2e3", "#0b5c0b"),
    "Proficient": ("Khá, giỏi", "TCI từ 3,20 đến dưới 3,60", "#e2edfb", "#184f95"),
    "Intermediate": ("Trung bình", "TCI từ 2,50 đến dưới 3,20", "#fdf0d2", "#7a5200"),
    "At-Risk": ("Cần hỗ trợ", "TCI dưới 2,50", "#fbe3e3", "#9c2323"),
    ch3.CHUA_DU_DU_LIEU: ("Chưa đủ dữ liệu", "Không có môn nào có điểm hợp lệ", "#ecebe6", "#52514e"),
}

CSS = f"""
<style>
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1240px; }}
h1 {{ font-size: 1.75rem !important; font-weight: 700 !important; letter-spacing: -0.01em; margin-bottom: 0 !important; }}
h2, h3 {{ font-weight: 650 !important; letter-spacing: -0.005em; }}
h3 {{ font-size: 1.12rem !important; margin-top: 1.4rem !important; }}
.phu-de {{ color: {MUC_PHU}; font-size: 0.98rem; margin: 0.15rem 0 1.1rem 0; }}

/* Tab: chữ to, rõ */
.stTabs [data-baseweb="tab-list"] {{ gap: 0.4rem; border-bottom: 1px solid {VIEN}; }}
.stTabs [data-baseweb="tab"] {{ font-size: 0.98rem; font-weight: 600; padding: 0.55rem 0.9rem; color: {MUC_PHU}; }}
.stTabs [aria-selected="true"] {{ color: {MAU_CHINH}; }}

/* Thẻ số liệu */
.the-so {{ background: #ffffff; border: 1px solid {VIEN}; border-radius: 12px; padding: 0.95rem 1.1rem; height: 100%; }}
.the-so .nhan {{ color: {MUC_PHU}; font-size: 0.86rem; line-height: 1.3; }}
.the-so .gia-tri {{ color: {MUC_CHU}; font-size: 1.85rem; font-weight: 700; line-height: 1.2; margin-top: 0.2rem;
                    font-variant-numeric: tabular-nums; }}
.the-so .phu {{ color: {MUC_MO}; font-size: 0.82rem; margin-top: 0.15rem; }}

/* Khung tóm tắt và ghi chú */
.tom-tat {{ background: #ffffff; border: 1px solid {VIEN}; border-left: 4px solid {MAU_CHINH}; border-radius: 10px;
            padding: 0.85rem 1.1rem; margin: 0.2rem 0 1.1rem 0; font-size: 1.02rem; line-height: 1.5; }}
.ghi-chu {{ color: {MUC_PHU}; font-size: 0.88rem; line-height: 1.5; }}

/* Huy hiệu */
.huy-hieu {{ display: inline-block; padding: 0.16rem 0.6rem; border-radius: 999px; font-size: 0.86rem; font-weight: 650;
             white-space: nowrap; }}

/* Danh sách lý do */
ul.ly-do {{ margin: 0.3rem 0 0.2rem 1.1rem; padding: 0; line-height: 1.55; }}
ul.ly-do li {{ margin-bottom: 0.3rem; }}

/* Thanh bên */
section[data-testid="stSidebar"] {{ border-right: 1px solid {VIEN}; }}
section[data-testid="stSidebar"] h2 {{ font-size: 1rem !important; }}
</style>
"""


def nap_css() -> None:
    """Chèn kiểu dáng chung vào trang (gọi một lần ở đầu app)."""
    st.markdown(CSS, unsafe_allow_html=True)


def so(x, le: int = 0) -> str:
    """Viết số kiểu Việt Nam: 1.234 và 3,62. Giá trị trống hiện "–"."""
    if x is None or pd.isna(x):
        return "–"
    return f"{x:,.{le}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def the_so(cot, nhan: str, gia_tri: str, phu: str = "") -> None:
    """Vẽ một thẻ số liệu trong cột `cot`: nhãn nhỏ ở trên, con số lớn, dòng phụ bên dưới."""
    cot.markdown(f'<div class="the-so"><div class="nhan">{html.escape(nhan)}</div>'
                 f'<div class="gia-tri">{html.escape(gia_tri)}</div>'
                 f'<div class="phu">{html.escape(phu)}</div></div>', unsafe_allow_html=True)


def huy_hieu_muc(muc: object) -> str:
    """HTML huy hiệu của một mức năng lực, ví dụ "Advanced · Xuất sắc"."""
    viet, _, nen, chu = MUC_VIET.get(muc, (str(muc), "", "#ecebe6", MUC_PHU))
    ten = str(muc) if str(muc) == viet else f"{muc} · {viet}"
    return f'<span class="huy-hieu" style="background:{nen};color:{chu}">{html.escape(ten)}</span>'


def tom_tat(noi_dung_html: str) -> None:
    """Khung tóm tắt một câu ở đầu mỗi trang (nội dung là HTML đã được kiểm soát)."""
    st.markdown(f'<div class="tom-tat">{noi_dung_html}</div>', unsafe_allow_html=True)


def ghi_chu(chu: str) -> None:
    """Dòng ghi chú nhỏ, màu nhạt."""
    st.markdown(f'<div class="ghi-chu">{html.escape(chu)}</div>', unsafe_allow_html=True)


def danh_sach_ly_do(cac_y: list[str]) -> None:
    """Hiện các ý giải thích thành danh sách gạch đầu dòng (đã thoát ký tự HTML)."""
    muc = "".join(f"<li>{html.escape(y)}</li>" for y in cac_y if y.strip())
    st.markdown(f'<ul class="ly-do">{muc}</ul>', unsafe_allow_html=True)


def kieu_bieu_do(bd: alt.Chart) -> alt.Chart:
    """Áp kiểu chung cho biểu đồ: nền trong suốt, lưới mờ, chữ trục màu nhạt, không khung."""
    return (bd.configure(background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUC_PHU, titleColor=MUC_PHU, gridColor=VIEN, domainColor="#c3c2b7",
                            tickColor="#c3c2b7", labelFontSize=12, titleFontSize=12, titleFontWeight="normal")
            .configure_legend(labelColor=MUC_PHU, labelFontSize=12, symbolType="square", labelLimit=400))
