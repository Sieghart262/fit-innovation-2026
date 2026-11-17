"""Xuất kết quả Giải pháp 3: danh sách phân loại, ma trận chuyển mức, biểu đồ Trước/Sau, báo cáo.

Danh sách phân loại có Mã SV (dành cho nhà trường) → 01_du-lieu/ket-qua/gp3/ (bị .gitignore chặn).
Báo cáo Markdown chỉ có số liệu tổng hợp.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from eda.report import bang_markdown  # noqa: E402
from . import cau_hinh as ch3  # noqa: E402

# Màu theo bảng màu đã kiểm tra (an toàn cho người mù màu): slot 1 xanh, slot 2 cam.
MAU_TRUOC, MAU_SAU = "#2a78d6", "#eb6834"
MUC_CHU, MUC_PHU, LUOI, NEN = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"

COT_PHAN_LOAI = {
    "student": "Mã SV", "so_mon": "Số môn", "so_tc": "Số TC", "GPA4_goc": "GPA thang 4 danh nghĩa",
    "muc_truoc": "Mức theo GPA danh nghĩa", "TCI": "TCI", "muc_sau": "Mức theo TCI", "chenh": "TCI − GPA",
    "doi_muc": "Thay đổi mức", "do_tin_cay": "Độ tin cậy", "so_mon_hieu_chinh": "Số môn bị hiệu chỉnh",
    "so_mon_review": "Số môn REVIEW_REQUIRED", "giai_thich": "Giải thích",
}


def ma_tran_chuyen_muc(sv: pd.DataFrame) -> pd.DataFrame:
    """Đếm số SV theo (mức danh nghĩa, mức TCI) – hàng là trước, cột là sau."""
    return (pd.crosstab(sv["muc_truoc"], sv["muc_sau"])
            .reindex(index=ch3.THU_TU_MUC, columns=ch3.THU_TU_MUC, fill_value=0))


def _trang_tri(ax) -> None:
    """Kiểu chung: lưới mờ, bỏ khung trên/phải, chữ màu mực phụ."""
    ax.set_facecolor(NEN)
    for k in ["top", "right"]:
        ax.spines[k].set_visible(False)
    for k in ["left", "bottom"]:
        ax.spines[k].set_color("#c3c2b7")
    ax.tick_params(colors=MUC_PHU)
    ax.grid(axis="y", color=LUOI, lw=0.8)
    ax.set_axisbelow(True)


def ve_bieu_do(sv: pd.DataFrame, thu_muc: Path) -> dict:
    """Vẽ 2 biểu đồ Trước/Sau: số SV theo mức, và phân phối GPA danh nghĩa so với TCI.

    Tham số:
        sv: bảng phân loại; thu_muc: nơi lưu PNG.
    Trả về:
        {tên file: đường dẫn}.
    Vì sao cần: đề yêu cầu biểu đồ phân phối Trước vs Sau.
    """
    thu_muc.mkdir(parents=True, exist_ok=True)
    ra = {}

    truoc = sv["muc_truoc"].value_counts().reindex(ch3.THU_TU_MUC, fill_value=0)
    sau = sv["muc_sau"].value_counts().reindex(ch3.THU_TU_MUC, fill_value=0)
    x = np.arange(len(ch3.THU_TU_MUC))
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=NEN)
    _trang_tri(ax)
    w = 0.38
    for dx, y, mau, nhan in [(-w / 2 - 0.01, truoc, MAU_TRUOC, "GPA danh nghĩa (trước)"),
                             (w / 2 + 0.01, sau, MAU_SAU, "TCI (sau)")]:
        cot = ax.bar(x + dx, y.values, width=w, color=mau, label=nhan)
        ax.bar_label(cot, labels=[f"{v:,}" for v in y.values], padding=2, fontsize=8, color=MUC_PHU)
    ax.set_xticks(x, ch3.THU_TU_MUC)
    ax.set_ylabel("Số sinh viên", color=MUC_PHU)
    ax.set_title("Số sinh viên theo mức năng lực: trước và sau hiệu chỉnh", color=MUC_CHU, loc="left")
    ax.legend(frameon=False, labelcolor=MUC_PHU)
    fig.tight_layout()
    ra["1_so_sv_theo_muc.png"] = thu_muc / "1_so_sv_theo_muc.png"
    fig.savefig(ra["1_so_sv_theo_muc.png"], dpi=130, facecolor=NEN)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=NEN)
    _trang_tri(ax)
    khoang = np.arange(0, 4.01, 0.1)
    ax.hist(sv["GPA4_goc"].dropna(), bins=khoang, histtype="step", lw=2, color=MAU_TRUOC, label="GPA danh nghĩa (trước)")
    ax.hist(sv["TCI"].dropna(), bins=khoang, histtype="step", lw=2, color=MAU_SAU, label="TCI (sau)")
    for nguong, _ in ch3.MUC_NANG_LUC[:-1]:
        ax.axvline(nguong, color="#c3c2b7", lw=1, ls="--")
    ax.set_xlabel("Thang 4 (đường đứt: ngưỡng 2,50 / 3,20 / 3,60)", color=MUC_PHU)
    ax.set_ylabel("Số sinh viên", color=MUC_PHU)
    ax.set_title("Phân phối GPA danh nghĩa và TCI", color=MUC_CHU, loc="left")
    ax.legend(frameon=False, labelcolor=MUC_PHU)
    fig.tight_layout()
    ra["2_phan_phoi_gpa_tci.png"] = thu_muc / "2_phan_phoi_gpa_tci.png"
    fig.savefig(ra["2_phan_phoi_gpa_tci.png"], dpi=130, facecolor=NEN)
    plt.close(fig)
    return ra


def ghi_ket_qua(kq: dict, kc: pd.DataFrame | None, cfg: ch3.CauHinhGP3, thu_muc: Path) -> list[Path]:
    """Ghi danh sách phân loại, môn của từng SV, ma trận chuyển mức và tham số ra CSV.

    Tham số:
        kq: kết quả chay_gp3(); kc: bảng kiểm chứng (có thể None); cfg: cấu hình; thu_muc: nơi ghi.
    Trả về:
        Danh sách file đã ghi.
    Vì sao cần: danh sách phân loại toàn trường là đầu ra bắt buộc; dashboard đọc các file này.
    """
    thu_muc.mkdir(parents=True, exist_ok=True)
    sv = kq["phan_loai"]
    bang = {
        "phan_loai_sinh_vien.csv": sv.reindex(columns=list(COT_PHAN_LOAI)).rename(columns=COT_PHAN_LOAI),
        "mon_cua_sinh_vien.csv": kq["mon_sv"],
        "ma_tran_chuyen_muc.csv": ma_tran_chuyen_muc(sv).reset_index(),
        "tham_so.csv": pd.DataFrame(list(asdict(cfg).items()), columns=["tham_so", "gia_tri"]),
    }
    if kc is not None:
        bang["kiem_chung_gp3.csv"] = kc
    ra = []
    for ten, b in bang.items():
        p = thu_muc / ten
        b.to_csv(p, index=False, encoding="utf-8-sig")
        ra.append(p)
    return ra


def ghi_bao_cao(kq: dict, kc: pd.DataFrame | None, hinh: dict, thu_muc: Path) -> Path:
    """Ghi báo cáo tóm tắt Markdown (chỉ số liệu tổng hợp, không có Mã SV).

    Tham số:
        kq: kết quả chay_gp3(); kc: bảng kiểm chứng; hinh: biểu đồ; thu_muc: nơi ghi.
    Trả về:
        Đường dẫn file báo cáo.
    Vì sao cần: nguyên liệu cho báo cáo kỹ thuật và video demo.
    """
    sv = kq["phan_loai"]
    theo_muc = pd.DataFrame({
        "muc": ch3.THU_TU_MUC,
        "so_sv_truoc": sv["muc_truoc"].value_counts().reindex(ch3.THU_TU_MUC, fill_value=0).values,
        "so_sv_sau": sv["muc_sau"].value_counts().reindex(ch3.THU_TU_MUC, fill_value=0).values})
    tom_tat = pd.DataFrame([
        ("Số SV được phân loại", len(sv)),
        ("SV đổi mức", int(sv["doi_muc"].ne("Giữ nguyên").sum())),
        ("– lên mức", int(sv["doi_muc"].eq("Lên mức").sum())),
        ("– xuống mức", int(sv["doi_muc"].eq("Xuống mức").sum())),
        ("SV có ít nhất 1 môn bị hiệu chỉnh", int(sv["so_mon_hieu_chinh"].gt(0).sum())),
        ("SV độ tin cậy thấp (< 3 môn)", int(sv["do_tin_cay"].eq(ch3.DO_TIN_CAY_THAP).sum())),
        ("GPA thang 4 danh nghĩa TB", round(float(sv["GPA4_goc"].mean()), 3)),
        ("TCI TB", round(float(sv["TCI"].mean()), 3)),
    ], columns=["chi_so", "gia_tri"])
    dong = ["# Báo cáo Giải pháp 3 – Phân loại năng lực thực chất (TCI)", "",
            "TCI = trung bình có trọng số tín chỉ của điểm thang 4 quy đổi từ điểm đã hiệu chỉnh (GP2). "
            "Mức: Advanced ≥ 3,60; Proficient 3,20–<3,60; Intermediate 2,50–<3,20; At-Risk < 2,50.", "",
            "## Tóm tắt", "", bang_markdown(tom_tat, so_le=3), "",
            "## Số SV theo mức", "", bang_markdown(theo_muc), "",
            "## Ma trận chuyển mức (hàng: theo GPA danh nghĩa, cột: theo TCI)", "",
            bang_markdown(ma_tran_chuyen_muc(sv).reset_index().rename(columns={"muc_truoc": "Trước \\ Sau"})), ""]
    if kc is not None:
        dong += ["## Kiểm chứng bằng mô phỏng", "", bang_markdown(kc, so_le=2), ""]
    dong += ["## Biểu đồ", ""] + [f"![{t}](charts/{t})" for t in hinh]
    p = thu_muc / "BaoCao_GiaiPhap3.md"
    p.write_text("\n".join(dong), encoding="utf-8")
    return p
