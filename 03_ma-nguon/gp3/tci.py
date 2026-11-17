"""Tính TCI (True Competency Index, thang 4) và xếp mức năng lực cho từng SV.

    TCI = trung bình có trọng số tín chỉ của điểm thang 4, quy đổi từ Adjusted_Score (Giải pháp 2).
    GPA danh nghĩa (thang 4) tính y hệt nhưng từ Điểm HP gốc → so sánh được trước/sau.
    Mỗi môn lấy lần học có điểm cao nhất (cùng giả định với Giải pháp 2).
    Đồ án/thực tập/khóa luận được tính (quyết định của đội). Không co rút TCI về mức trung bình;
    SV học dưới 3 môn có độ tin cậy "Thấp".
    Lượt vắng thi (HP = 0 và Thi trống/0) KHÔNG tính vào GPA danh nghĩa lẫn TCI (quyết định của
    đội): vắng thi không đo năng lực, và Giải pháp 1 cũng loại các lượt này. SV không còn môn nào
    có điểm hợp lệ được ghi "Chưa đủ dữ liệu".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import cau_hinh as ch3


def lam_tron_nua_len(x: pd.Series, so_le: int) -> pd.Series:
    """Làm tròn kiểu "nửa lên": 8,45 → 8,5; 3,595 → 3,60.

    Tham số:
        x: cột số không âm (có thể có NaN).
        so_le: số chữ số thập phân giữ lại.
    Trả về:
        Cột đã làm tròn.
    Vì sao cần: round() của pandas làm tròn "nửa về số chẵn" và dính sai số nhị phân, nên 8,45
    thành 8,4 (B+) trong khi điểm học phần được làm tròn lên 8,5 (A). Sai một bậc điểm chữ ở
    đúng ranh giới là bất công với SV.
    """
    he_so = 10 ** so_le
    return np.floor(x.astype(float) * he_so + 0.5 + 1e-9) / he_so


def quy_doi(diem: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Quy đổi điểm thang 10 sang điểm chữ và thang 4 theo bảng NEU.

    Tham số:
        diem: cột điểm thang 10 (có thể có NaN).
    Trả về:
        (điểm thang 4, điểm chữ); ô thiếu điểm giữ NaN.
    Vì sao cần: TCI và mức năng lực của đề bài dùng thang 4. Điểm được làm tròn 1 chữ số
    kiểu "nửa lên" trước khi xét (như điểm HP chính thức), nên 8,45 → 8,5 → A.
    """
    r = lam_tron_nua_len(diem, 1)
    dk = [r >= nguong for nguong, _, _ in ch3.BANG_QUY_DOI]
    thang4 = pd.Series(np.select(dk, [d4 for _, _, d4 in ch3.BANG_QUY_DOI], default=np.nan), index=diem.index)
    chu = pd.Series(np.select(dk, [c for _, c, _ in ch3.BANG_QUY_DOI], default=""), index=diem.index)
    co = diem.notna()
    return thang4.where(co), chu.where(co)


def xep_muc(gia_tri: pd.Series) -> pd.Series:
    """Xếp mức năng lực (Advanced / Proficient / Intermediate / At-Risk) theo ngưỡng của đề."""
    v = lam_tron_nua_len(gia_tri, 2)
    dk = [v >= nguong for nguong, _ in ch3.MUC_NANG_LUC]
    return pd.Series(np.select(dk, [m for _, m in ch3.MUC_NANG_LUC], default=""), index=gia_tri.index).where(v.notna())


