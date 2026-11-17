"""Tạo báo cáo kỹ thuật PDF (≤ 15 trang) cho vòng Bán kết FIT Innovation 2026.

Cách chạy (ở thư mục gốc dự án, sau khi đã chạy run_gp3.py --kiem-chung):
    .venv/Scripts/python.exe -X utf8 04_bao-cao/tao_bao_cao.py

Các bước:
    1. Đọc kết quả GP1–GP3 trong 01_du-lieu/ket-qua/ và CHỈ tính số liệu tổng hợp.
       Mọi nhóm SV dưới 5 người được ghi "<5" hoặc bị ẩn khỏi biểu đồ (eda/privacy.py).
    2. Vẽ biểu đồ vào 04_bao-cao/hinh/.
    3. Điền số liệu vào mau_bao_cao.html → bao_cao.html.
    4. In ra PDF bằng Microsoft Edge chạy ngầm trên máy (không gửi gì ra ngoài).

Muốn sửa lời văn: sửa mau_bao_cao.html rồi chạy lại. Số liệu nằm trong {{tên}} được điền tự động.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "03_ma-nguon"))
from eda import config as cf  # noqa: E402
from eda.privacy import kiem_tra_an_toan  # noqa: E402

THU_MUC = Path(__file__).resolve().parent
HINH = THU_MUC / "hinh"
KQ = Path(os.environ.get("FIT_KET_QUA", GOC / "01_du-lieu" / "ket-qua"))
NHO = cf.NGUONG_NHOM_TOI_THIEU  # 5

XANH, CAM, XAM, CHU, CHU_PHU = "#2a78d6", "#eb6834", "#b8bec6", "#1f2933", "#5b6673"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": XAM,
    "axes.labelcolor": CHU_PHU, "xtick.color": CHU_PHU, "ytick.color": CHU_PHU,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e6e9ed", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

MUC = ["Advanced", "Proficient", "Intermediate", "At-Risk"]
NHAN = ["HIGH_INFLATION", "UNUSUALLY_STEEP", "SUSPICIOUS_DISTRIBUTION", "NEEDS_REVIEW", "NORMAL",
        "NO_REFERENCE", "INCOMPLETE_DATA", "INSUFFICIENT_DATA"]


# ---------------------------------------------------------------------------
# Định dạng số kiểu Việt Nam
# ---------------------------------------------------------------------------
def so(x: float, le: int = 0) -> str:
    """Định dạng số kiểu Việt Nam: 1.234,5.

    Tham số:
        x: số cần định dạng; le: số chữ số thập phân.
    Trả về:
        Chuỗi đã định dạng ("–" nếu thiếu).
    Vì sao cần: báo cáo tiếng Việt dùng dấu phẩy thập phân, dấu chấm hàng nghìn.
    """
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    s = f"{x:,.{le}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def pt(x: float, le: int = 0) -> str:
    """Định dạng tỷ lệ (0–1) thành phần trăm kiểu Việt Nam, vd 0,321 → "32%"."""
    return "–" if x is None or np.isnan(x) else so(100 * x, le) + "%"


def dem_sv(n: int) -> str:
    """Số SV để công bố: nhóm 1–4 người ghi "<5" (quy tắc riêng tư của BTC)."""
    return "<5" if 0 < n < NHO else so(n)


# ---------------------------------------------------------------------------
# 1. Số liệu tổng hợp
# ---------------------------------------------------------------------------
def doc(ten: str) -> pd.DataFrame:
    """Đọc một file CSV kết quả (UTF-8 có BOM)."""
    return pd.read_csv(KQ / ten, encoding="utf-8-sig", low_memory=False)


def so_lieu_gp1(s: dict) -> pd.DataFrame:
    """Tính số liệu tổng hợp của GP1 (đơn vị là LỚP, không có số liệu từng SV).

    Tham số:
        s: dict số liệu, được ghi thêm vào.
    Trả về:
        Bảng chỉ số lớp (để vẽ hình; không xuất ra báo cáo dạng bảng từng lớp).
    Vì sao cần: phần kết quả GP1 trong báo cáo.
    """
    c = doc("gp1/chi_so_chi_tiet.csv")
    s["so_lop"] = so(len(c))
    s["so_mon"] = so(c["course"].nunique())
    dem = c["anomaly_type"].value_counts()
    for n in NHAN:
        s[f"n_{n}"] = so(int(dem.get(n, 0)))
    bt = c["anomaly_type"].isin(NHAN[:3])
    s["n_bat_thuong"] = so(int(bt.sum()))
    s["pt_bat_thuong"] = pt(bt.mean(), 1)
    s["n_co_moc"] = so(int(c["z_mean"].notna().sum()))
    rl = c["ref_level"].fillna("").astype(str)
    s["n_moc_mon"] = so(int((rl == "Cùng môn").sum()))
    s["n_moc_nhom"] = so(int(rl.str.startswith("Cùng nhóm môn").sum()))
    s["n_du_dk"] = so(int(c["du_dieu_kien_hieu_chinh"].eq(True).sum()))
    s["n_ca_hai"] = so(int(c["ca_hai_cung_nghi"].eq(True).sum()))
    s["pt_ca_hai"] = pt(c["ca_hai_cung_nghi"].eq(True).sum() / max(bt.sum(), 1))
    thuong = c[~c["is_project"].astype(bool) & c["a_rate"].notna() & (c["n"] > 5)]
    s["pt_tren60_A"] = pt((thuong["a_rate"] > 0.6).mean(), 1)
    s["n_tren60_A"] = so(int((thuong["a_rate"] > 0.6).sum()))
    s["n_tren60_A_high"] = so(int(((thuong["a_rate"] > 0.6) & (thuong["anomaly_type"] == "HIGH_INFLATION")).sum()))
    sev = c["severity"].value_counts()
    for k, ten in [("Rất cao", "rat_cao"), ("Cao", "cao"), ("Trung bình", "tb"), ("Thấp", "thap")]:
        s[f"sev_{ten}"] = so(int(sev.get(k, 0)))
    return c


def so_lieu_gp2(s: dict) -> pd.DataFrame:
    """Tính số liệu tổng hợp của GP2: lớp được hiệu chỉnh, lượt điểm, GPA hệ 10.

    Tham số:
        s: dict số liệu, được ghi thêm vào.
    Trả về:
        Bảng hiệu chỉnh theo lớp (để vẽ hình).
    Vì sao cần: phần kết quả GP2 trong báo cáo.
    """
    lop = doc("gp2/hieu_chinh_theo_lop.csv")
    dc = pd.to_numeric(lop["Số điểm bị trừ (âm = được cộng)"], errors="coerce").fillna(0)
    sua = dc.ne(0)
    s["n_lop_sua"] = so(int(sua.sum()))
    s["n_lop_tru"] = so(int((dc > 0).sum()))
    s["n_lop_cong"] = so(int((dc < 0).sum()))
    s["dc_tb"] = so(dc[sua].abs().mean(), 2)
    s["dc_max"] = so(dc[sua].abs().max(), 2)
    s["n_cham_tran"] = so(int((dc.abs() >= 1.999).sum()))
    a = pd.to_numeric(lop.loc[sua, "α"], errors="coerce")
    s["alpha_min"], s["alpha_tb"], s["alpha_max"] = so(a.min(), 2), so(a.mean(), 2), so(a.max(), 2)

    d = doc("gp2/diem_hieu_chinh.csv")
    co_diem = d["Điểm HP gốc"].notna()
    s["n_luot"] = so(int(co_diem.sum()))
    s["n_luot_sua"] = so(int(pd.to_numeric(d["Điều chỉnh"], errors="coerce").fillna(0).ne(0).sum()))
    rv = d["Cờ"].astype(str).eq("REVIEW_REQUIRED")
    s["n_review"] = so(int(rv.sum()))
    s["pt_review"] = pt(rv.sum() / co_diem.sum(), 1)
    s["n_co_ky_vong"] = so(int(d["Điểm kỳ vọng"].notna().sum()))

    g = doc("gp2/gpa_sinh_vien.csv")
    ch = g["chenh_GPA"].fillna(0)
    s["n_sv_gpa"] = so(len(g))
    s["n_sv_gpa_doi"] = so(int(ch.ne(0).sum()))
    s["gpa10_doi_tb"] = so(ch[ch.ne(0)].abs().mean(), 3)
    s["gpa10_doi_max"] = so(ch.abs().max(), 2)
    return lop


def so_lieu_gp3(s: dict) -> pd.DataFrame:
    """Tính số liệu tổng hợp của GP3: số SV theo mức trước/sau, ma trận chuyển mức (ẩn nhóm < 5).

    Tham số:
        s: dict số liệu, được ghi thêm vào.
    Trả về:
        Bảng phân loại SV (chỉ dùng để vẽ hình tổng hợp, không xuất từng dòng).
    Vì sao cần: phần kết quả GP3 và biểu đồ GPA danh nghĩa vs TCI mà đề bắt buộc.
    """
    p = doc("gp3/phan_loai_sinh_vien.csv").rename(columns={
        "GPA thang 4 danh nghĩa": "gpa", "Mức theo GPA danh nghĩa": "truoc", "Mức theo TCI": "sau",
        "Thay đổi mức": "doi", "Độ tin cậy": "tin_cay", "TCI − GPA": "chenh"})
    s["n_sv"] = so(len(p))
    co = p["TCI"].notna()
    s["n_sv_tci"] = so(int(co.sum()))
    s["n_chua_du"] = dem_sv(int((~co).sum()))
    s["n_tin_cay_thap"] = so(int(p["tin_cay"].eq("Thấp").sum()))
    s["pt_tin_cay_thap"] = pt(p["tin_cay"].eq("Thấp").mean())
    s["gpa_tb"], s["tci_tb"] = so(p["gpa"].mean(), 3), so(p["TCI"].mean(), 3)
    ch = p["chenh"].fillna(0)
    s["n_sv_tci_doi"] = so(int(ch.ne(0).sum()))
    s["tci_doi_tb"] = so(ch[ch.ne(0)].abs().mean(), 2)
    s["n_doi_muc"] = dem_sv(int(p["doi"].ne("Giữ nguyên").sum()))
    s["n_len_muc"] = dem_sv(int(p["doi"].eq("Lên mức").sum()))
    s["n_xuong_muc"] = dem_sv(int(p["doi"].eq("Xuống mức").sum()))
    s["pt_doi_muc"] = pt(p["doi"].ne("Giữ nguyên").sum() / co.sum(), 1)
    for m in MUC:
        k = m.replace("-", "")
        s[f"truoc_{k}"] = dem_sv(int(p["truoc"].eq(m).sum()))
        s[f"sau_{k}"] = dem_sv(int(p["sau"].eq(m).sum()))

    # Ma trận chuyển mức – ô 1–4 SV ghi "<5"
    mt = pd.crosstab(p["truoc"], p["sau"]).reindex(index=MUC, columns=MUC, fill_value=0)
    dong = []
    for m in MUC:
        o = "".join(f"<td{' class=\"cheo\"' if m == m2 else ''}>{dem_sv(int(mt.loc[m, m2]))}</td>" for m2 in MUC)
        dong.append(f"<tr><th>{m}</th>{o}</tr>")
    s["bang_chuyen_muc"] = "\n".join(dong)
    return p


def so_lieu_kiem_chung(s: dict) -> None:
    """Đọc 3 bảng kiểm chứng mô phỏng (đơn vị là kịch bản, số tổng hợp) thành bảng HTML.

    Tham số:
        s: dict số liệu, được ghi thêm vào.
    Vì sao cần: bằng chứng định lượng rằng thuật toán bắt đúng và không sửa oan.
    """
    k1 = doc("gp1/kiem_chung_mo_phong.csv")
    s["bang_kc1"] = "\n".join(
        f"<tr><td>{r.kich_ban}</td><td><code>{r.nhan_mong_doi.replace(' hoặc ', '</code> / <code>')}</code></td>"
        f"<td>{pt(r.ty_le_dung_nhan)}</td><td>{pt(r.ty_le_duoc_sua_diem)}</td><td>{r.mong_doi_sua_diem}</td>"
        f"<td>{pt(r.ty_le_bao_dong_gia, 1)}</td></tr>" for r in k1.itertuples())
    s["kc1_bao_dong_gia_max"] = pt(k1["ty_le_bao_dong_gia"].max(), 1)
    by = k1.set_index("kich_ban")
    tim = lambda khoa: by[by.index.str.contains(khoa)].iloc[0]  # noqa: E731
    s["kc1_lam_phat"] = pt(tim("chấm dễ")["ty_le_dung_nhan"])
    s["kc1_ep"] = pt(tim("khắt khe")["ty_le_dung_nhan"])
    s["kc1_gioi_sua_oan"] = pt(tim("giỏi thật")["ty_le_duoc_sua_diem"])
    s["kc1_kttx_rong"] = pt(tim("rộng tay")["ty_le_dung_nhan"])

    k2 = doc("gp2/kiem_chung_gp2.csv")
    s["bang_kc2"] = "\n".join(
        f"<tr><td>{r.kich_ban}</td><td>{so(r.diem_da_cai, 1)}</td><td>{pt(r.ty_le_lop_duoc_hieu_chinh)}</td>"
        f"<td>{so(r.dich_chuyen_tb, 2)}</td><td>{pt(r.ty_le_phan_cai_duoc_go)}</td>"
        f"<td>{so(r.dich_chuyen_tb_lop_khong_cai, 3)}</td></tr>" for r in k2.itertuples())

    k3 = doc("gp3/kiem_chung_gp3.csv")
    kiem_tra_an_toan(k3, "kiểm chứng GP3", cot_dem="so_sv_bi_anh_huong")
    s["bang_kc3"] = "\n".join(
        f"<tr><td>{r.kich_ban}</td><td>{so(r.so_sv_bi_anh_huong)}</td><td>{so(r.gpa_danh_nghia_doi_tb, 3)}</td>"
        f"<td>{so(r.tci_doi_tb, 3)}</td><td>{pt(r.ty_le_go_hoac_giu)} ({r.y_nghia_ty_le})</td>"
        f"<td>{dem_sv(int(r.so_sv_doi_muc_danh_nghia))}</td><td>{pt(r.ty_le_ve_dung_muc)}</td></tr>"
        for r in k3.itertuples())


# ---------------------------------------------------------------------------
# 2. Biểu đồ
# ---------------------------------------------------------------------------
def luu(fig, ten: str) -> None:
    """Lưu hình vào 04_bao-cao/hinh/ và đóng lại."""
    HINH.mkdir(exist_ok=True)
    fig.savefig(HINH / ten)
    plt.close(fig)


def hinh_nguong_co_dinh(c: pd.DataFrame) -> None:
    """Hình 1: theo năm học, % lớp thường có > 60% điểm A so với % lớp bị GP1 gắn nhãn bất thường.

    Vì sao cần: chứng minh ngưỡng cố định 60% của đề sẽ gắn cờ ồ ạt khi điểm tăng dần qua các năm,
    còn mốc tương đối của GP1 thì ổn định. Đơn vị là lớp, không có số liệu SV.
    """
    t = c[~c["is_project"].astype(bool) & c["a_rate"].notna() & (c["n"] > 5)].copy()
    t["tren60"] = t["a_rate"] > 0.6
    t["bt"] = t["anomaly_type"].isin(NHAN[:3])
    g = t.groupby("year").agg(tren60=("tren60", "mean"), bt=("bt", "mean")).sort_index()
    kiem_tra_an_toan(g, "hình 1", ly_do_khong_dem="tỷ lệ số lớp theo năm, không có nhóm người")
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    x = np.arange(len(g))
    ax.plot(x, 100 * g["tren60"], color=CAM, lw=2, marker="o", ms=4)
    ax.plot(x, 100 * g["bt"], color=XANH, lw=2, marker="o", ms=4)
    ax.text(x[-1] + 0.12, 100 * g["tren60"].iloc[-1], "Ngưỡng cố định: > 60% điểm A", color=CHU, va="center", fontsize=8)
    ax.text(x[-1] + 0.12, 100 * g["bt"].iloc[-1], "GP1: mốc tương đối + bằng chứng", color=CHU, va="center", fontsize=8)
    ax.set_xticks(x, [str(n)[:4] + "-" + str(n)[-2:] for n in g.index])
    ax.set_xlim(-0.3, len(g) + 2.6)
    ax.set_ylabel("% số lớp thường bị gắn cờ")
    ax.grid(axis="x", visible=False)
    luu(fig, "h1_nguong_co_dinh.png")


def hinh_nhan_gp1(c: pd.DataFrame) -> None:
    """Hình 2: số lớp theo nhãn GP1 (3 nhãn của đề tô màu, nhãn bổ sung màu xám).

    Vì sao cần: cho thấy GP1 thận trọng – phần lớn lớp lệch chỉ được gắn "cần xem xét".
    """
    dem = c["anomaly_type"].value_counts().reindex(NHAN, fill_value=0)[::-1]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    mau = [XANH if n in NHAN[:3] else XAM for n in dem.index]
    ax.barh(dem.index, dem.values, color=mau, height=0.62)
    for i, v in enumerate(dem.values):
        ax.text(v + 6, i, so(int(v)), va="center", color=CHU, fontsize=8)
    ax.set_xlabel("Số lớp học phần")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, dem.max() * 1.1)
    luu(fig, "h2_nhan_gp1.png")


def hinh_dich_chuyen(lop: pd.DataFrame) -> None:
    """Hình 3: phân bố số điểm được cộng/bị trừ ở các lớp được hiệu chỉnh (đơn vị: lớp).

    Vì sao cần: cho thấy mức hiệu chỉnh vừa phải, đúng hướng và nằm trong giới hạn ±2 điểm.
    """
    dc = -pd.to_numeric(lop["Số điểm bị trừ (âm = được cộng)"], errors="coerce").fillna(0)
    dc = dc[dc.ne(0)]
    fig, ax = plt.subplots(figsize=(6.4, 2.3))
    bins = np.arange(-2.0, 2.01, 0.2)
    ax.hist(dc[dc < 0], bins=bins, color=CAM, edgecolor="white", linewidth=1.5, label="Bị trừ (chấm dễ)")
    ax.hist(dc[dc > 0], bins=bins, color=XANH, edgecolor="white", linewidth=1.5, label="Được cộng (chấm khắt khe)")
    ax.axvline(0, color=XAM, lw=1)
    ax.set_xlabel("Số điểm thay đổi của mỗi SV trong lớp (thang 10)")
    ax.set_ylabel("Số lớp")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="x", visible=False)
    luu(fig, "h3_dich_chuyen_gp2.png")


def _hist_an_nho(x: pd.Series, bins: np.ndarray) -> tuple[np.ndarray, int]:
    """Đếm histogram và đặt về 0 các khoảng có 1–4 SV.

    Trả về:
        (số SV mỗi khoảng sau khi ẩn, số khoảng bị ẩn).
    Vì sao cần: một cột 1–4 SV trên biểu đồ công bố là nhóm dưới 5 người.
    """
    h, _ = np.histogram(x.dropna(), bins=bins)
    nho = (h > 0) & (h < NHO)
    return np.where(nho, 0, h), int(nho.sum())


def hinh_gpa_tci(p: pd.DataFrame, s: dict) -> None:
    """Hình 4 (đề bắt buộc): phân phối GPA danh nghĩa và TCI; số SV theo mức trước/sau.

    Vì sao cần: biểu đồ "GPA danh nghĩa vs TCI" là yêu cầu bắt buộc của báo cáo.
    Các khoảng/cột có 1–4 SV bị ẩn.
    """
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"width_ratios": [1.35, 1]})
    bins = np.arange(0, 4.0001, 0.25)
    h1, an1 = _hist_an_nho(p["gpa"], bins)
    h2, an2 = _hist_an_nho(p["TCI"], bins)
    giua = (bins[:-1] + bins[1:]) / 2
    a1.bar(giua - 0.06, h1, width=0.11, color=XANH, label="GPA danh nghĩa")
    a1.bar(giua + 0.06, h2, width=0.11, color=CAM, label="TCI")
    for x0 in (2.5, 3.2, 3.6):
        a1.axvline(x0, color=CHU_PHU, lw=0.8, ls=":")
    a1.set_xlabel("Thang 4 (vạch chấm: ngưỡng 2,50 / 3,20 / 3,60)")
    a1.set_ylabel("Số SV")
    a1.set_title("Phân phối GPA danh nghĩa và TCI", loc="left", fontsize=9, color=CHU)
    a1.legend(frameon=False, fontsize=8, loc="upper left")
    a1.grid(axis="x", visible=False)
    s["so_khoang_an"] = so(an1 + an2)

    tr = p["truoc"].value_counts().reindex(MUC, fill_value=0)
    sa = p["sau"].value_counts().reindex(MUC, fill_value=0)
    x = np.arange(len(MUC))
    w = 0.38
    for dx, v, mau, ten in [(-w / 2, tr, XANH, "Theo GPA danh nghĩa"), (w / 2, sa, CAM, "Theo TCI")]:
        v = v.where(v >= NHO, 0)
        a2.bar(x + dx, v.values, width=w - 0.04, color=mau, label=ten)
    a2.set_xticks(x, MUC, fontsize=8)
    a2.set_title("Số SV theo mức", loc="left", fontsize=9, color=CHU)
    a2.set_ylim(0, max(tr.max(), sa.max()) * 1.25)
    a2.legend(frameon=False, fontsize=7.5, loc="upper right", ncol=2)
    a2.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=2)
    luu(fig, "h4_gpa_vs_tci.png")


def hinh_chenh_tci(p: pd.DataFrame) -> None:
    """Hình 5: phân bố TCI − GPA danh nghĩa ở các SV có TCI khác GPA (khoảng < 5 SV bị ẩn).

    Vì sao cần: cho thấy hiệu chỉnh tác động hai chiều và độ lớn thường nhỏ.
    """
    ch = p["chenh"].dropna()
    ch = ch[ch.ne(0)]
    bins = np.arange(-0.6, 0.6001, 0.05)
    h, _ = _hist_an_nho(ch.clip(-0.599, 0.599), bins)
    fig, ax = plt.subplots(figsize=(6.4, 2.2))
    giua = (bins[:-1] + bins[1:]) / 2
    ax.bar(giua, h, width=0.045, color=np.where(giua < 0, CAM, XANH))
    ax.axvline(0, color=XAM, lw=1)
    ax.set_xlabel("TCI − GPA danh nghĩa (thang 4); âm: bị kéo xuống, dương: được kéo lên")
    ax.set_ylabel("Số SV")
    ax.grid(axis="x", visible=False)
    luu(fig, "h5_chenh_tci.png")


# ---------------------------------------------------------------------------
# 3–4. Điền mẫu và in PDF
# ---------------------------------------------------------------------------
def tim_edge() -> Path:
    """Tìm msedge.exe trên máy Windows."""
    for p in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]:
        if Path(p).exists():
            return Path(p)
    raise FileNotFoundError("Không tìm thấy Microsoft Edge để in PDF.")


def in_pdf(html: Path, pdf: Path) -> int:
    """In file HTML ra PDF bằng Edge chạy ngầm; trả về số trang.

    Vì sao cần: Edge có sẵn trên Windows, in đúng phông tiếng Việt và CSS khổ A4,
    không cần cài thêm thư viện và không gửi dữ liệu ra ngoài.
    """
    pdf.unlink(missing_ok=True)
    subprocess.run([str(tim_edge()), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", html.as_uri()], check=True, capture_output=True, timeout=120)
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def main() -> None:
    """Chạy cả 4 bước; màn hình chỉ in số liệu tổng hợp."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chi-so-lieu", action="store_true", help="chỉ tính số liệu và vẽ hình, không in PDF")
    args = ap.parse_args()

    s: dict = {}
    c = so_lieu_gp1(s)
    lop = so_lieu_gp2(s)
    p = so_lieu_gp3(s)
    so_lieu_kiem_chung(s)
    hinh_nguong_co_dinh(c)
    hinh_nhan_gp1(c)
    hinh_dich_chuyen(lop)
    hinh_gpa_tci(p, s)
    hinh_chenh_tci(p)
    (THU_MUC / "so_lieu.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print({k: v for k, v in s.items() if not k.startswith("bang_")})
    if args.chi_so_lieu:
        return

    mau = (THU_MUC / "mau_bao_cao.html").read_text(encoding="utf-8")
    thieu = sorted(set(re.findall(r"\{\{(\w+)\}\}", mau)) - set(s))
    if thieu:
        raise KeyError(f"Mẫu có ô chưa có số liệu: {thieu}")
    html = re.sub(r"\{\{(\w+)\}\}", lambda m: str(s[m.group(1)]), mau)
    (THU_MUC / "bao_cao.html").write_text(html, encoding="utf-8")
    trang = in_pdf(THU_MUC / "bao_cao.html", THU_MUC / "BaoCao_FIT-Innovation-2026.pdf")
    print(f"Đã in PDF: {trang} trang" + ("  (VƯỢT 15 TRANG!)" if trang > 15 else ""))


if __name__ == "__main__":
    main()
