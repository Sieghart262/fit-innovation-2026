"""Kiểm chứng Giải pháp 1 bằng mô phỏng: cài bất thường biết trước rồi xem code có bắt đúng không.

Giữ ý tưởng của bản gốc (cài vào các lớp đang bình thường, chạy lại toàn bộ quy trình,
đo tỷ lệ phát hiện và báo động giả), bổ sung 2 kịch bản theo quyết định của đội:
    - "SV giỏi thật": SV của lớp giỏi hơn ở MỌI môn → lớp lệch lên nhưng KHÔNG được sửa điểm.
    - "Chưa nhập điểm quá trình": HP ≈ 0,5 × Thi → phải là INCOMPLETE_DATA, không phải ép điểm.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import cau_hinh as ch
from .quy_trinh import chay_quy_trinh

# kịch bản → (mô tả, các nhãn được coi là đúng, có mong đợi "được sửa điểm" không)
KICH_BAN = {
    "lam_phat": ("Nâng điểm HP cả lớp +1,5 (chấm dễ)", [ch.HIGH], True),
    "ep_diem": ("Hạ điểm HP cả lớp −2,0 (chấm khắt khe)", [ch.STEEP], True),
    "nen_diem": ("Nén điểm về ĐTB, σ còn 15% (cho điểm đồng loạt)", [ch.DIST], False),
    "hoan_vi": ("Hoán vị điểm trong lớp (mất tương quan năng lực)", [ch.DIST], False),
    # SV giỏi thật: lớp lệch lên nhưng không có bằng chứng → bình thường hoặc chỉ "cần xem xét"
    "gioi_that": ("SV của lớp giỏi thật: +1,5 ở MỌI lớp họ học", [ch.NORMAL, ch.REVIEW], False),
    "thieu_qua_trinh": ("Chưa nhập CC/KTTX, HP = 0,5 × Thi", [ch.CHUA_DU], False),
}


def cai_bat_thuong(d: pd.DataFrame, kieu: str, cac_lop, rng: np.random.Generator) -> pd.DataFrame:
    """Cài một kiểu bất thường vào các lớp được chọn.

    Tham số:
        d: bảng điểm tên cột ngắn (chưa làm sạch).
        kieu: một khóa của KICH_BAN.
        cac_lop: danh sách mã lớp bị cài.
        rng: bộ sinh số ngẫu nhiên.
    Trả về:
        Bản sao đã bị cài.
    Vì sao cần: biết trước đáp án thì mới đo được code bắt đúng hay sai.
    """
    d = d.copy()
    for cid in cac_lop:
        m = (d["class_id"] == cid) & d["hp"].notna() & (d["hp"] > 0)
        x = d.loc[m, "hp"].to_numpy(float)
        if kieu == "lam_phat":
            x = np.clip(x + 1.5, 0, 10)
        elif kieu == "ep_diem":
            x = np.clip(x - 2.0, 0.5, 10)
        elif kieu == "nen_diem":
            x = x.mean() + 0.15 * (x - x.mean())
        elif kieu == "hoan_vi":
            x = rng.permutation(x)
        elif kieu == "gioi_that":
            sv = d.loc[m, "student"].unique()
            m2 = d["student"].isin(sv) & d["hp"].notna() & (d["hp"] > 0)
            d.loc[m2, "hp"] = np.clip(d.loc[m2, "hp"] + 1.5, 0, 10).round(1)
            continue
        elif kieu == "thieu_qua_trinh":
            mm = d["class_id"] == cid
            d.loc[mm, ["cc", "kttx"]] = np.nan
            d.loc[mm & d["exam"].notna(), "hp"] = (0.5 * d.loc[mm & d["exam"].notna(), "exam"]).round(1)
            continue
        d.loc[m, "hp"] = np.round(x, 1)
    return d


def kiem_chung(d: pd.DataFrame, kq_goc: pd.DataFrame, cfg: ch.CauHinh, so_lop: int = 25) -> pd.DataFrame:
    """Chạy lần lượt các kịch bản và đo kết quả.

    Tham số:
        d: bảng điểm tên cột ngắn (chưa bị cài).
        kq_goc: kết quả Giải pháp 1 trên dữ liệu gốc (để chọn lớp đang bình thường).
        cfg: cấu hình.
        so_lop: số lớp bị cài mỗi kịch bản.
    Trả về:
        Bảng mỗi dòng một kịch bản: tỷ lệ đúng nhãn, tỷ lệ "được sửa điểm" (với kịch bản
        SV giỏi thật thì đây là tỷ lệ sửa OAN), Anomaly Score TB, tỷ lệ báo động giả ở các
        lớp không bị cài.
    Vì sao cần: chứng minh bằng số rằng code bắt được bất thường mà không sửa điểm oan.
    """
    rng = np.random.default_rng(cfg.random_state)
    ung_vien = kq_goc[(kq_goc["anomaly_type"] == ch.NORMAL) & (kq_goc["n"] >= 20)
                      & ~kq_goc["is_project"].astype(bool) & (kq_goc["co_cau"] == ch.CO_CAU_DU)]
    ung_vien = ung_vien["class_id"].to_numpy()
    dong = []
    for kieu, (mo_ta, mong_doi, duoc_sua) in KICH_BAN.items():
        chon = rng.choice(ung_vien, size=min(so_lop, len(ung_vien)), replace=False)
        kq, *_ = chay_quy_trinh(cai_bat_thuong(d, kieu, chon, rng), cfg)
        kq = kq.set_index("class_id")
        cai = kq.loc[chon]
        khac = kq.loc[[c for c in ung_vien if c not in set(chon)]]
        dong.append(dict(
            kich_ban=mo_ta, nhan_mong_doi=" hoặc ".join(mong_doi), so_lop_cai=len(chon),
            ty_le_dung_nhan=float(cai["anomaly_type"].isin(mong_doi).mean()),
            ty_le_gan_co=float(cai["anomaly_type"].isin(ch.NHAN_BAT_THUONG).mean()),
            ty_le_duoc_sua_diem=float(cai["du_dieu_kien_hieu_chinh"].astype(bool).mean()),
            mong_doi_sua_diem="Có" if duoc_sua else "Không",
            anomaly_score_tb=float(cai["anomaly_score"].mean()),
            ty_le_bao_dong_gia=float(khac["anomaly_type"].isin(ch.NHAN_BAT_THUONG).mean())))
        print(f"  [{kieu:15s}] đúng nhãn {dong[-1]['ty_le_dung_nhan']:.0%}, "
              f"được sửa điểm {dong[-1]['ty_le_duoc_sua_diem']:.0%}")
    return pd.DataFrame(dong)
