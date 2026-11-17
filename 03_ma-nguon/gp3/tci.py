"""Tính TCI (True Competency Index, thang 4) và xếp mức năng lực cho từng SV.

    TCI = trung bình có trọng số tín chỉ của điểm thang 4, quy đổi từ Adjusted_Score (Giải pháp 2).
    GPA danh nghĩa (thang 4) tính y hệt nhưng từ Điểm HP gốc → so sánh được trước/sau.
    Mỗi môn lấy lần học có điểm cao nhất (cùng giả định với Giải pháp 2).
    Đồ án/thực tập/khóa luận được tính (quyết định của đội). Không co rút TCI về mức trung bình;
    SV học dưới 3 môn có độ tin cậy "Thấp".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import cau_hinh as ch3


def quy_doi(diem: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Quy đổi điểm thang 10 sang điểm chữ và thang 4 theo bảng NEU.

    Tham số:
        diem: cột điểm thang 10 (có thể có NaN).
    Trả về:
        (điểm thang 4, điểm chữ); ô thiếu điểm giữ NaN.
    Vì sao cần: TCI và mức năng lực của đề bài dùng thang 4. Điểm được làm tròn 1 chữ số
    trước khi xét (như điểm HP chính thức), nên 8,45 → 8,5 → A.
    """
    r = diem.astype(float).round(1)
    dk = [r >= nguong for nguong, _, _ in ch3.BANG_QUY_DOI]
    thang4 = pd.Series(np.select(dk, [d4 for _, _, d4 in ch3.BANG_QUY_DOI], default=np.nan), index=diem.index)
    chu = pd.Series(np.select(dk, [c for _, c, _ in ch3.BANG_QUY_DOI], default=""), index=diem.index)
    co = diem.notna()
    return thang4.where(co), chu.where(co)


def xep_muc(gia_tri: pd.Series) -> pd.Series:
    """Xếp mức năng lực (Advanced / Proficient / Intermediate / At-Risk) theo ngưỡng của đề."""
    v = gia_tri.round(2)
    dk = [v >= nguong for nguong, _ in ch3.MUC_NANG_LUC]
    return pd.Series(np.select(dk, [m for _, m in ch3.MUC_NANG_LUC], default=""), index=gia_tri.index).where(v.notna())


def mon_cua_sinh_vien(dd: pd.DataFrame, kq_gp1: pd.DataFrame) -> pd.DataFrame:
    """Gộp các lượt điểm thành 1 dòng cho mỗi (SV, môn), quy đổi thang 4 trước/sau.

    Tham số:
        dd: bảng lượt điểm từ Giải pháp 2 (hp, Adjusted_Score, credits...).
        kq_gp1: kết quả Giải pháp 1 (để biết nhãn của lớp).
    Trả về:
        Bảng (student, course): lớp được tính (lần học điểm cao nhất sau hiệu chỉnh), năm, học kỳ,
        số TC, điểm gốc/hiệu chỉnh, điểm chữ và thang 4 trước/sau, nhãn GP1 của lớp, cờ REVIEW.
    Vì sao cần: TCI và lời giải thích đều tính trên từng môn của SV.
    """
    co = dd[dd["hp"].notna() & dd["credits"].notna()].copy()
    co["d4_truoc"], co["chu_truoc"] = quy_doi(co["hp"])
    co["d4_sau"], co["chu_sau"] = quy_doi(co["Adjusted_Score"])
    khoa = ["student", "course"]
    truoc = co.groupby(khoa)["d4_truoc"].max().rename("d4_truoc_mon")
    chu_truoc = co.sort_values("hp").drop_duplicates(khoa, keep="last").set_index(khoa)["chu_truoc"]
    sau = co.sort_values("Adjusted_Score").drop_duplicates(khoa, keep="last").set_index(khoa)
    mon = sau[["class_id", "year", "sem", "credits", "hp", "Adjusted_Score", "d4_sau", "chu_sau",
               "duoc_hieu_chinh", "review_flag"]].join(truoc).join(chu_truoc).reset_index()
    nhan = kq_gp1.set_index("class_id")["anomaly_type"]
    mon["nhan_lop_gp1"] = mon["class_id"].map(nhan)
    mon = mon.rename(columns={"d4_truoc_mon": "d4_truoc", "hp": "hp_lan_tinh"})
    mon["anh_huong_tc"] = (mon["d4_sau"] - mon["d4_truoc"]) * mon["credits"]
    return mon


def tinh_tci(mon: pd.DataFrame, cfg: ch3.CauHinhGP3) -> pd.DataFrame:
    """Tính GPA thang 4 danh nghĩa, TCI, mức năng lực trước/sau và độ tin cậy cho từng SV.

    Tham số:
        mon: bảng từ mon_cua_sinh_vien().
        cfg: cấu hình.
    Trả về:
        Bảng mỗi SV: so_mon, so_tc, GPA4_goc, muc_truoc, TCI, muc_sau, doi_muc, do_tin_cay,
        so_mon_hieu_chinh, so_mon_review.
    Vì sao cần: đầu ra bắt buộc của Giải pháp 3 – danh sách phân loại toàn trường.
    """
    m = mon.assign(_t=mon["d4_truoc"] * mon["credits"], _s=mon["d4_sau"] * mon["credits"],
                   _hc=mon["duoc_hieu_chinh"].astype(bool), _rv=mon["review_flag"].astype(str).ne(""))
    g = m.groupby("student")
    sv = pd.DataFrame({"so_mon": g["course"].nunique(), "so_tc": g["credits"].sum(),
                       "GPA4_goc": (g["_t"].sum() / g["credits"].sum()).round(2),
                       "TCI": (g["_s"].sum() / g["credits"].sum()).round(2),
                       "so_mon_hieu_chinh": g["_hc"].sum().astype(int),
                       "so_mon_review": g["_rv"].sum().astype(int)})
    sv["chenh"] = (sv["TCI"] - sv["GPA4_goc"]).round(2)
    sv["muc_truoc"], sv["muc_sau"] = xep_muc(sv["GPA4_goc"]), xep_muc(sv["TCI"])
    hang = {m_: i for i, m_ in enumerate(ch3.THU_TU_MUC)}  # 0 = Advanced
    h_truoc, h_sau = sv["muc_truoc"].map(hang), sv["muc_sau"].map(hang)
    sv["doi_muc"] = np.select([h_sau < h_truoc, h_sau > h_truoc], ["Lên mức", "Xuống mức"], default="Giữ nguyên")
    sv["do_tin_cay"] = np.where(sv["so_mon"] < cfg.so_mon_tin_cay, ch3.DO_TIN_CAY_THAP, ch3.DO_TIN_CAY_DU)
    return sv.reset_index()
