"""Xuất kết quả Giải pháp 2: bảng điểm hiệu chỉnh, GPA, biểu đồ và báo cáo.

Bảng điểm và GPA có Mã SV (dành cho nhà trường) → ghi vào 01_du-lieu/ket-qua/gp2/
(bị .gitignore chặn). Báo cáo Markdown chỉ có số liệu tổng hợp và mã lớp, không có Mã SV.
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
from .cau_hinh import CauHinhGP2  # noqa: E402

COT_DIEM = {
    "student": "Mã SV", "class_id": "Mã lớp HP", "course": "Mã môn", "year": "Năm học", "sem": "Học kỳ",
    "credits": "Số TC", "hp": "Điểm HP gốc", "Adjusted_Score": "Adjusted_Score", "dieu_chinh": "Điều chỉnh",
    "alpha": "α của lớp", "diem_ky_vong": "Điểm kỳ vọng", "ky_vong_thap": "Kỳ vọng – cận dưới 95%",
    "ky_vong_cao": "Kỳ vọng – cận trên 95%", "review_flag": "Cờ", "diem_de_xuat": "Điểm đề xuất (khi REVIEW)",
}
COT_LOP = {
    "class_id": "Mã lớp HP", "course": "Mã môn", "year": "Năm học", "sem": "Học kỳ", "n": "Số điểm hợp lệ",
    "anomaly_type": "Nhãn GP1", "anomaly_score": "Anomaly Score", "huong_hieu_chinh": "Hướng",
    "ref_level": "Mốc so sánh", "mean": "ĐTB lớp", "ref_mean": "ĐTB mốc", "delta_tho": "Δ thô",
    "delta_nang_luc": "Δ sau khi trừ năng lực nền", "delta": "Δ dùng", "alpha": "α",
    "dich_chuyen": "Số điểm bị trừ (âm = được cộng)",
}


def bang_diem_hieu_chinh(dd: pd.DataFrame) -> pd.DataFrame:
    """Bảng điểm hiệu chỉnh từng lượt (đầu ra Adjusted_Score), tên cột tiếng Việt."""
    dd = dd.assign(dieu_chinh=(dd["Adjusted_Score"] - dd["hp"]).round(2))
    return dd[list(COT_DIEM)].rename(columns=COT_DIEM)


def ve_bieu_do(sv: pd.DataFrame, lop: pd.DataFrame, thu_muc: Path) -> dict:
    """Vẽ phân phối GPA trước/sau và mức hiệu chỉnh của các lớp.

    Tham số:
        sv: bảng GPA; lop: bảng hiệu chỉnh theo lớp; thu_muc: nơi lưu PNG.
    Trả về:
        {tên file: đường dẫn}.
    Vì sao cần: đề yêu cầu biểu đồ phân phối Trước vs Sau.
    """
    thu_muc.mkdir(parents=True, exist_ok=True)
    ra = {}
    fig, ax = plt.subplots(figsize=(9, 4.5))
    khoang = np.arange(0, 10.01, 0.25)
    ax.hist(sv["GPA_goc"].dropna(), bins=khoang, alpha=0.55, label="GPA gốc", color="#9e9e9e")
    ax.hist(sv["Normalized_GPA"].dropna(), bins=khoang, histtype="step", lw=2, label="Normalized_GPA", color="#1e88e5")
    ax.set(xlabel="GPA hệ 10", ylabel="Số sinh viên", title="Phân phối GPA trước và sau hiệu chỉnh")
    ax.legend()
    fig.tight_layout()
    ra["1_gpa_truoc_sau.png"] = thu_muc / "1_gpa_truoc_sau.png"
    fig.savefig(ra["1_gpa_truoc_sau.png"], dpi=130)
    plt.close(fig)

    sua = lop[lop["dich_chuyen"].ne(0)].sort_values("dich_chuyen")
    if len(sua):
        fig, ax = plt.subplots(figsize=(10, max(4, 0.12 * len(sua))))
        mau = np.where(sua["dich_chuyen"] > 0, "#e53935", "#1e88e5")
        ax.barh(sua["class_id"] + " · " + sua["course"], -sua["dich_chuyen"], color=mau)
        ax.axvline(0, c="k", lw=0.8)
        ax.set(xlabel="Điểm được cộng (+) / bị trừ (−) cho cả lớp",
               title="Mức hiệu chỉnh của các lớp (đỏ: chấm dễ → trừ; xanh: chấm khắt khe → cộng)")
        ax.tick_params(axis="y", labelsize=6)
        fig.tight_layout()
        ra["2_muc_hieu_chinh_lop.png"] = thu_muc / "2_muc_hieu_chinh_lop.png"
        fig.savefig(ra["2_muc_hieu_chinh_lop.png"], dpi=130)
        plt.close(fig)
    return ra


def ghi_ket_qua(kq: dict, kc: pd.DataFrame | None, cfg: CauHinhGP2, thu_muc: Path) -> list[Path]:
    """Ghi các bảng CSV (UTF-8 có BOM để Excel đọc đúng tiếng Việt).

    Tham số:
        kq: kết quả chay_gp2(); kc: bảng kiểm chứng (có thể None); cfg: cấu hình; thu_muc: nơi ghi.
    Trả về:
        Danh sách file đã ghi.
    Vì sao cần: Adjusted_Score và Normalized_GPA là đầu ra bắt buộc; bảng theo lớp để giải thích.
    """
    thu_muc.mkdir(parents=True, exist_ok=True)
    bang = {
        "diem_hieu_chinh.csv": bang_diem_hieu_chinh(kq["diem"]),
        "hieu_chinh_theo_lop.csv": kq["lop"][list(COT_LOP)].rename(columns=COT_LOP),
        "gpa_sinh_vien.csv": kq["sv"].rename(columns={"student": "Mã SV"}),
        "tham_so.csv": pd.DataFrame(list(asdict(cfg).items()), columns=["tham_so", "gia_tri"]),
    }
    if kc is not None:
        bang["kiem_chung_gp2.csv"] = kc
    ra = []
    for ten, b in bang.items():
        p = thu_muc / ten
        b.to_csv(p, index=False, encoding="utf-8-sig")
        ra.append(p)
    return ra


def ghi_bao_cao(kq: dict, kc: pd.DataFrame | None, hinh: dict, thu_muc: Path) -> Path:
    """Ghi báo cáo tóm tắt Markdown (chỉ số liệu tổng hợp và mã lớp, không có Mã SV).

    Tham số:
        kq: kết quả chay_gp2(); kc: bảng kiểm chứng; hinh: biểu đồ; thu_muc: nơi ghi.
    Trả về:
        Đường dẫn file báo cáo.
    Vì sao cần: đọc nhanh kết quả, làm nguyên liệu cho báo cáo kỹ thuật.
    """
    lop, dd, sv = kq["lop"], kq["diem"], kq["sv"]
    sua = lop[lop["dich_chuyen"].ne(0)]
    tom_tat = pd.DataFrame([
        ("Lớp được hiệu chỉnh", len(sua)),
        ("– bị trừ điểm (chấm dễ)", int((sua["dich_chuyen"] > 0).sum())),
        ("– được cộng điểm (chấm khắt khe)", int((sua["dich_chuyen"] < 0).sum())),
        ("Lượt điểm được hiệu chỉnh", int(dd["duoc_hieu_chinh"].sum())),
        ("Mức hiệu chỉnh TB mỗi lớp (điểm, trị tuyệt đối)", round(float(sua["dich_chuyen"].abs().mean()), 2) if len(sua) else 0),
        ("Lượt điểm REVIEW_REQUIRED (chỉ gắn cờ)", int(dd["co_review"].sum())),
        ("Lượt điểm có điểm kỳ vọng", int(dd["diem_ky_vong"].notna().sum())),
        ("SV có GPA thay đổi", int(sv["chenh_GPA"].ne(0).sum())),
        ("GPA gốc TB", round(float(sv["GPA_goc"].mean()), 3)),
        ("Normalized_GPA TB", round(float(sv["Normalized_GPA"].mean()), 3)),
        ("Thay đổi GPA lớn nhất (trị tuyệt đối)", round(float(sv["chenh_GPA"].abs().max()), 3)),
    ], columns=["chi_so", "gia_tri"])
    top = sua.reindex(sua["dich_chuyen"].abs().sort_values(ascending=False).index).head(15)
    dong = ["# Báo cáo Giải pháp 2 – Hiệu chỉnh điểm", "",
            "Phương án A (chiết khấu α) sửa điểm cả lớp cho lớp đủ điều kiện ở Giải pháp 1; "
            "phương án C (điểm kỳ vọng) chỉ gắn cờ REVIEW_REQUIRED cho từng lượt điểm.", "",
            f"σ_w (độ dao động điểm chuẩn hóa của một SV giữa các môn) = {kq['sigma_w']:.3f}", "",
            "## Tóm tắt", "", bang_markdown(tom_tat, so_le=3), "",
            "## 15 lớp hiệu chỉnh nhiều nhất", "",
            bang_markdown(top[list(COT_LOP)].rename(columns=COT_LOP), so_le=2), ""]
    if kc is not None:
        dong += ["## Kiểm chứng bằng mô phỏng", "", bang_markdown(kc, so_le=2), ""]
    dong += ["## Biểu đồ", ""] + [f"![{t}](charts/{t})" for t in hinh]
    p = thu_muc / "BaoCao_GiaiPhap2.md"
    p.write_text("\n".join(dong), encoding="utf-8")
    return p
