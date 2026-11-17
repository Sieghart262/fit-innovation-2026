"""Phương án A: hiệu chỉnh điểm cả lớp bằng hệ số chiết khấu α.

    Điểm hiệu chỉnh = Điểm − (1 − α) × Δ
        Δ: phần lệch do cách chấm (điểm), lấy THẬN TRỌNG = mức nhỏ hơn giữa
           - lệch thô: ĐTB lớp − ĐTB mốc;
           - lệch sau khi trừ năng lực nền: SV ở lớp này cao/thấp hơn chính họ ở lớp khác,
             so với các lớp mốc (chỉ có khi mốc là cùng môn và lớp đủ SV có năng lực nền).
        α = 1 − Anomaly Score, kẹp trong [0,05; 1]: lớp càng bất thường thì gỡ càng nhiều phần lệch.

Chỉ lớp "đủ điều kiện hiệu chỉnh" ở Giải pháp 1 (lệch + có bằng chứng) mới bị sửa; mọi lớp
khác có α = 1 (giữ nguyên điểm). Thứ hạng giữa các SV trong cùng lớp không đổi.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .cau_hinh import CauHinhGP2


def tinh_dich_chuyen_lop(kq: pd.DataFrame, ds_moc: dict, d: pd.DataFrame, cfg: CauHinhGP2) -> pd.DataFrame:
    """Tính Δ, α và mức dịch chuyển điểm cho từng lớp.

    Tham số:
        kq: bảng kết quả Giải pháp 1 (1 dòng/lớp).
        ds_moc: {mã lớp: danh sách lớp mốc} từ Giải pháp 1.
        d: bảng lượt điểm đã xử lý ở Giải pháp 1 (có sd_chuan, valid).
        cfg: cấu hình.
    Trả về:
        Bảng 1 dòng/lớp: delta_tho, delta_nang_luc, delta, alpha, dich_chuyen (số điểm bị TRỪ;
        âm nghĩa là được cộng), cùng nhãn và Anomaly Score của GP1.
    Vì sao cần: tách phần tính toán theo lớp để dễ kiểm tra và giải thích.
    """
    cot = ["class_id", "course", "year", "sem", "n", "anomaly_type", "anomaly_score",
           "du_dieu_kien_hieu_chinh", "huong_hieu_chinh", "ref_level", "mean", "ref_mean", "resid_mean"]
    lop = kq.reindex(columns=cot).copy()  # reindex: thiếu cột nào thì để trống thay vì báo lỗi
    for c in ["mean", "ref_mean", "resid_mean", "anomaly_score"]:
        lop[c] = pd.to_numeric(lop[c], errors="coerce")
    lop["du_dieu_kien_hieu_chinh"] = lop["du_dieu_kien_hieu_chinh"].eq(True)
    sd_lop = d[d["valid"]].groupby("class_id")["sd_chuan"].mean()
    lop["sd_lop"] = lop["class_id"].map(sd_lop)

    resid = kq.set_index("class_id")["resid_mean"]
    lop["ref_resid"] = [float(resid.reindex(ds_moc[c]).median()) if c in ds_moc else np.nan
                        for c in lop["class_id"]]

    lop["delta_tho"] = lop["mean"] - lop["ref_mean"]
    cung_mon = lop["ref_level"].eq("Cùng môn")
    lop["delta_nang_luc"] = np.where(cung_mon, (lop["resid_mean"] - lop["ref_resid"]) * lop["sd_lop"], np.nan)

    co_nl = lop["delta_nang_luc"].notna()
    cung_dau = np.sign(lop["delta_tho"]) == np.sign(lop["delta_nang_luc"])
    nho_hon = np.sign(lop["delta_tho"]) * np.minimum(lop["delta_tho"].abs(), lop["delta_nang_luc"].abs())
    # Năng lực nền nói ngược chiều (SV giải thích hết độ lệch) → không có phần nào do cách chấm
    lop["delta"] = np.where(co_nl, np.where(cung_dau, nho_hon, 0.0), lop["delta_tho"])
    # Chỉ sửa đúng hướng nhãn: "Giảm" thì Δ ≥ 0, "Tăng" thì Δ ≤ 0
    lop["delta"] = np.where(lop["huong_hieu_chinh"].eq("Giảm"), lop["delta"].clip(lower=0),
                            np.where(lop["huong_hieu_chinh"].eq("Tăng"), lop["delta"].clip(upper=0), 0.0))

    du = lop["du_dieu_kien_hieu_chinh"]
    lop["alpha"] = np.where(du, (1 - lop["anomaly_score"]).clip(cfg.alpha_min, 1.0), 1.0)
    lop["dich_chuyen"] = np.where(du, ((1 - lop["alpha"]) * lop["delta"]).clip(-cfg.dieu_chinh_toi_da,
                                                                            cfg.dieu_chinh_toi_da), 0.0)
    lop["dich_chuyen"] = lop["dich_chuyen"].fillna(0.0)
    return lop


def ap_dung(d: pd.DataFrame, lop: pd.DataFrame, cfg: CauHinhGP2) -> pd.DataFrame:
    """Áp mức dịch chuyển của lớp vào từng lượt điểm → cột Adjusted_Score.

    Tham số:
        d: bảng lượt điểm (có hp, valid, absent).
        lop: bảng từ tinh_dich_chuyen_lop().
        cfg: cấu hình.
    Trả về:
        Bản sao d có thêm alpha, dich_chuyen, Adjusted_Score, duoc_hieu_chinh.
        SV vắng thi (HP = 0) và ô chưa có điểm giữ nguyên; điểm kẹp trong 0–10.
    Vì sao cần: đây là bảng điểm hiệu chỉnh – đầu ra bắt buộc của Giải pháp 2.
    """
    dd = d.merge(lop[["class_id", "alpha", "dich_chuyen"]], on="class_id", how="left")
    dd[["alpha", "dich_chuyen"]] = dd[["alpha", "dich_chuyen"]].fillna({"alpha": 1.0, "dich_chuyen": 0.0})
    sua = dd["valid"] & dd["dich_chuyen"].ne(0)
    dd["Adjusted_Score"] = np.where(sua, (dd["hp"] - dd["dich_chuyen"]).clip(0, 10), dd["hp"])
    dd["Adjusted_Score"] = dd["Adjusted_Score"].round(cfg.lam_tron)
    dd["duoc_hieu_chinh"] = sua
    return dd
