"""Chạy cả 3 giải pháp và ghi toàn bộ kết quả (đầu vào cho dashboard).

Cách chạy (từ thư mục gốc dự án):
    .venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp3.py                (dữ liệu thật)
    .venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp3.py --kiem-chung   (+ mô phỏng GP3, ~2 phút)

Ghi vào 01_du-lieu/ket-qua/gp1, gp2, gp3 (không đưa lên GitHub). Màn hình chỉ in số liệu
tổng hợp. Sau đó mở dashboard:
    .venv/Scripts/streamlit.exe run 03_ma-nguon/dashboard/app.py
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda import config as cf  # noqa: E402
from eda.load import doc_du_lieu_diem  # noqa: E402
from gp1 import cau_hinh as ch1, xuat as x1  # noqa: E402
from gp1.du_lieu import chuan_bi  # noqa: E402
from gp2 import cau_hinh as ch2, xuat as x2  # noqa: E402
from gp3 import cau_hinh as ch3, xuat as x3  # noqa: E402
from gp3.kiem_chung import kiem_chung_gp3  # noqa: E402
from gp3.quy_trinh import chay_gp3  # noqa: E402

THU_MUC_KET_QUA = cf.THU_MUC_GOC / "01_du-lieu" / "ket-qua"


def ghi_tat_ca(kq: dict, kc, cfg1, cfg2, cfg3, goc: Path) -> None:
    """Ghi kết quả của cả 3 giải pháp vào goc/gp1, goc/gp2, goc/gp3.

    Tham số:
        kq: kết quả chay_gp3(); kc: bảng kiểm chứng GP3 (có thể None); cfg1-3: cấu hình; goc: thư mục gốc.
    Vì sao cần: dashboard đọc đủ 3 thư mục; chạy một lệnh là có đủ dữ liệu cho dashboard.
    """
    t1, t2, t3 = goc / "gp1", goc / "gp2", goc / "gp3"
    hs, (xh, doc) = x1.diem_nong(kq["kq_gp1"]), x1.xu_huong(kq["kq_gp1"])
    h1 = x1.ve_bieu_do(kq["kq_gp1"], kq["diem_lop"], kq["ds_moc"], xh, t1 / "charts")
    x1.ghi_ket_qua(kq["kq_gp1"], hs, xh, doc, None, cfg1, t1)
    x1.ghi_bao_cao(kq["kq_gp1"], hs, doc, None, kq["b"], h1, t1)
    h2 = x2.ve_bieu_do(kq["sv"], kq["lop"], t2 / "charts")
    x2.ghi_ket_qua(kq, None, cfg2, t2)
    x2.ghi_bao_cao(kq, None, h2, t2)
    h3 = x3.ve_bieu_do(kq["phan_loai"], t3 / "charts")
    x3.ghi_ket_qua(kq, kc, cfg3, t3)
    x3.ghi_bao_cao(kq, kc, h3, t3)


def main() -> None:
    """Đọc dữ liệu, chạy GP1 → GP3, (tùy chọn) kiểm chứng, ghi kết quả và in tóm tắt."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Chạy cả 3 giải pháp")
    p.add_argument("--du-lieu", type=Path, default=cf.FILE_DIEM, help="file Du_lieu.csv")
    p.add_argument("--ra", type=Path, default=THU_MUC_KET_QUA, help="thư mục gốc ghi kết quả")
    p.add_argument("--kiem-chung", action="store_true", help="chạy thêm kiểm chứng mô phỏng của GP3")
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
          f"độ tin cậy thấp: {int(sv['do_tin_cay'].eq(ch3.DO_TIN_CAY_THAP).sum())} SV")

    kc = None
    if a.kiem_chung:
        print("3) Kiểm chứng GP3 bằng mô phỏng ...")
        kc = kiem_chung_gp3(d, kq, cfg1, cfg2, cfg3)

    print("4) Ghi kết quả 3 giải pháp ...")
    ghi_tat_ca(kq, kc, cfg1, cfg2, cfg3, a.ra)
    print(f"   Đã ghi vào {a.ra} (gp1, gp2, gp3)")
    print(f"Xong trong {time.perf_counter() - bat_dau:.1f} giây.")


if __name__ == "__main__":
    main()
