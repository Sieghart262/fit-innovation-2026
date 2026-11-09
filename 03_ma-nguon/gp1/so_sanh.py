"""So sánh mỗi lớp với mốc (Bước 1: tìm lớp lệch) và tính các chỉ số cho bằng chứng.

Mốc so sánh (quyết định của đội):
    - Chỉ so với lớp cùng loại (đồ án với đồ án), cùng cơ cấu điểm, trong ±1 năm học.
    - Mốc chính: các lớp khác CÙNG MÔN (≥ 3 lớp).
    - Mốc phụ: các lớp của môn khác CÙNG NHÓM MÔN – dùng khi môn có quá ít lớp,
      hoặc khi cả môn lệch so với nhóm môn (môn dễ/khó ở mọi lớp).
    - KHÔNG so với môn khác nhóm. Không đủ cả hai mốc → NO_REFERENCE.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import cau_hinh as ch


def robust_z(gia_tri: float, moc, san: float = 0.2) -> float:
    """Z-score bền vững: (x − trung vị) / (1,4826 · MAD), có sàn để tránh chia cho ~0.

    Tham số:
        gia_tri: giá trị của lớp đang xét.
        moc: các giá trị của nhóm mốc.
        san: mẫu số tối thiểu.
    Trả về:
        z (NaN nếu mốc có < 2 giá trị hoặc giá trị bị thiếu).
    Vì sao cần: trung vị/MAD ít bị kéo bởi vài lớp quá lạ trong mốc hơn TB/SD.
    """
    moc = np.asarray(moc, dtype=float)
    moc = moc[~np.isnan(moc)]
    if len(moc) < 2 or gia_tri is None or np.isnan(gia_tri):
        return np.nan
    trung_vi = np.median(moc)
    mad = 1.4826 * np.median(np.abs(moc - trung_vi))
    thang = mad if mad > 0 else np.std(moc, ddof=1)
    return float((gia_tri - trung_vi) / max(thang, san))


def bh_fdr(p_values) -> np.ndarray:
    """Hiệu chỉnh Benjamini–Hochberg cho nhiều kiểm định cùng lúc, trả về q-value.

    Tham số:
        p_values: dãy p-value (NaN được giữ nguyên).
    Trả về:
        Mảng q-value.
    Vì sao cần: kiểm định hàng trăm lớp cùng lúc thì chắc chắn có lớp "ý nghĩa" do
    ngẫu nhiên; FDR kiểm soát tỷ lệ báo nhầm trong số lớp bị gắn cờ.
    """
    p = np.asarray(p_values, dtype=float)
    q = np.full_like(p, np.nan)
    co = ~np.isnan(p)
    pv = p[co]
    m = len(pv)
    if m == 0:
        return q
    thu_tu = np.argsort(pv)
    xep = pv[thu_tu] * m / np.arange(1, m + 1)
    xep = np.minimum.accumulate(xep[::-1])[::-1]
    ra = np.empty(m)
    ra[thu_tu] = np.clip(xep, 0, 1)
    q[co] = ra
    return q


def so_sanh_moc(lop: pd.DataFrame, diem: dict, cfg: ch.CauHinh) -> tuple[pd.DataFrame, dict]:
    """So từng lớp với mốc và tính độ lệch, các chỉ số phân tán, p-chart, KS, KTTX − Thi.

    Tham số:
        lop: bảng đặc trưng lớp (dac_trung_lop).
        diem: {mã lớp: mảng điểm HP hợp lệ}.
        cfg: cấu hình.
    Trả về:
        (bảng lớp có thêm các cột so sánh, {mã lớp: danh sách mã lớp mốc}).
        Cột duoc_cham = True nếu lớp đủ dữ liệu để chấm (không thiếu dữ liệu, > 5 điểm).
    Vì sao cần: Bước 1 của quyết định số 1 – tìm lớp lệch so với lớp tương đương.
    """
    lop = lop.copy()
    lop["duoc_cham"] = ~lop["du_lieu_chua_du"] & (lop["n"] > cfg.max_it_du_lieu)
    lop["loai_ss"] = np.where(lop["is_project"], ch.SS_DO_AN, ch.SS_THUONG)
    el = lop[lop["duoc_cham"]].set_index("class_id")
    rho_chung = el["rho_ability"].median()

    ra, ds_moc = [], {}
    for cid, r in el.iterrows():
        ung_vien = el[(el["loai_ss"] == r["loai_ss"]) & (el["co_cau"] == r["co_cau"])
                      & ((el["year_start"] - r["year_start"]).abs() <= cfg.cua_so_nam)
                      & (el.index != cid)]
        moc_mon = ung_vien[ung_vien["course"] == r["course"]]
        moc_nhom = ung_vien[(ung_vien["group"] == r["group"]) & (ung_vien["course"] != r["course"])]

        # Cả môn có lệch so với nhóm môn không? (TB các lớp của môn, kể cả lớp này)
        z_mon = np.nan
        if len(moc_nhom) >= cfg.min_lop_moc:
            tb_mon = pd.concat([moc_mon["mean"], pd.Series([r["mean"]])]).mean()
            z_mon = robust_z(tb_mon, moc_nhom["mean"])
        mon_lech = not np.isnan(z_mon) and abs(z_mon) >= cfg.z_lech

        # Lớp có lệch so với chính các lớp khác cùng môn không?
        z_trong_mon = robust_z(r["mean"], moc_mon["mean"]) if len(moc_mon) >= cfg.min_lop_moc else np.nan
        lech_trong_mon = not np.isnan(z_trong_mon) and abs(z_trong_mon) >= cfg.z_lech

        o = dict(class_id=cid, z_course_level=z_mon)
        # Ưu tiên mốc cùng môn; chỉ chuyển sang nhóm môn khi môn quá ít lớp, hoặc khi cả môn
        # lệch so với nhóm môn mà lớp này lại không lệch so với các lớp cùng môn.
        if len(moc_mon) >= cfg.min_lop_moc and (not mon_lech or lech_trong_mon):
            moc, o["ref_level"] = moc_mon, "Cùng môn"
        elif len(moc_nhom) >= cfg.min_lop_moc:
            moc = moc_nhom
            o["ref_level"] = "Cùng nhóm môn (cả môn lệch)" if mon_lech else "Cùng nhóm môn"
        else:
            o["ref_level"] = "Không đủ mốc"
            o["ref_n_classes"] = len(moc_mon)
            ra.append(o)
            continue

        ds_moc[cid] = list(moc.index)
        x = diem[cid]
        n = len(x)
        gop = np.concatenate([diem[c] for c in moc.index])
        o.update(ref_n_classes=len(moc), ref_mean=float(gop.mean()))

        # (a) Lệch ĐTB: robust z giữa các lớp, Welch t-test;
        #     z_adj: phần chênh "SV ở lớp này so với chính họ ở lớp khác" so với các lớp mốc
        o["z_mean"] = robust_z(r["mean"], moc["mean"])
        o["z_adj"] = robust_z(r["resid_mean"], moc["resid_mean"])
        if (r["std"] > 0 or gop.std() > 0) and n > 1:
            o["p_value"] = float(stats.ttest_ind(x, gop, equal_var=False).pvalue)
        else:
            o["p_value"] = 1.0
        o["cohen_d"] = (r["mean"] - gop.mean()) / max(gop.std(ddof=1), 1e-6)

        # (b) Độ phân tán so với trung vị σ của mốc
        sd_moc = float(np.nanmedian(moc["std"]))
        o["ref_std"] = sd_moc
        o["sigma_ratio"] = r["std"] / sd_moc if sd_moc > 0 else np.nan

        # (c) Biểu đồ kiểm soát p-chart cho tỷ lệ A và tỷ lệ trượt (ngưỡng thống kê, không cố định 60%)
        pA = float((gop >= cfg.diem_a).mean())
        seA = np.sqrt(max(pA * (1 - pA), 1e-4) / n)
        o["ref_a_rate"], o["a_ucl"] = pA, min(1.0, pA + 3 * seA)
        o["z_a"] = (r["a_rate"] - pA) / seA
        pF = float((gop < cfg.diem_dat).mean())
        seF = np.sqrt(max(pF * (1 - pF), 1e-4) / n)
        o["ref_fail_rate"], o["fail_ucl"] = pF, min(1.0, pF + 3 * seF)
        o["z_fail"] = (r["fail_rate"] - pF) / seF

        # (d) Tương quan với năng lực nền của mốc
        rr = moc["rho_ability"].dropna()
        o["ref_rho"] = float(rr.median()) if len(rr) >= 3 else float(rho_chung)

        # (e) Hình dạng phân phối (đã khử trung bình) – kiểm định KS 2 mẫu
        ks = stats.ks_2samp(x - x.mean(), gop - gop.mean())
        o["ks_shape_stat"], o["ks_shape_p"] = float(ks.statistic), float(ks.pvalue)

        # (f) Chênh KTTX − Thi và tỷ lệ KTTX trùng Thi so với mốc
        o["z_gap"] = robust_z(r["proc_exam_gap"], moc["proc_exam_gap"], san=0.3)
        gap_moc = moc["proc_exam_gap"].dropna()
        o["ref_gap"] = float(gap_moc.median()) if len(gap_moc) else np.nan
        o["gap_diff"] = r["proc_exam_gap"] - o["ref_gap"]
        eq_moc = moc["kttx_eq_exam"].dropna()
        o["ref_kttx_eq_exam"] = float(eq_moc.median()) if len(eq_moc) else np.nan
        ra.append(o)

    kq = lop.merge(pd.DataFrame(ra, columns=None if ra else ["class_id"]), on="class_id", how="left")
    kq["q_value"] = bh_fdr(kq["p_value"]) if "p_value" in kq else np.nan
    return kq, ds_moc
