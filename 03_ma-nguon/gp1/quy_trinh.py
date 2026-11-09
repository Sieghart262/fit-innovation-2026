"""Nối các bước của Giải pháp 1 thành một quy trình chạy từ đầu đến cuối."""

from __future__ import annotations

import pandas as pd

from . import cau_hinh as ch
from .cham_diem import cham_lop
from .dac_trung import dac_trung_lop
from .du_lieu import lam_sach, tinh_trang_lop
from .nang_luc import tinh_nang_luc
from .so_sanh import so_sanh_moc


def chay_quy_trinh(d_goc: pd.DataFrame, cfg: ch.CauHinh | None = None):
    """Chạy toàn bộ Giải pháp 1 trên bảng điểm (tên cột ngắn, từ du_lieu.chuan_bi).

    Các bước:
        1. Làm sạch: tách SV vắng thi; xác định cơ cấu điểm và lớp dữ liệu chưa đủ.
        2. Năng lực nền của SV (leave-one-class-out, chuẩn hóa theo môn trong ±1 năm).
        3. Đặc trưng thống kê từng lớp.
        4. So với mốc (cùng môn → cùng nhóm môn; cùng loại, cùng cơ cấu, ±1 năm).
        5. Chấm điểm: lệch + bằng chứng → nhãn, Anomaly Score, giải thích.
    Tham số:
        d_goc: bảng điểm tên cột ngắn (có thể đã bị cài bất thường khi kiểm chứng).
        cfg: cấu hình (mặc định CauHinh()).
    Trả về:
        (bảng kết quả 1 dòng/lớp, bảng lượt điểm đã xử lý, {lớp: điểm HP}, {lớp: các lớp mốc}, hệ số b).
    Vì sao cần: kiểm chứng bằng mô phỏng phải chạy lại đúng y quy trình này nhiều lần.
    """
    cfg = cfg or ch.CauHinh()
    d = lam_sach(d_goc)
    d = d.merge(tinh_trang_lop(d, cfg), on="class_id", how="left")
    d, b = tinh_nang_luc(d, cfg)
    lop, diem = dac_trung_lop(d, b, cfg)
    kq, ds_moc = so_sanh_moc(lop, diem, cfg)
    kq = cham_lop(kq, cfg)
    return kq, d, diem, ds_moc, b
