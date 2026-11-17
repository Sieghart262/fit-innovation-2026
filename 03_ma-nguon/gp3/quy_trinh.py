"""Nối Giải pháp 1 → 2 → 3 thành một quy trình."""

from __future__ import annotations

import pandas as pd

from gp1 import cau_hinh as ch1
from gp2.cau_hinh import CauHinhGP2
from gp2.quy_trinh import chay_gp2
from .cau_hinh import CauHinhGP3
from .giai_thich import giai_thich
from .tci import mon_cua_sinh_vien, tinh_tci


def chay_gp3(d_goc: pd.DataFrame, cfg1: ch1.CauHinh | None = None, cfg2: CauHinhGP2 | None = None,
             cfg3: CauHinhGP3 | None = None, co_giai_thich: bool = True) -> dict:
    """Chạy cả 3 giải pháp trên bảng điểm (tên cột ngắn, từ gp1.du_lieu.chuan_bi).

    Tham số:
        d_goc: bảng điểm; cfg1/cfg2/cfg3: cấu hình từng giải pháp;
        co_giai_thich: False để bỏ bước viết lời giải thích (chạy nhanh hơn khi kiểm chứng).
    Trả về:
        dict của chay_gp2() cộng thêm mon_sv (môn của từng SV) và phan_loai (TCI, mức, giải thích).
    Vì sao cần: một lệnh duy nhất cho ra toàn bộ kết quả, dùng chung cho dòng lệnh và dashboard.
    """
    cfg3 = cfg3 or CauHinhGP3()
    kq = chay_gp2(d_goc, cfg1, cfg2)
    mon = mon_cua_sinh_vien(kq["diem"], kq["kq_gp1"])
    sv = tinh_tci(mon, cfg3)
    if co_giai_thich:
        sv["giai_thich"] = giai_thich(sv, mon, cfg3)
    kq.update(mon_sv=mon, phan_loai=sv)
    return kq
