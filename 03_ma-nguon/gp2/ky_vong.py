"""Phương án C: điểm kỳ vọng của từng SV và cờ REVIEW_REQUIRED.

    Điểm kỳ vọng X̂ = TB môn (trong ±1 năm) + năng lực nền thô × SD môn
        năng lực nền thô = TB điểm chuẩn hóa của SV ở CÁC LỚP KHÁC.
    Khoảng tin cậy 95%: X̂ ± 1,96 × SE, với SE tính từ độ dao động điểm của chính SV giữa các
    môn và số lớp khác k (ít lớp → khoảng rộng hơn): SE = σ_w · √(1 + 1/k) · SD môn.
    REVIEW_REQUIRED khi điểm (sau phương án A) nằm ngoài khoảng VÀ lệch X̂ ≥ 1 điểm.

Chỉ GẮN CỜ và đưa ra điểm đề xuất (biên gần nhất của khoảng tin cậy) – KHÔNG tự đổi điểm,
vì ở mức từng SV chưa đủ bằng chứng (quyết định số 1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .cau_hinh import REVIEW_REQUIRED, CauHinhGP2


def diem_ky_vong(dd: pd.DataFrame, cfg: CauHinhGP2) -> tuple[pd.DataFrame, float]:
    """Thêm điểm kỳ vọng, khoảng tin cậy 95%, cờ REVIEW_REQUIRED và điểm đề xuất.

    Tham số:
        dd: bảng lượt điểm đã có Adjusted_Score, zc, ability_raw, so_lop_khac, sd_chuan.
        cfg: cấu hình.
    Trả về:
        (bảng có thêm diem_ky_vong, ky_vong_thap, ky_vong_cao, co_review, diem_de_xuat;
         σ_w – độ dao động điểm chuẩn hóa của một SV giữa các môn).
    Vì sao cần: phát hiện từng SV có điểm khác hẳn năng lực thể hiện ở các môn khác,
    kể cả khi cả lớp không bị coi là bất thường.
    """
    dd = dd.copy()
    co = (dd["zc"].notna() & dd["ability_raw"].notna()
          & (dd["so_lop_khac"] >= cfg.so_lop_khac_toi_thieu))
    he_so = 1 + 1 / dd["so_lop_khac"].where(co)
    e = (dd["zc"] - dd["ability_raw"]).where(co)
    # E[e²] = σ_w² · (1 + 1/k)  →  σ_w² = TB(e²) / TB(1 + 1/k)
    sigma_w = float(np.sqrt((e ** 2).mean() / he_so.mean())) if co.any() else np.nan

    tb_mon = dd["hp"] - dd["zc"] * dd["sd_chuan"]          # TB môn dùng khi chuẩn hóa lượt điểm này
    dd["diem_ky_vong"] = (tb_mon + dd["ability_raw"] * dd["sd_chuan"]).where(co).clip(0, 10)
    se = sigma_w * np.sqrt(he_so) * dd["sd_chuan"]
    dd["ky_vong_thap"] = (dd["diem_ky_vong"] - cfg.z_tin_cay * se).clip(0, 10)
    dd["ky_vong_cao"] = (dd["diem_ky_vong"] + cfg.z_tin_cay * se).clip(0, 10)

    x = dd["Adjusted_Score"]
    ngoai = (x > dd["ky_vong_cao"]) | (x < dd["ky_vong_thap"])
    dd["co_review"] = co & ngoai & ((x - dd["diem_ky_vong"]).abs() >= cfg.lech_toi_thieu_diem)
    dd["review_flag"] = np.where(dd["co_review"], REVIEW_REQUIRED, "")
    dd["diem_de_xuat"] = np.where(dd["co_review"],
                                  np.where(x > dd["ky_vong_cao"], dd["ky_vong_cao"], dd["ky_vong_thap"]),
                                  np.nan)
    for c in ["diem_ky_vong", "ky_vong_thap", "ky_vong_cao", "diem_de_xuat"]:
        dd[c] = dd[c].round(cfg.lam_tron)
    return dd, sigma_w
