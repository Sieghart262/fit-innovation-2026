"""GPA hệ 10 của từng SV trước và sau hiệu chỉnh (Normalized_GPA)."""

from __future__ import annotations

import pandas as pd


def _gpa(dd: pd.DataFrame, cot_diem: str) -> pd.DataFrame:
    """GPA có trọng số tín chỉ theo một cột điểm, mỗi môn lấy lần học có điểm cao nhất.

    Tham số:
        dd: bảng lượt điểm (student, course, credits và cột điểm).
        cot_diem: tên cột điểm dùng để tính.
    Trả về:
        Bảng mỗi SV: gpa, so_tc, so_mon.
    Vì sao cần: SV học lại một môn có nhiều dòng; lấy lần cao nhất để không đếm tín chỉ hai lần
    (giả định của đội – cần đối chiếu quy chế NEU).
    """
    co = dd[dd[cot_diem].notna() & dd["credits"].notna()]
    cao_nhat = co.sort_values(cot_diem).drop_duplicates(["student", "course"], keep="last")
    g = cao_nhat.assign(_tich=cao_nhat[cot_diem] * cao_nhat["credits"]).groupby("student")
    return pd.DataFrame({"gpa": g["_tich"].sum() / g["credits"].sum(),
                         "so_tc": g["credits"].sum(), "so_mon": g["course"].nunique()})


def tinh_gpa(dd: pd.DataFrame) -> pd.DataFrame:
    """Tính GPA hệ 10 trước (Điểm HP gốc) và sau hiệu chỉnh (Adjusted_Score) cho từng SV.

    Tham số:
        dd: bảng lượt điểm đã có Adjusted_Score, duoc_hieu_chinh, co_review.
    Trả về:
        Bảng mỗi SV: GPA_goc, Normalized_GPA, chenh_GPA, so_tc, so_mon,
        so_luot_duoc_hieu_chinh, so_luot_review.
    Vì sao cần: đầu ra Normalized_GPA của Giải pháp 2 và đầu vào cho Giải pháp 3 (TCI).
    """
    goc, hc = _gpa(dd, "hp"), _gpa(dd, "Adjusted_Score")
    sv = goc.rename(columns={"gpa": "GPA_goc"}).join(hc[["gpa"]].rename(columns={"gpa": "Normalized_GPA"}))
    sv["chenh_GPA"] = sv["Normalized_GPA"] - sv["GPA_goc"]
    g = dd.groupby("student")
    sv["so_luot_duoc_hieu_chinh"] = g["duoc_hieu_chinh"].sum().reindex(sv.index).fillna(0).astype(int)
    sv["so_luot_review"] = g["co_review"].sum().reindex(sv.index).fillna(0).astype(int)
    for c in ["GPA_goc", "Normalized_GPA", "chenh_GPA"]:
        sv[c] = sv[c].round(3)
    return sv.reset_index()
