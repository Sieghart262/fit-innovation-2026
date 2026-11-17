"""Tạo bộ dữ liệu GIẢ cho video demo và chọn sẵn "lớp chấm dễ" + sinh viên để quay.

Video demo (3–5 phút) theo đề: phát hiện 1 lớp điểm cao bất thường → hiệu chỉnh điểm →
mức năng lực TCI của sinh viên thay đổi. Video công khai nên CHỈ dùng dữ liệu giả.

Cách chạy (ở thư mục gốc dự án):
    .venv/Scripts/python.exe -X utf8 05_video-demo/tao_du_lieu_demo.py

Kết quả:
    01_du-lieu/video-demo/Du_lieu_demo.csv   file điểm giả (19 cột, đúng định dạng BTC) để tải lên dashboard
    Màn hình in: lớp nên chọn để quay, lý do GP1 gắn nhãn, mức hiệu chỉnh, và vài sinh viên
    của lớp đó bị đổi mức (mã SV giả) – dùng để điền vào kịch bản.
Cùng seed → cùng dữ liệu, cùng lớp, cùng sinh viên.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "03_ma-nguon"))

import tao_du_lieu_gia as tg  # noqa: E402
from eda.load import doc_du_lieu_diem  # noqa: E402
from gp1.du_lieu import chuan_bi  # noqa: E402
from gp3.quy_trinh import chay_gp3  # noqa: E402

import numpy as np  # noqa: E402

THU_MUC_RA = GOC / "01_du-lieu" / "video-demo"  # trong 01_du-lieu/ nên không lên GitHub


def tao_file(seed: int, so_sv: int) -> Path:
    """Sinh dữ liệu giả sạch (không ô lỗi) và ghi Du_lieu_demo.csv.

    Tham số:
        seed: hạt giống ngẫu nhiên; so_sv: số sinh viên giả.
    Trả về:
        Đường dẫn file đã ghi.
    Vì sao cần: dùng lại đúng bộ sinh dữ liệu giả của dự án, chỉ thêm tên file riêng cho video.
    """
    a = argparse.Namespace(so_sv=so_sv, nhan_lop=1, seed=seed, sach=True, cai_loi=False, phay_thap_phan=False)
    dong, _ = tg.tao_bang_diem(a, np.random.default_rng(seed))
    THU_MUC_RA.mkdir(parents=True, exist_ok=True)
    f = THU_MUC_RA / "Du_lieu_demo.csv"
    tg.ghi_csv(f, tg.COT_DIEM, dong, ",")
    return f


def chon_lop_va_sv(kq: dict) -> tuple[str | None, list]:
    """Chọn lớp HIGH_INFLATION có nhiều sinh viên bị xuống mức nhất vì chính lớp đó.

    Tham số:
        kq: kết quả chay_gp3().
    Trả về:
        (mã lớp, danh sách mã SV của lớp đó bị xuống mức và có độ tin cậy bình thường).
    Vì sao cần: video cần một ví dụ rõ ràng, nối liền cả 3 giải pháp.
    """
    lop = kq["kq_gp1"]
    ung_vien = lop[(lop["anomaly_type"] == "HIGH_INFLATION") & lop["du_dieu_kien_hieu_chinh"].eq(True)
                   & (lop["n"] >= 15)]["class_id"]
    sv = kq["phan_loai"].set_index("student")
    mon = kq["mon_sv"]
    tot, ds_tot = None, []
    for cid in ung_vien:
        hoc = mon[(mon["class_id"] == cid) & mon["duoc_hieu_chinh"].astype(bool)]["student"]
        hoc = [s for s in hoc if sv.loc[s, "doi_muc"] == "Xuống mức" and sv.loc[s, "do_tin_cay"] != "Thấp"]
        if len(hoc) > len(ds_tot):
            tot, ds_tot = cid, hoc
    # SV có GPA cao xếp trước: "từ Advanced xuống Proficient" dễ hiểu nhất khi xem video
    return tot, sorted(ds_tot, key=lambda s: -sv.loc[s, "GPA4_goc"])


def in_goi_y(kq: dict, cid: str, ds_sv: list) -> None:
    """In thông tin lớp và sinh viên để điền vào kịch bản (dữ liệu giả nên được phép in)."""
    lop = kq["kq_gp1"].set_index("class_id").loc[cid]
    hc = kq["lop"].set_index("class_id").loc[cid]
    print(f"\nLỚP NÊN QUAY: {cid} – môn {lop['course']}, {lop['year']} HK{lop['sem']}, {int(lop['n'])} điểm hợp lệ")
    print(f"  Nhãn: {lop['anomaly_type']} – Anomaly Score {lop['anomaly_score']:.2f} ({lop['severity']}), "
          f"hạng {int(lop['rank'])}")
    print(f"  ĐTB lớp {lop['mean']:.2f} so với mốc {lop['ref_mean']:.2f}; tỷ lệ A {lop['a_rate']:.0%}")
    print(f"  Giải thích: {lop['explanation']}")
    print(f"  Hiệu chỉnh: α = {hc['alpha']:.2f}, Δ = {hc['delta']:.2f} → mỗi SV bị trừ {hc['dich_chuyen']:.2f} điểm")
    sv = kq["phan_loai"].set_index("student")
    print(f"\nSINH VIÊN CỦA LỚP BỊ XUỐNG MỨC ({len(ds_sv)} SV), chọn 1 để tra cứu:")
    for s in ds_sv[:5]:
        r = sv.loc[s]
        print(f"  {s}: GPA {r['GPA4_goc']:.2f} ({r['muc_truoc']}) → TCI {r['TCI']:.2f} ({r['muc_sau']}), "
              f"{int(r['so_mon'])} môn")
    if ds_sv:
        print(f"\n  Giải thích của {ds_sv[0]}: {sv.loc[ds_sv[0], 'giai_thich']}")
    p = kq["phan_loai"]
    print(f"\nTỔNG QUAN: {len(p)} SV; đổi mức {int(p['doi_muc'].ne('Giữ nguyên').sum())}; "
          f"{int(kq['kq_gp1']['anomaly_type'].isin(['HIGH_INFLATION', 'UNUSUALLY_STEEP', 'SUSPICIOUS_DISTRIBUTION']).sum())} "
          f"lớp bất thường; {int(kq['lop']['dich_chuyen'].ne(0).sum())} lớp được hiệu chỉnh")


def main() -> None:
    """Tạo file, chạy GP1 → GP3 và in gợi ý cho kịch bản."""
    ap = argparse.ArgumentParser(description="Tạo dữ liệu giả cho video demo")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--so-sv", type=int, default=1500)
    a = ap.parse_args()
    f = tao_file(a.seed, a.so_sv)
    print(f"Đã ghi {f}")
    kq = chay_gp3(chuan_bi(doc_du_lieu_diem(f)[0]))
    cid, ds = chon_lop_va_sv(kq)
    if cid is None:
        print("Không có lớp HIGH_INFLATION phù hợp – thử seed khác.")
        return
    in_goi_y(kq, cid, ds)


if __name__ == "__main__":
    main()
