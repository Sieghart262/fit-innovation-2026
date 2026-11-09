"""Năng lực nền của sinh viên (leave-one-class-out, có co rút).

Ý tưởng (giữ từ bản gốc của thành viên nhóm):
    1. Chuẩn hóa điểm mỗi lượt theo môn: zc = (HP − TB môn) / SD môn → bỏ chênh lệch độ khó môn.
       Bản này chuẩn hóa theo môn TRONG CỬA SỔ ±1 năm và cùng cơ cấu điểm, vì điểm tăng
       dần qua các năm và lớp "chỉ có Thi" có mặt bằng khác.
    2. Năng lực nền của SV khi xét lớp c = Σ zc ở CÁC LỚP KHÁC / (số lớp khác + k):
       không dùng điểm của chính lớp c để đánh giá lớp c; k co rút về 0 khi SV có ít lớp.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import cau_hinh as ch

SD_SAN = 0.3          # SD môn tối thiểu (tránh chia cho số quá nhỏ)
MIN_LUOT_CHUAN = 10   # cần ≥ 10 lượt điểm trong cửa sổ, nếu không thì chuẩn hóa theo cả môn


def _thong_ke_cua_so(d: pd.DataFrame, cfg: ch.CauHinh) -> pd.DataFrame:
    """Tính TB và SD điểm HP theo (môn, cơ cấu, năm) trong cửa sổ ±cua_so_nam năm.

    Tham số:
        d: các lượt điểm dùng để chuẩn hóa (cột course, co_cau, year_start, hp).
        cfg: cấu hình.
    Trả về:
        Bảng (course, co_cau, year_start) → n_cs, tb_cs, sd_cs.
    Vì sao cần: tính bằng tổng (n, Σx, Σx²) cộng dồn qua các năm lân cận nên không cần
    vòng lặp theo từng lượt điểm – chạy nhanh với dữ liệu > 100.000 dòng.
    """
    khoa = ["course", "co_cau", "year_start"]
    g = d.assign(x2=d["hp"] ** 2).groupby(khoa).agg(n=("hp", "size"), s=("hp", "sum"),
                                                    s2=("x2", "sum")).reset_index()
    dich = [g.assign(year_start=g["year_start"] + k) for k in range(-cfg.cua_so_nam, cfg.cua_so_nam + 1)]
    cs = pd.concat(dich).groupby(khoa)[["n", "s", "s2"]].sum().reset_index()
    cs["tb_cs"] = cs["s"] / cs["n"]
    var = (cs["s2"] - cs["n"] * cs["tb_cs"] ** 2) / (cs["n"] - 1)
    cs["sd_cs"] = np.sqrt(var.clip(lower=0))
    return cs.rename(columns={"n": "n_cs"})[khoa + ["n_cs", "tb_cs", "sd_cs"]]


def tinh_nang_luc(d: pd.DataFrame, cfg: ch.CauHinh) -> tuple[pd.DataFrame, float]:
    """Thêm cột zc (điểm chuẩn hóa), sd_chuan và ability (năng lực nền) cho từng lượt điểm.

    Tham số:
        d: bảng đã qua lam_sach() và đã gắn co_cau, du_lieu_chua_du của lớp.
        cfg: cấu hình.
    Trả về:
        (bảng có thêm zc, sd_chuan, ability; hệ số b của hồi quy zc theo ability).
        b cho biết năng lực nền giải thích điểm môn mạnh tới đâu (b ≈ 1: rất mạnh).
    Vì sao cần: là bằng chứng độc lập E1 – nếu SV của lớp bình thường ở các môn khác
    mà điểm lớp này cao/thấp vọt thì độ lệch do cách chấm, không do SV.
    """
    d = d.copy()
    base = d["valid"] & ~d["is_project"] & ~d["du_lieu_chua_du"]

    cs = _thong_ke_cua_so(d[base], cfg)
    d = d.merge(cs, on=["course", "co_cau", "year_start"], how="left")
    ca_mon = d[base].groupby("course")["hp"].agg(tb_mon="mean", sd_mon="std")
    d = d.join(ca_mon, on="course")
    du_luot = d["n_cs"] >= MIN_LUOT_CHUAN
    d["tb_chuan"] = np.where(du_luot, d["tb_cs"], d["tb_mon"])
    d["sd_chuan"] = np.where(du_luot, d["sd_cs"], d["sd_mon"])
    d["sd_chuan"] = d["sd_chuan"].fillna(1.0).clip(lower=SD_SAN)
    d["zc"] = np.where(base, (d["hp"] - d["tb_chuan"]) / d["sd_chuan"], np.nan)

    # Năng lực nền = TB zc ở các lớp KHÁC (trừ phần của chính lớp đang xét)
    tong = d[base].groupby("student")["zc"].agg(_tong="sum", _dem="count")
    d = d.join(tong, on="student")
    d[["_tong", "_dem"]] = d[["_tong", "_dem"]].fillna(0)
    rieng = np.where(base, d["zc"].fillna(0), 0.0)
    tong_khac = d["_tong"] - rieng
    dem_khac = d["_dem"] - base.astype(int)
    du_lop = dem_khac >= cfg.so_lop_khac_nang_luc
    # ability: có co rút (dùng cho tương quan và mô tả); ability_raw: TB thô ở các lớp khác,
    # dùng cho bằng chứng E1 "điểm ở lớp này so với chính SV đó ở các lớp khác" – co rút ở đây
    # sẽ trừ thiếu phần giỏi/yếu thật của SV và làm lớp có SV giỏi thật bị nghi oan.
    d["ability"] = np.where(du_lop, tong_khac / (dem_khac + cfg.co_rut_nang_luc), np.nan)
    d["ability_raw"] = np.where(du_lop, tong_khac / dem_khac.where(dem_khac > 0), np.nan)

    m = base & d["ability"].notna()
    b = float(np.polyfit(d.loc[m, "ability"], d.loc[m, "zc"], 1)[0]) if m.sum() > 30 else 0.0
    bo = ["n_cs", "tb_cs", "sd_cs", "tb_mon", "sd_mon", "tb_chuan", "_tong", "_dem"]
    return d.drop(columns=bo), b
