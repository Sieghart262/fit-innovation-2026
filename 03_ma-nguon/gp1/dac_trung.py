"""Đặc trưng thống kê của từng lớp học phần (giữ từ bản gốc, bổ sung vài chỉ số)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import cau_hinh as ch

TRAN = 9.5  # điểm ≥ 9,5 coi là "sát trần": lớp giỏi thật cũng dồn điểm ở đây

# Các chỉ số tính từ điểm hợp lệ. Khai báo sẵn (để trống) cho MỌI lớp, nhờ đó bảng kết quả
# luôn đủ cột kể cả khi file không có lớp nào có điểm hợp lệ – các bước sau không bị thiếu cột.
COT_CHI_SO = ["mean", "median", "std", "min", "max", "a_rate", "fail_rate", "skew", "mode_share",
              "mode_value", "ceiling_share", "n_ability", "ability_cov", "mean_ability", "rho_ability",
              "resid_mean", "kttx_mean", "exam_mean", "proc_exam_gap", "kttx_eq_exam"]


def dac_trung_lop(d: pd.DataFrame, b: float, cfg: ch.CauHinh) -> tuple[pd.DataFrame, dict]:
    """Tính các chỉ số mô tả cho mỗi lớp.

    Chỉ số chính: ĐTB, σ, tỷ lệ A, tỷ lệ trượt, độ lệch (skew), tỷ lệ SV cùng một mức
    điểm (mode_share), năng lực nền TB của lớp, tương quan điểm – năng lực nền,
    chênh KTTX − Thi, tỷ lệ SV có KTTX trùng y hệt Thi, resid_mean (SV ở lớp này
    cao/thấp hơn chính họ ở các lớp khác). Lớp không có điểm hợp lệ: các chỉ số để trống.
    Tham số:
        d: bảng lượt điểm đã có zc, ability, ability_raw, co_cau, du_lieu_chua_du.
        b: hệ số hồi quy zc theo ability (chỉ để báo cáo).
        cfg: cấu hình.
    Trả về:
        (bảng 1 dòng/lớp, dict {mã lớp: mảng điểm HP hợp lệ}).
    Vì sao cần: các chỉ số này là nguyên liệu cho bước so với mốc và tìm bằng chứng.
    """
    rows, diem = [], {}
    for cid, g in d.groupby("class_id", sort=False):
        v = g[g["valid"]]
        x = v["hp"].to_numpy(float)
        n = len(x)
        dau = g.iloc[0]
        r = dict(class_id=cid, year=dau["year"], year_start=dau["year_start"], sem=dau["sem"],
                 course=dau["course"], group=dau["group"], credits=dau["credits"],
                 is_project=bool(dau["is_project"]), is_ep=bool(dau["is_ep"]),
                 co_cau=dau["co_cau"], du_lieu_chua_du=bool(dau["du_lieu_chua_du"]),
                 ly_do_chua_du=dau["ly_do_chua_du"], ty_le_hp_thi=dau["ty_le_hp_thi"],
                 n_sv=int(g["student"].nunique()), n_rows=len(g), n=n,
                 n_absent=int(g["absent"].sum()), n_missing=int(g["hp"].isna().sum()))
        r["absent_rate"] = r["n_absent"] / max(n + r["n_absent"], 1)
        r.update(dict.fromkeys(COT_CHI_SO, np.nan), co_nang_luc=False)
        rows.append(r)
        if n == 0:
            continue
        diem[cid] = x
        std = float(np.std(x, ddof=1)) if n > 1 else np.nan
        r.update(mean=float(x.mean()), median=float(np.median(x)), std=std,
                 min=float(x.min()), max=float(x.max()),
                 a_rate=float((x >= cfg.diem_a).mean()),
                 fail_rate=float((x < cfg.diem_dat).mean()),
                 skew=float(stats.skew(x)) if n >= 3 and std > 0 else 0.0)
        tan_suat = pd.Series(np.round(x, 1)).value_counts(normalize=True)
        r["mode_share"], r["mode_value"] = float(tan_suat.iloc[0]), float(tan_suat.index[0])
        r["ceiling_share"] = float((x >= TRAN).mean())  # tỷ lệ điểm sát trần 10

        # Năng lực nền của các SV trong lớp
        ab = v["ability"].to_numpy(float)
        co_ab = ~np.isnan(ab)
        r["n_ability"] = int(co_ab.sum())
        r["ability_cov"] = r["n_ability"] / n
        r["mean_ability"] = float(ab[co_ab].mean()) if co_ab.any() else np.nan
        du_ab = r["n_ability"] >= cfg.min_sv_nang_luc and r["ability_cov"] >= cfg.min_phu_nang_luc
        r["co_nang_luc"] = bool(du_ab)
        if du_ab and std > 0 and np.std(ab[co_ab]) > 0:
            r["rho_ability"] = float(stats.spearmanr(x[co_ab], ab[co_ab])[0])
        else:
            r["rho_ability"] = np.nan
        # Phần chênh "do cách chấm": SV ở lớp này cao/thấp hơn chính họ ở các lớp khác bao nhiêu
        # (đơn vị: độ lệch chuẩn của môn). SV giỏi thật thì giỏi ở mọi lớp → chênh ≈ 0.
        co_raw = v["ability_raw"].notna() & v["zc"].notna()
        r["resid_mean"] = (float((v.loc[co_raw, "zc"] - v.loc[co_raw, "ability_raw"]).mean())
                           if du_ab and co_raw.any() else np.nan)

        # Điểm quá trình (GV tự chấm) so với điểm thi (2 GV chấm)
        pe = v[["kttx", "exam"]].dropna()
        if len(pe) > cfg.max_it_du_lieu:
            r["kttx_mean"] = float(pe["kttx"].mean())
            r["exam_mean"] = float(pe["exam"].mean())
            r["proc_exam_gap"] = r["kttx_mean"] - r["exam_mean"]
            r["kttx_eq_exam"] = float((pe["kttx"] - pe["exam"]).abs().lt(0.01).mean())
        else:
            r["kttx_mean"] = r["exam_mean"] = r["proc_exam_gap"] = r["kttx_eq_exam"] = np.nan
    return pd.DataFrame(rows), diem
