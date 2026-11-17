"""Chấm điểm bất thường, gắn nhãn và viết lời giải thích cho từng lớp.

Theo quyết định số 1 của đội, một lớp chỉ mang nhãn HIGH_INFLATION / UNUSUALLY_STEEP
(và đủ điều kiện để Giải pháp 2 hiệu chỉnh điểm) khi có ĐỦ CẢ HAI:
    1. Lệch so với mốc (điểm lệch ≥ 0,5, tương đương |z| ≈ 2).
    2. Có bằng chứng độc lập rằng độ lệch do cách chấm (độ mạnh bằng chứng ≥ 0,5):
         E1 năng lực nền: điểm lớp vẫn lệch sau khi trừ phần do năng lực SV;
         E2 KTTX (GV tự chấm) lệch bất thường so với Thi (2 GV chấm), ĐÚNG CHIỀU với độ lệch
            và vượt mức thường của các lớp tương đương ít nhất 1,0 điểm;
         E3 phân phối biến dạng: σ quá nhỏ, KTTX trùng y hệt Thi, dồn điểm, mất tương quan với năng lực.
Lớp chỉ lệch mà không có bằng chứng → NEEDS_REVIEW (gắn cờ xem xét, không sửa điểm).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import cau_hinh as ch


def sigmoid(x: float, tam: float, doc: float) -> float:
    """Hàm chữ S đưa một chỉ số về khoảng 0–1 (bằng 0,5 khi x = tam).

    Tham số:
        x: giá trị chỉ số; tam: điểm giữa; doc: độ dốc.
    Trả về:
        Số trong (0, 1).
    Vì sao cần: biến các chỉ số khác đơn vị (z, tỷ lệ...) về cùng thang để cộng gộp.
    """
    return float(1.0 / (1.0 + np.exp(-doc * (x - tam))))


def kep01(x: float) -> float:
    """Kẹp một số vào đoạn [0, 1]; NaN coi là 0."""
    return 0.0 if x is None or np.isnan(x) else float(np.clip(x, 0.0, 1.0))


def hoac_nhieu(*p: float) -> float:
    """Gộp kiểu noisy-OR: 1 − Π(1 − p). Chỉ cần một dấu hiệu mạnh là kết quả mạnh."""
    return float(1 - np.prod([1 - kep01(x) for x in p]))


def _so(r: pd.Series, cot: str) -> float:
    """Lấy giá trị số của một cột, trả về NaN nếu không có."""
    v = r.get(cot, np.nan)
    return np.nan if v is None else float(v)


def diem_quy_tac(r: pd.Series, cfg: ch.CauHinh) -> dict:
    """Tính điểm lệch, độ mạnh bằng chứng và 3 điểm thành phần cho một lớp.

    Tham số:
        r: một dòng của bảng so sánh (lớp đã có mốc).
        cfg: cấu hình.
    Trả về:
        dict gồm dev_up/dev_down (điểm lệch lên/xuống), e_* (từng bằng chứng),
        E_up/E_down (gộp bằng chứng), S_HIGH_INFLATION, S_UNUSUALLY_STEEP,
        S_SUSPICIOUS_DISTRIBUTION.
    Vì sao cần: tách rõ "lệch" và "bằng chứng" để thực hiện đúng quyết định số 1.
    """
    z = _so(r, "z_mean")
    z = 0.0 if np.isnan(z) else z
    q = _so(r, "q_value")
    cong = 1.0 if (not np.isnan(q) and q < cfg.fdr_alpha) else 0.5  # chưa có ý nghĩa thống kê → giảm nửa

    # --- Bước 1: lệch so với mốc (không dùng ngưỡng cố định 60%, chỉ dùng p-chart) ---
    s_tb_len = sigmoid(z, cfg.z_lech, 2.0) * cong if z > 0 else 0.0
    s_tb_xuong = sigmoid(-z, cfg.z_lech, 2.0) * cong if z < 0 else 0.0
    s_a = sigmoid(_so(r, "z_a"), 3.0, 1.5) if r["a_rate"] > r["ref_a_rate"] else 0.0
    s_f = (sigmoid(_so(r, "z_fail"), 3.0, 1.5)
           if r["fail_rate"] > r["ref_fail_rate"] and r["fail_rate"] >= 0.10 else 0.0)
    dev_up, dev_down = max(s_tb_len, s_a), max(s_tb_xuong, s_f)

    # --- Bước 2: bằng chứng độc lập ---
    # E1: năng lực nền – chỉ khi lớp có đủ SV có năng lực nền VÀ mốc là cùng môn.
    # Khi so với môn khác cùng nhóm, "SV bình thường ở môn khác nhưng điểm môn này thấp"
    # có thể chỉ vì môn này khó hơn thật → không dùng làm bằng chứng về cách chấm.
    z_adj = _so(r, "z_adj")
    e_nl_up = e_nl_down = 0.0
    if bool(r.get("co_nang_luc", False)) and not np.isnan(z_adj) and r.get("ref_level") == "Cùng môn":
        e_nl_up = sigmoid(z_adj, cfg.z_lech, 2.0) if z_adj > 0 else 0.0
        e_nl_down = sigmoid(-z_adj, cfg.z_lech, 2.0) if z_adj < 0 else 0.0
    # E2: KTTX (GV tự chấm) lệch bất thường so với Thi (2 GV chấm) – CHỈ tính khi ĐÚNG CHIỀU.
    # Thi thấp hơn KTTX ở mức các lớp tương đương cũng vậy là bình thường (đã nằm trong mốc).
    #   Nghi chấm dễ  (lệch lên):   Thi thấp hơn KTTX NHIỀU HƠN mức thường ≥ ngưỡng → GV cho điểm quá trình rộng tay.
    #   Nghi ép điểm (lệch xuống): KTTX thấp hơn mức thường so với Thi ≥ ngưỡng → GV chấm quá trình chặt hơn hẳn.
    # Lệch ngược chiều (vd lớp điểm cao nhưng Thi cao hơn hẳn KTTX) KHÔNG phải bằng chứng về cách chấm của GV.
    z_gap, gap_diff = _so(r, "z_gap"), _so(r, "gap_diff")
    e_gap_up = e_gap_down = 0.0
    if not np.isnan(z_gap) and not np.isnan(gap_diff) and abs(gap_diff) >= cfg.chenh_kttx_thi_toi_thieu:
        if gap_diff > 0:
            e_gap_up = sigmoid(abs(z_gap), 2.5, 1.5)
        else:
            e_gap_down = sigmoid(abs(z_gap), 2.5, 1.5)
    e_gap = max(e_gap_up, e_gap_down)  # độ bất thường của chênh lệch, không kể chiều (chỉ để mô tả)
    # E3: phân phối biến dạng
    std, ratio = _so(r, "std"), _so(r, "sigma_ratio")
    s_sigma = kep01((cfg.sigma_ti_le_thap - ratio) / 0.40) if not np.isnan(ratio) else 0.0
    if not np.isnan(std) and std < cfg.sigma_tuyet_doi and not np.isnan(ratio) and ratio < 0.8:
        s_sigma = 1.0  # σ → 0 trong khi mốc không thấp như vậy
    eq, eq_moc = _so(r, "kttx_eq_exam"), _so(r, "ref_kttx_eq_exam")
    s_copy = kep01((eq - max(0.3, (0 if np.isnan(eq_moc) else eq_moc) + 0.2)) / 0.4) if not np.isnan(eq) else 0.0
    rho = _so(r, "rho_ability")
    s_corr = 0.0
    if not np.isnan(rho):
        nguong = min(cfg.rho_thap, _so(r, "ref_rho") - 0.25)
        s_corr = kep01((nguong - rho) / 0.30)
    # Dồn điểm và hình dạng phân phối: bỏ qua khi điểm dồn ở sát trần 10 – SV giỏi thật
    # cũng bị "chặn trên" ở 10 nên phân phối co lại, không phải dấu hiệu cách chấm.
    s_heap = kep01((_so(r, "mode_share") - 0.30) / 0.40) if _so(r, "mode_value") < 9.5 else 0.0
    s_shape = (kep01((-np.log10(max(_so(r, "ks_shape_p"), 1e-300)) - 2.0) / 6.0)
               if _so(r, "ceiling_share") < 0.3 else 0.0)
    e_dist = hoac_nhieu(s_sigma, 0.9 * s_copy, 0.8 * s_corr, 0.6 * s_heap, 0.5 * s_shape)

    E_up = hoac_nhieu(e_nl_up, e_gap_up, e_dist)
    E_down = hoac_nhieu(e_nl_down, e_gap_down, e_dist)
    return dict(dev_up=dev_up, dev_down=dev_down, s_mean_up=s_tb_len, s_mean_down=s_tb_xuong,
                s_a_rate=s_a, s_fail_rate=s_f, e_ability_up=e_nl_up, e_ability_down=e_nl_down,
                e_gap=e_gap, e_gap_up=e_gap_up, e_gap_down=e_gap_down, s_sigma=s_sigma, s_copy=s_copy, s_corr=s_corr, s_heap=s_heap,
                s_shape=s_shape, e_dist=e_dist, E_up=E_up, E_down=E_down,
                S_HIGH_INFLATION=dev_up * E_up, S_UNUSUALLY_STEEP=dev_down * E_down,
                S_SUSPICIOUS_DISTRIBUTION=hoac_nhieu(e_dist, 0.5 * e_gap))


DAC_TRUNG_ML = ["z_mean", "z_adj", "log_sigma_ratio", "z_a", "z_fail", "rho_ability",
                "mode_share", "z_gap", "skew", "ks_shape_stat", "kttx_eq_exam"]


def diem_ml(el: pd.DataFrame, cfg: ch.CauHinh) -> np.ndarray:
    """Điểm bất thường đa biến bằng Isolation Forest (học máy không giám sát), thang 0–1.

    Tham số:
        el: các lớp được chấm (có đủ cột DAC_TRUNG_ML).
        cfg: cấu hình.
    Trả về:
        Mảng điểm 0–1 (0 = giống số đông, 1 = khác nhất).
    Vì sao cần: kiểm tra chéo – lớp mà cả quy tắc thống kê lẫn học máy cùng nghi thì càng chắc.
    """
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import RobustScaler

    if len(el) < 10:
        return np.zeros(len(el))
    X = el.assign(log_sigma_ratio=np.log(el["sigma_ratio"].clip(lower=0.05)))[DAC_TRUNG_ML].astype(float)
    X["rho_ability"] = X["rho_ability"].fillna(el["ref_rho"])
    X[["z_gap", "kttx_eq_exam"]] = X[["z_gap", "kttx_eq_exam"]].fillna(0)
    X = X.fillna(X.median()).fillna(0).clip(-10, 10)
    Xs = RobustScaler().fit_transform(X)
    iso = IsolationForest(n_estimators=500, random_state=cfg.random_state).fit(Xs)
    tho = -iso.score_samples(Xs)
    giua, dinh = np.median(tho), tho.max()
    return np.clip((tho - giua) / max(dinh - giua, 1e-9), 0, 1)


def muc_do(s: float) -> str:
    """Đổi Anomaly Score thành mức độ dễ đọc."""
    if np.isnan(s):
        return "–"
    if s >= 0.70:
        return "Rất cao"
    if s >= 0.50:
        return "Cao"
    if s >= 0.30:
        return "Trung bình"
    return "Thấp"


def giai_thich(r: pd.Series, cfg: ch.CauHinh) -> str:
    """Viết lời giải thích tiếng Việt cho một lớp: lệch thế nào, bằng chứng gì, vì sao gắn nhãn.

    Tham số:
        r: một dòng kết quả đã chấm.
        cfg: cấu hình.
    Trả về:
        Chuỗi giải thích (các ý ngăn bằng "; ").
    Vì sao cần: đề yêu cầu giải thích được (Explainable) – phòng khảo thí cần biết lý do.
    """
    nhan = r["anomaly_type"]
    if nhan == ch.CHUA_DU:
        return f"Dữ liệu chưa đầy đủ: {r['ly_do_chua_du']}"
    if nhan == ch.IT_DU_LIEU:
        return f"Chỉ có {int(r['n'])} điểm hợp lệ (≤ {cfg.max_it_du_lieu}) → không gắn cờ, giữ nguyên điểm"
    if nhan == ch.KHONG_MOC:
        return "Không đủ lớp cùng môn/nhóm môn, cùng giai đoạn, cùng cơ cấu điểm để so sánh"
    y = []
    if r["dev_up"] >= cfg.lech_toi_thieu or r["dev_down"] >= cfg.lech_toi_thieu:
        y.append(f"ĐTB {r['mean']:.2f} so với {r['ref_mean']:.2f} ({r['ref_level'].lower()}); "
                 f"z={r['z_mean']:+.1f}, q={r['q_value']:.1e}")
    if r["s_a_rate"] > 0.3:
        y.append(f"Tỷ lệ A {r['a_rate']:.0%} (mốc {r['ref_a_rate']:.0%}, giới hạn kiểm soát {r['a_ucl']:.0%})")
    if r["s_fail_rate"] > 0.3:
        y.append(f"Tỷ lệ trượt {r['fail_rate']:.0%} (mốc {r['ref_fail_rate']:.0%}, giới hạn {r['fail_ucl']:.0%})")
    # Bằng chứng
    lech_len = r["dev_up"] >= r["dev_down"]  # chiều lệch chính của lớp
    if (r["e_ability_up"] if lech_len else r["e_ability_down"]) > 0.3:
        y.append(f"[Bằng chứng] SV ở lớp này {'cao' if lech_len else 'thấp'} hơn hẳn so với chính họ "
                 f"ở các lớp khác (z={r['z_adj']:+.1f}, {int(r['n_ability'])} SV có năng lực nền)")
    if r["e_gap"] > 0.3:
        chenh = f"KTTX − Thi = {r['proc_exam_gap']:+.1f} điểm, mức thường của mốc {r['ref_gap']:+.1f} (z={r['z_gap']:+.1f})"
        if (r["e_gap_up"] if lech_len else r["e_gap_down"]) > 0.3:
            y.append(f"[Bằng chứng] {chenh}: điểm quá trình được chấm "
                     f"{'rộng tay' if lech_len else 'chặt'} hơn hẳn các lớp tương đương")
        else:
            y.append(f"{chenh} – ngược chiều với độ lệch của lớp nên không tính là bằng chứng")
    if r["s_sigma"] > 0.3:
        y.append(f"[Bằng chứng] σ={r['std']:.2f}, chỉ bằng {r['sigma_ratio']:.0%} σ mốc")
    if r["s_copy"] > 0.3:
        y.append(f"[Bằng chứng] {r['kttx_eq_exam']:.0%} SV có KTTX trùng y hệt Thi")
    if r["s_corr"] > 0.3:
        y.append(f"[Bằng chứng] Điểm gần như không tương quan với năng lực nền (ρ={r['rho_ability']:.2f}, mốc {r['ref_rho']:.2f})")
    if r["s_heap"] > 0.3:
        y.append(f"[Bằng chứng] {r['mode_share']:.0%} SV cùng một mức điểm")
    if r["s_shape"] > 0.3:
        y.append(f"[Bằng chứng] Hình dạng phân phối khác mốc (KS p={r['ks_shape_p']:.1e})")
    if nhan == ch.REVIEW:
        if str(r["ref_level"]).startswith("Cùng nhóm môn"):
            y.append("So với môn khác cùng nhóm: chênh lệch có thể do độ khó môn; chưa thấy dấu hiệu "
                     "KTTX−Thi hay phân phối bất thường → chỉ xem xét, không sửa điểm")
        else:
            y.append("Chưa có bằng chứng độc lập rằng độ lệch do cách chấm (có thể do SV giỏi/yếu thật) "
                     "→ chỉ xem xét, không sửa điểm")
    if r["ml_score"] >= cfg.nguong_ml_cao:
        y.append("Isolation Forest cũng đánh giá lớp này khác thường")
    return "; ".join(y)


def cham_lop(kq: pd.DataFrame, cfg: ch.CauHinh) -> pd.DataFrame:
    """Chấm điểm và gắn nhãn cho mọi lớp, rồi xếp hạng.

    Quy tắc nhãn (theo thứ tự ưu tiên):
        INCOMPLETE_DATA → INSUFFICIENT_DATA → NO_REFERENCE → nhãn bất thường có điểm
        thành phần lớn nhất trong các nhãn đủ điều kiện → NEEDS_REVIEW → NORMAL.
        HIGH_INFLATION cần lệch lên + bằng chứng; UNUSUALLY_STEEP cần lệch xuống + bằng chứng;
        SUSPICIOUS_DISTRIBUTION cần điểm phân phối biến dạng ≥ 0,5.
    Anomaly Score = 0,8 × điểm quy tắc + 0,2 × điểm Isolation Forest (giữ từ bản gốc).
    Tham số:
        kq: bảng từ so_sanh_moc().
        cfg: cấu hình.
    Trả về:
        Bảng đủ mọi lớp, thêm anomaly_score, anomaly_type, secondary_flags, severity,
        du_dieu_kien_hieu_chinh, huong_hieu_chinh, explanation, rank.
    Vì sao cần: đây là đầu ra bắt buộc của Giải pháp 1 và đầu vào cho Giải pháp 2.
    """
    kq = kq.copy()
    co_moc = kq["duoc_cham"] & kq["z_mean"].notna()
    el = kq[co_moc].copy()
    if len(el):
        el = pd.concat([el, el.apply(lambda r: pd.Series(diem_quy_tac(r, cfg)), axis=1)], axis=1)
        S = el[[f"S_{l}" for l in ch.NHAN_BAT_THUONG]].to_numpy()
        sap = np.sort(S, axis=1)
        el["rule_score"] = 1 - (1 - sap[:, -1]) * (1 - 0.3 * sap[:, -2])
        el["ml_score"] = diem_ml(el, cfg)
        el["anomaly_score"] = (cfg.w_quy_tac * el["rule_score"] + cfg.w_ml * el["ml_score"]).round(4)

        dk = {ch.HIGH: (el["dev_up"] >= cfg.lech_toi_thieu) & (el["E_up"] >= cfg.bang_chung_toi_thieu),
              ch.STEEP: (el["dev_down"] >= cfg.lech_toi_thieu) & (el["E_down"] >= cfg.bang_chung_toi_thieu),
              ch.DIST: el["S_SUSPICIOUS_DISTRIBUTION"] >= cfg.bang_chung_toi_thieu}
        D = np.column_stack([dk[l].to_numpy() for l in ch.NHAN_BAT_THUONG])
        S_dk = np.where(D, S, -1.0)
        chinh = np.array(ch.NHAN_BAT_THUONG)[S_dk.argmax(axis=1)]
        lech = (el["dev_up"] >= cfg.lech_toi_thieu) | (el["dev_down"] >= cfg.lech_toi_thieu)
        el["anomaly_type"] = np.where(D.any(axis=1), chinh, np.where(lech, ch.REVIEW, ch.NORMAL))
        el["secondary_flags"] = [", ".join(l for l, ok in zip(ch.NHAN_BAT_THUONG, hang) if ok and l != t)
                                 for hang, t in zip(D, el["anomaly_type"])]
        # Giải pháp 2 chỉ hiệu chỉnh lớp có lệch + bằng chứng (HIGH hoặc STEEP, kể cả là nhãn phụ)
        el["du_dieu_kien_hieu_chinh"] = dk[ch.HIGH] | dk[ch.STEEP]
        el["huong_hieu_chinh"] = np.select(
            [dk[ch.HIGH] & (el["S_HIGH_INFLATION"] >= el["S_UNUSUALLY_STEEP"]), dk[ch.STEEP], dk[ch.HIGH]],
            ["Giảm", "Tăng", "Giảm"], default="")

    con_lai = kq[~co_moc].copy()
    con_lai["anomaly_type"] = np.select(
        [con_lai["du_lieu_chua_du"], con_lai["n"] <= cfg.max_it_du_lieu],
        [ch.CHUA_DU, ch.IT_DU_LIEU], default=ch.KHONG_MOC)
    con_lai["du_dieu_kien_hieu_chinh"] = False
    con_lai["huong_hieu_chinh"] = ""

    ra = pd.concat([el, con_lai], ignore_index=True)
    for cot in ["anomaly_score", "ml_score", "dev_up", "dev_down", "e_ability_up", "e_ability_down",
                "e_gap", "e_gap_up", "e_gap_down", "s_sigma", "s_copy", "s_corr", "s_heap", "s_shape", "s_a_rate", "s_fail_rate"]:
        if cot not in ra:
            ra[cot] = np.nan
    ra["secondary_flags"] = ra.get("secondary_flags", pd.Series("", index=ra.index)).fillna("")
    ra["severity"] = ra["anomaly_score"].apply(muc_do)
    ra["y_nghia_nhan"] = ra["anomaly_type"].map(ch.Y_NGHIA_NHAN)
    ra["ca_hai_cung_nghi"] = ra["anomaly_type"].isin(ch.NHAN_BAT_THUONG) & (ra["ml_score"] >= cfg.nguong_ml_cao)
    ra["explanation"] = ra.apply(lambda r: giai_thich(r, cfg), axis=1)
    ra = ra.sort_values("anomaly_score", ascending=False, na_position="last").reset_index(drop=True)
    ra["rank"] = np.where(ra["anomaly_score"].notna(), np.arange(1, len(ra) + 1), np.nan)
    return ra