def mon_cua_sinh_vien(dd: pd.DataFrame, kq_gp1: pd.DataFrame) -> pd.DataFrame:
    """Gộp các lượt điểm thành 1 dòng cho mỗi (SV, môn), quy đổi thang 4 trước/sau.

    Tham số:
        dd: bảng lượt điểm từ Giải pháp 2 (hp, Adjusted_Score, credits, valid...).
        kq_gp1: kết quả Giải pháp 1 (để biết nhãn của lớp).
    Trả về:
        Bảng (student, course). "Sau": lần học có điểm hiệu chỉnh cao nhất (class_id, hp_lan_tinh,
        Adjusted_Score, d4_sau, chu_sau, nhan_lop_gp1). "Trước": lần học có điểm gốc cao nhất
        (lop_truoc, hp_truoc, d4_truoc, chu_truoc, nhan_lop_truoc). Thường là cùng một lần học;
        chỉ khác khi SV học lại và việc hiệu chỉnh làm đổi lần có điểm cao nhất.
    Vì sao cần: TCI và lời giải thích đều tính trên từng môn của SV. Chỉ lấy lượt có điểm hợp lệ
    (bỏ lượt vắng thi và lượt chưa có điểm).
    """
    co = dd[dd["valid"] & dd["credits"].notna()].copy()
    co["d4_truoc"], co["chu_truoc"] = quy_doi(co["hp"])
    co["d4_sau"], co["chu_sau"] = quy_doi(co["Adjusted_Score"])
    co["nhan_lop_gp1"] = co["class_id"].map(kq_gp1.set_index("class_id")["anomaly_type"])
    khoa = ["student", "course"]
    truoc = (co.sort_values("hp", kind="stable").drop_duplicates(khoa, keep="last").set_index(khoa)
             [["hp", "d4_truoc", "chu_truoc", "class_id", "nhan_lop_gp1"]]
             .rename(columns={"hp": "hp_truoc", "class_id": "lop_truoc", "nhan_lop_gp1": "nhan_lop_truoc"}))
    sau = co.sort_values("Adjusted_Score", kind="stable").drop_duplicates(khoa, keep="last").set_index(khoa)
    mon = sau[["class_id", "year", "sem", "credits", "hp", "Adjusted_Score", "d4_sau", "chu_sau",
               "duoc_hieu_chinh", "review_flag", "nhan_lop_gp1"]].join(truoc).reset_index()
    mon = mon.rename(columns={"hp": "hp_lan_tinh"})
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
                       "GPA4_goc": lam_tron_nua_len(g["_t"].sum() / g["credits"].sum(), 2),
                       "TCI": lam_tron_nua_len(g["_s"].sum() / g["credits"].sum(), 2),
                       "so_mon_hieu_chinh": g["_hc"].sum().astype(int),
                       "so_mon_review": g["_rv"].sum().astype(int)})
    sv["chenh"] = (sv["TCI"] - sv["GPA4_goc"]).round(2)
    sv["muc_truoc"], sv["muc_sau"] = xep_muc(sv["GPA4_goc"]), xep_muc(sv["TCI"])
    hang = {m_: i for i, m_ in enumerate(ch3.THU_TU_MUC)}  # 0 = Advanced
    h_truoc, h_sau = sv["muc_truoc"].map(hang), sv["muc_sau"].map(hang)
    sv["doi_muc"] = np.select([h_sau < h_truoc, h_sau > h_truoc], ["Lên mức", "Xuống mức"], default="Giữ nguyên")
    sv["do_tin_cay"] = np.where(sv["so_mon"] < cfg.so_mon_tin_cay, ch3.DO_TIN_CAY_THAP, ch3.DO_TIN_CAY_DU)
    return sv.reset_index()


def bo_sung_sinh_vien(sv: pd.DataFrame, dd: pd.DataFrame) -> pd.DataFrame:
    """Thêm số lượt vắng thi không được tính, và thêm các SV không có môn nào có điểm hợp lệ.

    Tham số:
        sv: bảng từ tinh_tci().
        dd: bảng lượt điểm từ Giải pháp 2 (cần cột student, absent).
    Trả về:
        Bảng SV có thêm cột so_luot_vang_thi; SV không có điểm hợp lệ nào được thêm vào với
        TCI để trống, mức "Chưa đủ dữ liệu" và độ tin cậy "Thấp".
    Vì sao cần: danh sách phân loại phải có đủ mọi SV; SV chỉ có lượt vắng thi không bị xếp
    At-Risk oan mà được ghi rõ là chưa đủ dữ liệu.
    """
    vang = dd[dd["absent"]].groupby("student").size()
    sv = sv.assign(so_luot_vang_thi=sv["student"].map(vang).fillna(0).astype(int))
    thieu = sorted(set(dd["student"].dropna()) - set(sv["student"]))
    if not thieu:
        return sv
    them = pd.DataFrame({"student": thieu, "so_mon": 0, "so_tc": 0.0, "GPA4_goc": np.nan, "TCI": np.nan,
                         "so_mon_hieu_chinh": 0, "so_mon_review": 0, "chenh": np.nan,
                         "muc_truoc": ch3.CHUA_DU_DU_LIEU, "muc_sau": ch3.CHUA_DU_DU_LIEU,
                         "doi_muc": "Giữ nguyên", "do_tin_cay": ch3.DO_TIN_CAY_THAP})
    them["so_luot_vang_thi"] = them["student"].map(vang).fillna(0).astype(int)
    return pd.concat([sv, them], ignore_index=True)
