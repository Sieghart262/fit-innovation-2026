"""Chạy Giải pháp 2 – Hiệu chỉnh điểm (tự chạy Giải pháp 1 trước).

Cách chạy (từ thư mục gốc dự án):
    .venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp2.py                (dữ liệu thật)
    .venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp2.py --kiem-chung   (+ mô phỏng, ~1 phút)

Kết quả ghi vào 01_du-lieu/ket-qua/gp2/ (không đưa lên GitHub). Màn hình chỉ in số liệu
tổng hợp, không in điểm của SV nào.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda import config as cf  # noqa: E402
from eda.load import doc_du_lieu_diem  # noqa: E402
from gp1 import cau_hinh as ch1  # noqa: E402
from gp1.du_lieu import chuan_bi  # noqa: E402
from gp2 import cau_hinh as ch2  # noqa: E402
from gp2.kiem_chung import kiem_chung_gp2  # noqa: E402
from gp2.quy_trinh import chay_gp2  # noqa: E402
from gp2.xuat import ghi_bao_cao, ghi_ket_qua, ve_bieu_do  # noqa: E402


def main() -> None:
    """Đọc dữ liệu, chạy GP1 + GP2, (tùy chọn) kiểm chứng, ghi kết quả và in tóm tắt."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Giải pháp 2 – Hiệu chỉnh điểm")
    p.add_argument("--du-lieu", type=Path, default=cf.FILE_DIEM, help="file Du_lieu.csv")
    p.add_argument("--ra", type=Path, default=ch2.THU_MUC_KET_QUA, help="thư mục ghi kết quả")
    p.add_argument("--kiem-chung", action="store_true", help="chạy thêm kiểm chứng bằng mô phỏng")
    a = p.parse_args()
    cfg1, cfg2 = ch1.CauHinh(), ch2.CauHinhGP2()
    bat_dau = time.perf_counter()

    print("1) Đọc dữ liệu ...")
    d = chuan_bi(doc_du_lieu_diem(a.du_lieu)[0])
    print(f"   {len(d):,} dòng, {d['class_id'].nunique():,} lớp")

    print("2) Giải pháp 1 + hiệu chỉnh điểm ...")
    kq = chay_gp2(d, cfg1, cfg2)
    lop, dd, sv = kq["lop"], kq["diem"], kq["sv"]
    sua = lop[lop["dich_chuyen"].ne(0)]
    print(f"   Lớp được hiệu chỉnh: {len(sua)} (trừ điểm {int((sua['dich_chuyen'] > 0).sum())}, "
          f"cộng điểm {int((sua['dich_chuyen'] < 0).sum())}); lượt điểm: {int(dd['duoc_hieu_chinh'].sum()):,}")
    print(f"   REVIEW_REQUIRED: {int(dd['co_review'].sum()):,} lượt "
          f"/ {int(dd['diem_ky_vong'].notna().sum()):,} lượt có điểm kỳ vọng")
    print(f"   GPA TB: gốc {sv['GPA_goc'].mean():.3f} → hiệu chỉnh {sv['Normalized_GPA'].mean():.3f}; "
          f"{int(sv['chenh_GPA'].ne(0).sum()):,} SV có GPA thay đổi")

    kc = None
    if a.kiem_chung:
        print("3) Kiểm chứng bằng mô phỏng ...")
        kc = kiem_chung_gp2(d, kq["kq_gp1"], cfg1, cfg2)

    print("4) Ghi kết quả ...")
    hinh = ve_bieu_do(sv, lop, a.ra / "charts")
    files = ghi_ket_qua(kq, kc, cfg2, a.ra)
    bc = ghi_bao_cao(kq, kc, hinh, a.ra)
    print(f"   {len(files)} file CSV, {len(hinh)} biểu đồ, báo cáo: {bc}")
    print(f"Xong trong {time.perf_counter() - bat_dau:.1f} giây.")


if __name__ == "__main__":
    main()
