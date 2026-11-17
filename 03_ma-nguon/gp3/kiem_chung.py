"""Kiểm chứng Giải pháp 3 bằng mô phỏng: SV học lớp bị cài bất thường có được đưa về đúng mức không.

So với kết quả trên dữ liệu gốc (chưa cài):
    - Chấm dễ: GPA danh nghĩa của SV bị thổi phồng → TCI phải gỡ được phần thổi phồng,
      SV bị đẩy lên mức cao hơn phải được đưa về mức cũ.
    - Chấm khắt khe: ngược lại.
    - SV giỏi thật: điểm tăng ở MỌI môn là thật → TCI phải giữ phần tăng, không kéo SV xuống.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from gp1 import cau_hinh as ch1
from gp1.kiem_chung import cai_bat_thuong
from gp2.cau_hinh import CauHinhGP2
from . import cau_hinh as ch3
from .quy_trinh import chay_gp3

KICH_BAN = {
    "lam_phat": "Chấm dễ: HP cả lớp +1,5",
    "ep_diem": "Chấm khắt khe: HP cả lớp −2,0",
    "gioi_that": "SV giỏi thật: +1,5 ở MỌI lớp họ học",
}


def kiem_chung_gp3(d: pd.DataFrame, kq_goc: dict, cfg1: ch1.CauHinh, cfg2: CauHinhGP2,
                   cfg3: ch3.CauHinhGP3, so_lop: int = 25) -> pd.DataFrame:
    """Chạy từng kịch bản và đo ảnh hưởng tới GPA danh nghĩa, TCI và mức năng lực của SV bị ảnh hưởng.

    Tham số:
        d: bảng điểm tên cột ngắn (chưa bị cài).
        kq_goc: kết quả chay_gp3() trên dữ liệu gốc.
        cfg1, cfg2, cfg3: cấu hình; so_lop: số lớp bị cài mỗi kịch bản.
    Trả về:
        Bảng mỗi kịch bản: số SV bị ảnh hưởng, GPA danh nghĩa thay đổi TB, TCI thay đổi TB,
        tỷ lệ phần thay đổi bị gỡ (chấm dễ/khắt khe – càng cao càng tốt) hoặc được giữ
        (SV giỏi thật – càng gần 100% càng tốt), số SV bị đổi mức danh nghĩa và tỷ lệ được
        đưa về đúng mức.
    Vì sao cần: chứng minh TCI phản ánh năng lực thật chứ không phản ánh cách chấm.
    """
    rng = np.random.default_rng(cfg1.random_state)
    kq1 = kq_goc["kq_gp1"]
    ung_vien = kq1[(kq1["anomaly_type"] == ch1.NORMAL) & (kq1["n"] >= 20)
                   & ~kq1["is_project"].astype(bool) & (kq1["co_cau"] == ch1.CO_CAU_DU)]["class_id"].to_numpy()
    goc = kq_goc["phan_loai"].set_index("student")
    hang = {m: i for i, m in enumerate(ch3.THU_TU_MUC)}
    dong = []
    for kieu, mo_ta in KICH_BAN.items():
        chon = rng.choice(ung_vien, size=min(so_lop, len(ung_vien)), replace=False)
        moi = chay_gp3(cai_bat_thuong(d, kieu, chon, rng), cfg1, cfg2, cfg3, co_giai_thich=False)
        moi = moi["phan_loai"].set_index("student")
        sv = d.loc[d["class_id"].isin(chon), "student"].unique()
        sv = [s for s in sv if s in goc.index and s in moi.index]
        a, b = goc.loc[sv], moi.loc[sv]
        co_tci = a["TCI"].notna() & b["TCI"].notna()  # bỏ SV "Chưa đủ dữ liệu" (không có TCI để so)
        a, b = a[co_tci], b[co_tci]
        d_gpa = float((b["GPA4_goc"] - a["GPA4_goc"]).mean())
        d_tci = float((b["TCI"] - a["TCI"]).mean())
        bi_doi = b["muc_truoc"].map(hang) != a["muc_truoc"].map(hang)
        if kieu == "gioi_that":
            # năng lực tăng thật → mức TCI mới phải bằng mức danh nghĩa mới (không bị kéo xuống)
            dung = b.loc[bi_doi, "muc_sau"] == b.loc[bi_doi, "muc_truoc"]
            ty_le = d_tci / d_gpa if d_gpa else np.nan
        else:
            # cách chấm sai → mức TCI mới phải bằng mức TCI khi chưa cài
            dung = b.loc[bi_doi, "muc_sau"] == a.loc[bi_doi, "muc_sau"]
            ty_le = 1 - d_tci / d_gpa if d_gpa else np.nan
        dong.append(dict(kich_ban=mo_ta, so_sv_bi_anh_huong=len(a),
                         gpa_danh_nghia_doi_tb=round(d_gpa, 3), tci_doi_tb=round(d_tci, 3),
                         ty_le_go_hoac_giu=ty_le,
                         y_nghia_ty_le="phần tăng thật được GIỮ" if kieu == "gioi_that" else "phần sai lệch được GỠ",
                         so_sv_doi_muc_danh_nghia=int(bi_doi.sum()),
                         ty_le_ve_dung_muc=float(dung.mean()) if len(dung) else np.nan))
        print(f"  [{kieu:10s}] {len(a)} SV: GPA danh nghĩa {d_gpa:+.3f}, TCI {d_tci:+.3f}; "
              f"{int(bi_doi.sum())} SV đổi mức danh nghĩa, {dong[-1]['ty_le_ve_dung_muc']:.0%} được xếp đúng mức")
    return pd.DataFrame(dong)
