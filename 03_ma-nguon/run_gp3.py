"""Chạy cả 3 giải pháp và ghi toàn bộ kết quả (đầu vào cho dashboard).

Cách chạy (từ thư mục gốc dự án):
    .venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp3.py                (dữ liệu thật)
    .venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp3.py --kiem-chung   (+ mô phỏng cả 3 giải pháp, ~3 phút)

Ghi vào 01_du-lieu/ket-qua/gp1, gp2, gp3 (không đưa lên GitHub) và lưu một bản vào
01_du-lieu/lich-su-phan-tich/; kết quả đang dùng trước đó được cất vào lịch sử trước khi ghi đè.
Màn hình chỉ in số liệu tổng hợp. Sau đó mở dashboard:
    .venv/Scripts/streamlit.exe run 03_ma-nguon/dashboard/app.py
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kho_ket_qua as kho  # noqa: E402
from eda import config as cf  # noqa: E402
from eda.load import doc_du_lieu_diem  # noqa: E402
from gp1 import cau_hinh as ch1  # noqa: E402
from gp1.du_lieu import chuan_bi  # noqa: E402
from gp1.kiem_chung import kiem_chung as kiem_chung_gp1  # noqa: E402
from gp2 import cau_hinh as ch2  # noqa: E402
from gp2.kiem_chung import kiem_chung_gp2  # noqa: E402
from gp3 import cau_hinh as ch3  # noqa: E402
from gp3.kiem_chung import kiem_chung_gp3  # noqa: E402
from gp3.quy_trinh import chay_gp3  # noqa: E402

THU_MUC_KET_QUA = kho.THU_MUC_KET_QUA
ghi_tat_ca = kho.ghi_tat_ca  # giữ tên cũ cho code/tài liệu đang gọi run_gp3.ghi_tat_ca


def main() -> None:
    """Đọc dữ liệu, chạy GP1 → GP3, (tùy chọn) kiểm chứng, ghi kết quả và in tóm tắt."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Chạy cả 3 giải pháp")
    p.add_argument("--du-lieu", type=Path, default=cf.FILE_DIEM, help="file Du_lieu.csv")
    p.add_argument("--ra", type=Path, default=THU_MUC_KET_QUA, help="thư mục gốc ghi kết quả")
    p.add_argument("--kiem-chung", action="store_true", help="chạy thêm kiểm chứng mô phỏng của cả 3 giải pháp")
    a = p.parse_args()
    cfg1, cfg2, cfg3 = ch1.CauHinh(), ch2.CauHinhGP2(), ch3.CauHinhGP3()
    bat_dau = time.perf_counter()

    print("1) Đọc dữ liệu ...")
    d = chuan_bi(doc_du_lieu_diem(a.du_lieu)[0])
    print(f"   {len(d):,} dòng, {d['class_id'].nunique():,} lớp")

    print("2) Giải pháp 1 → 2 → 3 ...")
    kq = chay_gp3(d, cfg1, cfg2, cfg3)
    sv = kq["phan_loai"]
    print(f"   GP1: {int(kq['kq_gp1']['anomaly_type'].isin(ch1.NHAN_BAT_THUONG).sum())} lớp bất thường; "
          f"GP2: {int(kq['lop']['dich_chuyen'].ne(0).sum())} lớp được hiệu chỉnh")
    print("   GP3 – số SV theo mức (GPA danh nghĩa → TCI):")
    for muc in ch3.THU_TU_MUC:
        print(f"     {muc:13s} {int((sv['muc_truoc'] == muc).sum()):5d} → {int((sv['muc_sau'] == muc).sum()):5d}")
    print(f"   SV đổi mức: {int(sv['doi_muc'].ne('Giữ nguyên').sum())} "
          f"(lên {int(sv['doi_muc'].eq('Lên mức').sum())}, xuống {int(sv['doi_muc'].eq('Xuống mức').sum())}); "
          f"độ tin cậy thấp: {int(sv['do_tin_cay'].eq(ch3.DO_TIN_CAY_THAP).sum())} SV; "
          f"chưa đủ dữ liệu: {int(sv['TCI'].isna().sum())} SV")

    kc = None
    if a.kiem_chung:
        print("3) Kiểm chứng bằng mô phỏng ...")
        print("  Giải pháp 1:")
        kc = {"gp1": kiem_chung_gp1(d, kq["kq_gp1"], cfg1)}
        print("  Giải pháp 2:")
        kc["gp2"] = kiem_chung_gp2(d, kq["kq_gp1"], cfg1, cfg2)
        print("  Giải pháp 3:")
        kc["gp3"] = kiem_chung_gp3(d, kq, cfg1, cfg2, cfg3)

    print("4) Ghi kết quả 3 giải pháp ...")
    lich_su = kho.thu_muc_lich_su(a.ra)
    kho.luu_lich_su(a.ra, lich_su)  # cất kết quả đang dùng (nếu có) vào lịch sử trước khi ghi đè
    kho.xoa_ket_qua(a.ra)
    kho.ghi_tat_ca(kq, kc, cfg1, cfg2, cfg3, a.ra)
    kho.ghi_thong_tin(a.ra, a.du_lieu.name, kho.CACH_LENH, str(a.du_lieu.resolve()), kho.tom_tat_kq(kq))
    kho.luu_lich_su(a.ra, lich_su)  # mọi lần phân tích đều có trong lịch sử
    print(f"   Đã ghi vào {a.ra} (gp1, gp2, gp3) và lưu vào lịch sử {lich_su}")
    print(f"Xong trong {time.perf_counter() - bat_dau:.1f} giây.")


if __name__ == "__main__":
    main()
