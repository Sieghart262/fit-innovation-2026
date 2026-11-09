"""Nối Giải pháp 1 → Giải pháp 2 thành một quy trình."""

from __future__ import annotations

import pandas as pd

from gp1 import cau_hinh as ch1
from gp1.quy_trinh import chay_quy_trinh
from .cau_hinh import CauHinhGP2
from .gpa import tinh_gpa
from .hieu_chinh import ap_dung, tinh_dich_chuyen_lop
from .ky_vong import diem_ky_vong


def chay_gp2(d_goc: pd.DataFrame, cfg1: ch1.CauHinh | None = None, cfg2: CauHinhGP2 | None = None) -> dict:
    """Chạy Giải pháp 1 rồi Giải pháp 2 trên bảng điểm (tên cột ngắn, từ gp1.du_lieu.chuan_bi).

    Các bước:
        1. Giải pháp 1: nhãn từng lớp, lớp nào đủ điều kiện hiệu chỉnh.
        2. Phương án A: Δ, α → Adjusted_Score cho lớp đủ điều kiện.
        3. Phương án C: điểm kỳ vọng từng SV → REVIEW_REQUIRED (chỉ gắn cờ).
        4. GPA hệ 10 trước/sau (Normalized_GPA).
    Tham số:
        d_goc: bảng điểm tên cột ngắn; cfg1, cfg2: cấu hình GP1, GP2.
    Trả về:
        dict gồm kq_gp1, lop (hiệu chỉnh theo lớp), diem (từng lượt), sv (GPA), sigma_w.
    Vì sao cần: luôn chạy GP1 cùng lúc để GP2 dùng đúng kết quả của cùng một dữ liệu,
    và để kiểm chứng mô phỏng chạy lại được cả chuỗi.
    """
    cfg1, cfg2 = cfg1 or ch1.CauHinh(), cfg2 or CauHinhGP2()
    kq, d, _, ds_moc, _ = chay_quy_trinh(d_goc, cfg1)
    lop = tinh_dich_chuyen_lop(kq, ds_moc, d, cfg2)
    dd = ap_dung(d, lop, cfg2)
    dd, sigma_w = diem_ky_vong(dd, cfg2)
    return dict(kq_gp1=kq, lop=lop, diem=dd, sv=tinh_gpa(dd), sigma_w=sigma_w)
