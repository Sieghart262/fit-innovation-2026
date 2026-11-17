"""Chạy Giải pháp 1 – Phát hiện lớp học phần có điểm bất thường.

Cách chạy (từ thư mục gốc dự án):
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\run_gp1.py                 (dữ liệu thật)
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\run_gp1.py --kiem-chung    (+ mô phỏng, vài phút)
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\run_gp1.py --du-lieu 01_du-lieu\\gia-lap\\Du_lieu.csv
        --ra 01_du-lieu\\gia-lap\\gp1 --kiem-chung                             (dữ liệu giả)

Kết quả ghi vào 01_du-lieu/ket-qua/gp1/ (không đưa lên GitHub). Màn hình chỉ in số
liệu tổng hợp (số lớp theo nhãn), không in dòng điểm nào.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda import config as cf  # noqa: E402
from eda.load import doc_du_lieu_diem  # noqa: E402
from gp1 import cau_hinh as ch  # noqa: E402
from gp1.du_lieu import chuan_bi  # noqa: E402
from gp1.kiem_chung import kiem_chung  # noqa: E402
from gp1.quy_trinh import chay_quy_trinh  # noqa: E402
from gp1.xuat import diem_nong, ghi_bao_cao, ghi_ket_qua, ve_bieu_do, xu_huong  # noqa: E402


def main() -> None:
    """Đọc dữ liệu, chạy Giải pháp 1, (tùy chọn) kiểm chứng, ghi kết quả và in tóm tắt."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Giải pháp 1 – Phát hiện lớp học phần có điểm bất thường")
    p.add_argument("--du-lieu", type=Path, default=cf.FILE_DIEM, help="file Du_lieu.csv")
    p.add_argument("--ra", type=Path, default=ch.THU_MUC_KET_QUA, help="thư mục ghi kết quả")
    p.add_argument("--kiem-chung", action="store_true", help="chạy thêm kiểm chứng bằng mô phỏng")
    a = p.parse_args()
    cfg = ch.CauHinh()
    bat_dau = time.perf_counter()

    print("1) Đọc dữ liệu ...")
    bang, _ = doc_du_lieu_diem(a.du_lieu)
    d = chuan_bi(bang)
    print(f"   {len(d):,} dòng, {d['class_id'].nunique():,} lớp")

    print("2) Phân tích và chấm điểm bất thường ...")
    kq, _, diem, ds_moc, b = chay_quy_trinh(d, cfg)
    print("   Số lớp theo nhãn:")
    for nhan, so in kq["anomaly_type"].value_counts().items():
        print(f"     {nhan:24s} {so:5d}  ({ch.Y_NGHIA_NHAN[nhan]})")
    print(f"   Đủ điều kiện hiệu chỉnh ở GP2: {int(kq['du_dieu_kien_hieu_chinh'].sum())} lớp")

    kc = None
    if a.kiem_chung:
        print("3) Kiểm chứng bằng mô phỏng ...")
        kc = kiem_chung(d, kq, cfg)

    print("4) Ghi kết quả ...")
    hs = diem_nong(kq)
    xh, doc = xu_huong(kq)
    hinh = ve_bieu_do(kq, diem, ds_moc, xh, a.ra / "charts")
    files = ghi_ket_qua(kq, hs, xh, doc, kc, cfg, a.ra)
    bc = ghi_bao_cao(kq, hs, doc, kc, b, hinh, a.ra)
    print(f"   {len(files)} file CSV, {len(hinh)} biểu đồ, báo cáo: {bc}")
    print(f"Xong trong {time.perf_counter() - bat_dau:.1f} giây.")


if __name__ == "__main__":
    main()
