"""Tạo Du_lieu.csv và Thoi_khoa_bieu.csv GIẢ, đúng cấu trúc trong Mo_ta_du_lieu_diem.docx.

Toàn bộ là số ngẫu nhiên – KHÔNG lấy gì từ dữ liệu thật của BTC – nên được phép
dùng cho demo công khai, đưa lên GitHub, hoặc gửi cho công cụ AI.

Dùng để:
    1. Chạy thử code (EDA, 3 giải pháp) mà không cần đụng dữ liệu thật.
    2. Demo trên dashboard/Web API công khai.
    3. Chứng minh code chạy được với dữ liệu lớn (tiêu chí chấm: n > 10^5).

Những gì được mô phỏng (theo file mô tả):
    - 7 năm học 2019-2020 → 2025-2026, học kỳ 1, 2 và ít học kỳ 3.
    - Trọng số CC/KTTX/Thi = 10/20/70 trước HK2 2021-22, 10/40/50 từ đó;
      cột trọng số để trống ở ~36% dòng.
    - 2019-2020 phần lớn thiếu CC/KTTX; một số lớp 2025-2026 HK2 chưa có Thi/HP.
    - Điểm HP = 0 khi vắng thi (~3%); KTTX2 để trống ~98%; Khóa SV trống ~0,1%.
    - Học phần đồ án chỉ có Thi và HP; ~8% lớp là lớp EP.
    - ~8% lớp được CỐ Ý cài "KTTX chấm dễ" (KTTX cao và đồng đều) để kiểm tra
      xem thuật toán phát hiện bất thường có tìm ra chúng không.
    - Vài ô ghi "vắng" ở cột Thi để kiểm tra bộ đếm ô không đọc được.

Cách dùng (từ thư mục gốc dự án):
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\tao_du_lieu_gia.py
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\tao_du_lieu_gia.py --nhan-lop 6 --so-sv 8000   (~106.000 dòng)
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\tao_du_lieu_gia.py --sep ";" --phay-thap-phan  (kiểu Excel tiếng Việt)

Kiểm tra code bắt lỗi (xem kiem_tra_bat_loi.py):
    --sach      không có ô lỗi nào → code phải báo 0 lỗi ở mọi cột.
    --cai-loi   cài lỗi vào cả 19 cột, mỗi loại lỗi một số lượng khác nhau, và ghi
                đáp án ra dap_an_loi.json → code phải bắt đúng từng con số.

Rồi chạy EDA trên dữ liệu giả:
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\run_eda.py --du-lieu 01_du-lieu\\gia-lap\\Du_lieu.csv
        --tkb 01_du-lieu\\gia-lap\\Thoi_khoa_bieu.csv --bao-cao 01_du-lieu\\gia-lap\\bao-cao\\02-ket-qua-eda.md
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eda import config as cf  # chỉ lấy tên loại lỗi

THU_MUC_GOC = Path(__file__).resolve().parents[1]
THU_MUC_RA_MAC_DINH = THU_MUC_GOC / "01_du-lieu" / "gia-lap"  # nằm trong 01_du-lieu/ nên bị .gitignore chặn

COT_DIEM = ["Năm học", "Học kỳ", "Mã môn", "Nhóm môn", "Số TC", "Là đồ án/thực tập/khóa luận",
            "Lớp mang mã EP", "Mã lớp học phần", "Sĩ số lớp (trong dữ liệu)", "Mã SV", "Khóa SV",
            "Khoa của SV", "CC", "KTTX1", "KTTX2", "KTTX (TB)", "Thi", "Điểm HP (thang 10)",
            "Cơ cấu trọng số suy ra (CC/KTTX/Thi, %)"]
COT_TKB = ["Năm học", "Học kỳ", "Hệ", "Mã HP", "Số TC", "Sĩ số ĐK", "Mã LHP", "Thứ", "Tiết bắt đầu",
           "Tiết kết thúc", "Tuần bắt đầu", "Tuần kết thúc", "Phòng", "Dạng lịch", "Ngày bắt đầu",
           "Ngày kết thúc", "Số tiết đứng lớp", "Số tiết hệ thống"]


def doc_tham_so() -> argparse.Namespace:
    """Đọc tham số dòng lệnh.

    Trả về:
        Các tham số: thư mục ra, ký tự ngăn cột, kiểu dấu thập phân, số SV,
        hệ số nhân số lớp và seed.
    Vì sao cần: cùng một công cụ tạo được bộ nhỏ để thử nhanh, bộ lớn để thử
    tốc độ, và bộ kiểu Excel tiếng Việt để thử phần đọc file.
    """
    p = argparse.ArgumentParser(description="Tạo dữ liệu điểm GIẢ cùng cấu trúc với dữ liệu BTC.")
    p.add_argument("--ra", type=Path, default=THU_MUC_RA_MAC_DINH, help="thư mục ghi file")
    p.add_argument("--sep", default=",", help='ký tự ngăn cột ("," hoặc ";")')
    p.add_argument("--phay-thap-phan", action="store_true", help="ghi 8,5 thay vì 8.5")
    p.add_argument("--so-sv", type=int, default=1500, help="số sinh viên")
    p.add_argument("--nhan-lop", type=int, default=1,
                   help="nhân số lớp mỗi môn mỗi kỳ (1 ≈ 19.000 dòng, 6 ≈ 106.000 dòng)")
    p.add_argument("--seed", type=int, default=7, help="cùng seed → cùng dữ liệu")
    p.add_argument("--sach", action="store_true",
                   help="dữ liệu SẠCH: không cài ô lỗi nào (dùng để thử code không báo nhầm)")
    p.add_argument("--cai-loi", action="store_true",
                   help="cài lỗi vào CẢ 19 cột, số lượng biết trước; ghi đáp án ra dap_an_loi.json")
    return p.parse_args()


def lam_tron(x, buoc: float = 0.1):
    """Làm tròn điểm theo bước (0,1 / 0,25 / 1) và kẹp vào khoảng 0–10.

    Tham số:
        x: điểm (số hoặc mảng).
        buoc: bước làm tròn, vd 0.25 cho điểm thi chấm theo 0,25.
    Trả về:
        Điểm đã làm tròn.
    Vì sao cần: điểm thật luôn nằm trong 0–10 và có số chữ số thập phân cố định.
    """
    return np.clip(np.round(np.asarray(x) / buoc) * buoc, 0, 10)


def dinh_dang(x, phay_thap_phan: bool) -> str:
    """Đổi điểm thành chữ để ghi CSV; ô thiếu thành chuỗi rỗng.

    Tham số:
        x: điểm (có thể là NaN).
        phay_thap_phan: True thì ghi "8,5" thay vì "8.5".
    Trả về:
        Chuỗi ghi vào ô.
    Vì sao cần: file mô tả quy định ô trống = không có số liệu (khác điểm 0).
    """
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = f"{float(x):.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",") if phay_thap_phan else s


def tao_bang_diem(a: argparse.Namespace, rng: np.random.Generator) -> tuple[list[list[str]], int]:
    """Sinh các dòng điểm giả (1 dòng = 1 SV trong 1 lớp học phần).

    Tham số:
        a: tham số dòng lệnh.
        rng: bộ sinh số ngẫu nhiên.
    Trả về:
        (danh sách dòng dạng chữ, số lớp đã tạo).
    Vì sao cần: điểm được sinh từ một "năng lực ẩn" của từng SV + độ khó môn,
    nên các phương pháp "năng lực nền" và hiệu chỉnh điểm có tín hiệu thật để tìm.
    """
    so_sv = a.so_sv
    ma_sv = [f"S{i:05d}" for i in range(1, so_sv + 1)]
    khoa_sv = rng.choice([f"K{k}" for k in range(58, 68)], so_sv)
    khoa = rng.choice(["KH01", "KH02", "KH03", "KH04", "KH05", "KH-khác"], so_sv,
                      p=[.35, .25, .15, .12, .1, .03])
    nang_luc = rng.normal(0, 1, so_sv)  # năng lực "thật" – chỉ dùng để sinh điểm, không ghi ra file

    # 30 môn thường + 3 môn đồ án
    mon = [dict(ma=f"M{i:03d}", nhom=f"N{rng.integers(1, 9)}", tc=int(rng.choice([2, 3, 3, 3])),
                do_an=False, kho=rng.normal(0, 0.6)) for i in range(1, 31)]
    mon += [dict(ma=f"M{i:03d}", nhom="N8", tc=int(rng.choice([4, 6, 10])), do_an=True, kho=0.0)
            for i in range(31, 34)]

    dong: list[list[str]] = []
    so_lop = 0
    for y in range(2019, 2026):
        nam = f"{y}-{y + 1}"
        for hk in (1, 2, 3):
            for m in [m for m in mon if rng.random() < (0.55 if hk < 3 else 0.06)]:
                for _ in range(int(rng.integers(1, 4)) * a.nhan_lop):  # 1–3 lớp mỗi môn mỗi kỳ (× hệ số)
                    so_lop += 1
                    # ~7% lớp rất nhỏ (1–4 SV) để kiểm tra quy tắc ẩn nhóm < 5 người
                    si_so = int(rng.choice([rng.integers(1, 5), rng.integers(10, 45), rng.integers(45, 90)],
                                           p=[.3, .7, 0] if m["do_an"] else [.07, .7, .23]))
                    si_so = min(si_so, so_sv)
                    ep = (not m["do_an"]) and rng.random() < 0.08
                    lam_phat = rng.random() < 0.08
                    ts = (10, 40, 50) if y * 10 + hk >= 20212 else (10, 20, 70)
                    chua_co_thi = nam == "2025-2026" and hk == 2 and rng.random() < 0.5
                    for s in rng.choice(so_sv, si_so, replace=False):
                        dong.append(_mot_dong(rng, nam, hk, m, f"L{so_lop:04d}", si_so, ep, lam_phat, ts,
                                              chua_co_thi, y, ma_sv[s], khoa_sv[s], khoa[s], nang_luc[s],
                                              a.phay_thap_phan))

    if not (a.sach or a.cai_loi):  # chế độ thường: vài ô bẩn cho bản demo
        for i in rng.choice(len(dong), 5, replace=False):
            dong[i][16] = "vắng"
    return dong, so_lop


def _mot_dong(rng, nam, hk, m, ma_lop, si_so, ep, lam_phat, ts, chua_co_thi, y,
              ma_sv, khoa_sv, khoa, nl, phay) -> list[str]:
    """Sinh điểm của một SV trong một lớp và trả về một dòng CSV.

    Tham số:
        rng: bộ sinh số ngẫu nhiên; các tham số còn lại mô tả lớp (năm, kỳ, môn,
        mã lớp, sĩ số, EP, có bị cài lạm phát không, trọng số...) và SV (mã,
        khóa, khoa, năng lực ẩn nl).
    Trả về:
        Danh sách 19 ô dạng chữ theo đúng thứ tự COT_DIEM.
    Vì sao cần: gom quy tắc tính điểm vào một chỗ cho dễ đọc và dễ chỉnh.
    """
    vang = rng.random() < 0.03
    if m["do_an"]:
        thi = float(lam_tron(rng.normal(8.0 + 0.4 * nl, 0.6)))
        cc = kt1 = kt2 = kt = np.nan
        hp = thi
    else:
        nen = 6.5 + 1.0 * nl - m["kho"] + (0.5 if ep else 0)
        thi = float(lam_tron(rng.normal(nen, 1.3), 0.25))
        # Lớp bị cài lạm phát: KTTX cao hơn ~1,8 điểm và ít phân tán hơn
        kt1 = float(lam_tron(rng.normal(nen + 0.8 + (1.8 if lam_phat else 0), 0.4 if lam_phat else 0.9)))
        kt2 = float(lam_tron(rng.normal(nen + 0.8, 0.9))) if rng.random() < 0.02 else np.nan
        kt = kt1 if np.isnan(kt2) else float(lam_tron((kt1 + kt2) / 2, 0.01))
        cc = float(lam_tron(rng.normal(9, 1), 1.0))
        if vang:
            thi = 0.0
        if y == 2019 and rng.random() < 0.85:  # 2019-2020 thiếu CC/KTTX
            cc = kt1 = kt2 = kt = np.nan
        hp = thi if np.isnan(kt) else float(lam_tron((ts[0] * cc + ts[1] * kt + ts[2] * thi) / 100))
        if vang:
            hp = 0.0
        if rng.random() < 0.12 and not np.isnan(cc):  # ~12% thiếu CC
            cc = np.nan
    if chua_co_thi:
        thi = hp = np.nan
    trong_so = "" if (m["do_an"] or rng.random() < 0.36) else "/".join(map(str, ts))
    k_sv = "" if rng.random() < 0.001 else khoa_sv
    f = lambda x: dinh_dang(x, phay)  # noqa: E731
    return [nam, str(hk), m["ma"], m["nhom"], str(m["tc"]),
            "Có" if m["do_an"] else "Không", "Có" if ep else "Không",
            ma_lop, str(si_so), ma_sv, k_sv, khoa,
            f(cc), f(kt1), f(kt2), f(kt), f(thi), f(hp), trong_so]


def tao_thoi_khoa_bieu(rng: np.random.Generator) -> list[list[str]]:
    """Sinh thời khóa biểu giả (18 cột), có ~3% dòng ghi năm học một năm như dữ liệu thật.

    Tham số:
        rng: bộ sinh số ngẫu nhiên.
    Trả về:
        Danh sách dòng dạng chữ theo thứ tự COT_TKB.
    Vì sao cần: run_eda.py đối chiếu kích thước file thời khóa biểu với mô tả.
    """
    tkb = []
    for i in range(1, 301):
        y = int(rng.integers(2020, 2027))
        nam = f"{y}-{y + 1}" if rng.random() > 0.03 else str(y)
        for _ in range(2 if rng.random() < 0.07 else 1):  # một lớp có thể có nhiều dòng lịch
            tkb.append([nam, str(rng.choice(["HK01", "HK02", "HK03"])), "Hệ A", f"H{rng.integers(1, 40):03d}",
                        "3", str(rng.integers(0, 77)), f"P{i:04d}", str(rng.integers(2, 8)), "1", "3", "1", "15",
                        f"R{rng.integers(1, 50):03d}", "chuẩn", "2024-01-08", "2024-04-15", "45", "3"])
    return tkb


# Tên loại lỗi lấy chung từ eda/config.py để đáp án và bảng lỗi của báo cáo dùng
# đúng một cách gọi. (Chỉ dùng TÊN; số lượng lỗi do hàm cai_loi tự đếm khi cài.)
L_TRONG, L_DINH_DANG, L_CHU, L_NGOAI, L_LA = (
    cf.LOI_TRONG, cf.LOI_DINH_DANG, cf.LOI_CHU, cf.LOI_NGOAI, cf.LOI_LA)
L_LAN, L_SI_SO, L_TRUNG, L_TONG = cf.LOI_LAN, cf.LOI_SI_SO, cf.LOI_TRUNG, cf.LOI_TONG


def cai_loi(dong: list[list[str]], rng: np.random.Generator) -> list[dict]:
    """Cài lỗi vào CẢ 19 cột với số lượng biết trước, trả về đáp án.

    Quy tắc để lỗi này không che/kéo theo lỗi khác:
        - Mỗi lỗi nằm ở một dòng riêng (hoặc một lớp riêng), không dòng nào bị
          cài hai lỗi.
        - Cột cấp lớp (Năm học, Học kỳ, Mã môn, Mã lớp, Sĩ số) bị sửa cho CẢ LỚP –
          nếu chỉ sửa một dòng, lớp đó sẽ "lẫn nhiều năm/kỳ/môn" và sinh thêm lỗi
          ngoài ý muốn.
        - Mỗi loại lỗi có số lượng KHÁC NHAU → nếu code đếm nhầm sang cột khác
          thì con số sẽ lộ ra.
    Tham số:
        dong: các dòng dữ liệu sạch (bị sửa trực tiếp).
        rng: bộ sinh số ngẫu nhiên.
    Trả về:
        Đáp án: danh sách {cot, loai, don_vi, so_luong}. Do chính hàm này ghi lại
        khi cài – không dùng code EDA để tính, nên không phải "code tự chấm mình".
    Vì sao cần: kiểm tra code bắt lỗi có bắt đủ, đúng cột, không bỏ sót không.
    """
    vi_tri = {c: i for i, c in enumerate(COT_DIEM)}
    i_lop, i_sv, i_nam = vi_tri["Mã lớp học phần"], vi_tri["Mã SV"], vi_tri["Năm học"]
    lop: dict[str, list[int]] = {}
    for i, d in enumerate(dong):
        lop.setdefault(d[i_lop], []).append(i)
    lop_da_dung: set[str] = set()   # lớp đã bị cài lỗi (không cài thêm lỗi khác vào)
    dong_da_dung: set[int] = set()
    so_da_dung: set[int] = set()    # số lượng đã dùng → mỗi loại lỗi một số khác nhau
    dap_an: list[dict] = []

    def so_moi() -> int:
        """Số nguyên dương nhỏ nhất chưa dùng làm số lượng lỗi."""
        k = 1
        while k in so_da_dung:
            k += 1
        so_da_dung.add(k)
        return k

    def chon_lop(co_toi_thieu: int = 2, kich_thuoc_moi: bool = False) -> str:
        """Chọn một lớp thường chưa bị đụng tới (tùy chọn: sĩ số chưa dùng làm số lượng)."""
        ung_vien = [m for m, ds in lop.items()
                    if m not in lop_da_dung and len(ds) >= co_toi_thieu
                    and dong[ds[0]][vi_tri["Là đồ án/thực tập/khóa luận"]] == "Không"
                    and not (set(ds) & dong_da_dung)
                    and (not kich_thuoc_moi or len(ds) not in so_da_dung)]
        m = ung_vien[int(rng.integers(len(ung_vien)))]
        lop_da_dung.add(m)
        return m

    def ghi(cot: str, loai: str, so: int, don_vi: str = "ô") -> None:
        dap_an.append({"cot": cot, "loai": loai, "don_vi": don_vi, "so_luong": so})

    # 1) Lỗi đếm theo LỚP
    k = so_moi()
    for _ in range(k):  # một dòng của lớp ghi năm học khác (vẫn đúng định dạng)
        ds = lop[chon_lop()]
        y = int(dong[ds[0]][i_nam][:4])
        y2 = y + 1 if y < 2025 else y - 1
        dong[ds[0]][i_nam] = f"{y2}-{y2 + 1}"
    ghi("Mã lớp học phần", L_LAN, k, "lớp")
    k = so_moi()
    for _ in range(k):  # sĩ số ghi lệch số dòng thật (+7)
        ds = lop[chon_lop()]
        for i in ds:
            dong[i][vi_tri["Sĩ số lớp (trong dữ liệu)"]] = str(len(ds) + 7)
    ghi("Sĩ số lớp (trong dữ liệu)", L_SI_SO, k, "lớp")

    # 2) Lỗi cài cho CẢ LỚP (đếm theo ô = sĩ số của lớp đó)
    ca_lop = [
        ("Năm học", L_DINH_DANG, lambda v: v.replace("-", "/")),   # 2021/2022
        ("Năm học", L_TRONG, lambda v: ""),
        ("Học kỳ", L_CHU, lambda v: "hai"),
        ("Học kỳ", L_NGOAI, lambda v: "4"),
        ("Mã môn", L_DINH_DANG, lambda v: "M1"),
        ("Mã môn", L_TRONG, lambda v: ""),
        ("Mã lớp học phần", L_DINH_DANG, lambda v: "L12"),
        ("Sĩ số lớp (trong dữ liệu)", L_CHU, lambda v: "ba mươi"),
    ]
    # Giữ trước các số nhỏ cho lỗi theo dòng ở bước 3, để sĩ số lớp không trùng chúng.
    so_theo_dong = [so_moi() for _ in range(25)]
    for cot, loai, doi in ca_lop:
        ds = lop[chon_lop(kich_thuoc_moi=True)]
        so_da_dung.add(len(ds))
        for i in ds:
            dong[i][vi_tri[cot]] = doi(dong[i][vi_tri[cot]])
        ghi(cot, loai, len(ds))

    # 3) Lỗi theo DÒNG
    def chon_dong(so: int, moi_lop_mot_dong: bool = False) -> list[int]:
        """Chọn `so` dòng chưa dùng, thuộc lớp chưa bị cài lỗi cả lớp."""
        ung_vien = [i for m, ds in lop.items() if m not in lop_da_dung
                    for i in ds if i not in dong_da_dung]
        if moi_lop_mot_dong:  # vd Mã SV trống: 2 ô trống cùng lớp sẽ bị coi là "trùng"
            ra = []
            for _ in range(so):
                ds = lop[chon_lop(co_toi_thieu=1)]
                ra.append(ds[0])
        else:
            ra = [int(i) for i in rng.choice(ung_vien, so, replace=False)]
        dong_da_dung.update(ra)
        return ra

    theo_dong = [
        ("Nhóm môn", L_DINH_DANG, "N9"),
        ("Số TC", L_CHU, "ba"),
        ("Số TC", L_NGOAI, "15"),
        ("Là đồ án/thực tập/khóa luận", L_LA, "Có lẽ"),
        ("Lớp mang mã EP", L_LA, "?"),
        ("Mã SV", L_DINH_DANG, None),   # "SV-1", "SV-2"... (khác nhau để không tạo trùng)
        ("Mã SV", L_TRONG, ""),
        ("Khóa SV", L_DINH_DANG, "K99"),
        ("Khoa của SV", L_DINH_DANG, "KH1"),
        ("Khoa của SV", L_TRONG, ""),
        ("Cơ cấu trọng số suy ra (CC/KTTX/Thi, %)", L_DINH_DANG, "10/20"),
        ("Cơ cấu trọng số suy ra (CC/KTTX/Thi, %)", L_TONG, "10/20/60"),
    ]
    for cot in ["CC", "KTTX1", "KTTX2", "KTTX (TB)", "Thi", "Điểm HP (thang 10)"]:
        theo_dong += [(cot, L_CHU, "vắng"), (cot, L_NGOAI, None)]  # None: xen kẽ 11 và -2
    theo_dong.append(("Mã SV", L_TRUNG, None))
    assert len(theo_dong) == len(so_theo_dong)

    for (cot, loai, gia_tri), k in zip(theo_dong, so_theo_dong):
        if loai == L_TRUNG:  # k cặp, mỗi cặp ở một lớp: dòng A lấy Mã SV của dòng B cùng lớp
            for _ in range(k):
                ds = lop[chon_lop()]
                a_, b_ = ds[0], ds[1]
                dong[a_][i_sv] = dong[b_][i_sv]
                dong_da_dung.update([a_, b_])
            ghi(cot, loai, k, "dòng thừa")
            continue
        cac_dong = chon_dong(k, moi_lop_mot_dong=(cot == "Mã SV" and loai == L_TRONG))
        for j, i in enumerate(cac_dong):
            if cot == "Mã SV" and loai == L_DINH_DANG:
                dong[i][vi_tri[cot]] = f"SV-{j + 1}"
            elif loai == L_NGOAI and gia_tri is None:
                dong[i][vi_tri[cot]] = "11" if j % 2 == 0 else "-2"
            else:
                dong[i][vi_tri[cot]] = gia_tri
        ghi(cot, loai, k)
    return dap_an


def ghi_csv(duong_dan: Path, cot: list[str], dong: list[list[str]], sep: str) -> None:
    """Ghi CSV mã hóa UTF-8 có BOM, giống file của BTC.

    Tham số:
        duong_dan: file cần ghi.
        cot: tên cột.
        dong: các dòng dữ liệu.
        sep: ký tự ngăn cột.
    Vì sao cần: thử đúng kiểu file thật để phần đọc dữ liệu được kiểm tra luôn.
    """
    with open(duong_dan, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=sep)
        w.writerow(cot)
        w.writerows(dong)


def main() -> None:
    """Tạo hai file giả trong thư mục ra và in tóm tắt."""
    a = doc_tham_so()
    rng = np.random.default_rng(a.seed)
    a.ra.mkdir(parents=True, exist_ok=True)
    dong, so_lop = tao_bang_diem(a, rng)
    tkb = tao_thoi_khoa_bieu(rng)
    file_dap_an = a.ra / "dap_an_loi.json"
    if a.cai_loi:
        dap_an = cai_loi(dong, rng)
        file_dap_an.write_text(json.dumps(dap_an, ensure_ascii=False, indent=1), encoding="utf-8")
    elif file_dap_an.exists():
        file_dap_an.unlink()  # xóa đáp án cũ để không bị chấm nhầm với dữ liệu mới
    ghi_csv(a.ra / "Du_lieu.csv", COT_DIEM, dong, a.sep)
    ghi_csv(a.ra / "Thoi_khoa_bieu.csv", COT_TKB, tkb, a.sep)
    print(f"Đã tạo {len(dong):,} dòng điểm giả, {so_lop:,} lớp, {len(tkb)} dòng TKB giả tại {a.ra}"
          + (f"; đã cài {sum(d['so_luong'] for d in dap_an)} lỗi" if a.cai_loi else ""))


if __name__ == "__main__":
    main()
