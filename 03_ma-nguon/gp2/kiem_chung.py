"""Kiểm chứng Giải pháp 2 bằng mô phỏng: cài bất thường biết trước, đo xem hiệu chỉnh
gỡ được bao nhiêu phần đã cài và có sửa oan lớp không bị cài không.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from gp1 import cau_hinh as ch1
from gp1.kiem_chung import cai_bat_thuong
from .cau_hinh import CauHinhGP2
from .quy_trinh import chay_gp2

# kịch bản → (mô tả, số điểm đã cài vào cả lớp; 0 = không nên bị sửa)
KICH_BAN = {
    "lam_phat": ("Chấm dễ: HP cả lớp +1,5", 1.5),
    "ep_diem": ("Chấm khắt khe: HP cả lớp −2,0", -2.0),
    "gioi_that": ("SV giỏi thật: +1,5 ở MỌI lớp họ học", 0.0),
}


def kiem_chung_gp2(d: pd.DataFrame, kq_gp1: pd.DataFrame, cfg1: ch1.CauHinh, cfg2: CauHinhGP2,
                   so_lop: int = 25) -> pd.DataFrame:
    """Chạy từng kịch bản và đo kết quả hiệu chỉnh.

    Tham số:
        d: bảng điểm tên cột ngắn (chưa bị cài).
        kq_gp1: kết quả GP1 trên dữ liệu gốc (chọn lớp đang bình thường để cài).
        cfg1, cfg2: cấu hình; so_lop: số lớp bị cài mỗi kịch bản.
    Trả về:
        Bảng mỗi kịch bản: tỷ lệ lớp được hiệu chỉnh, mức dịch chuyển TB (điểm bị trừ;
        âm = được cộng), tỷ lệ phần cài được gỡ, và mức dịch chuyển TB ở lớp KHÔNG bị cài.
    Vì sao cần: chứng minh hiệu chỉnh sửa đúng hướng, đúng mức và không sửa oan.
    """
    rng = np.random.default_rng(cfg1.random_state)
    ung_vien = kq_gp1[(kq_gp1["anomaly_type"] == ch1.NORMAL) & (kq_gp1["n"] >= 20)
                      & ~kq_gp1["is_project"].astype(bool) & (kq_gp1["co_cau"] == ch1.CO_CAU_DU)]
    ung_vien = ung_vien["class_id"].to_numpy()
    dong = []
    for kieu, (mo_ta, da_cai) in KICH_BAN.items():
        chon = rng.choice(ung_vien, size=min(so_lop, len(ung_vien)), replace=False)
        lop = chay_gp2(cai_bat_thuong(d, kieu, chon, rng), cfg1, cfg2)["lop"].set_index("class_id")
        cai = lop.loc[chon]
        khac = lop.loc[[c for c in ung_vien if c not in set(chon)]]
        dich = float(cai["dich_chuyen"].mean())
        dong.append(dict(
            kich_ban=mo_ta, so_lop_cai=len(chon), diem_da_cai=da_cai,
            ty_le_lop_duoc_hieu_chinh=float(cai["du_dieu_kien_hieu_chinh"].mean()),
            dich_chuyen_tb=dich,
            ty_le_phan_cai_duoc_go=(dich / da_cai) if da_cai else np.nan,
            dich_chuyen_tb_lop_khong_cai=float(khac["dich_chuyen"].abs().mean())))
        print(f"  [{kieu:10s}] hiệu chỉnh {dong[-1]['ty_le_lop_duoc_hieu_chinh']:.0%} lớp, "
              f"dịch chuyển TB {dich:+.2f} điểm (đã cài {da_cai:+.1f})")
    return pd.DataFrame(dong)
