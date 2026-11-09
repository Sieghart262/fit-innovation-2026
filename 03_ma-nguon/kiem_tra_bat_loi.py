"""Kiểm tra code EDA có đọc được dữ liệu và bắt được hết lỗi không (dùng dữ liệu GIẢ).

Bước 1 – Dữ liệu SẠCH (không cài lỗi):
    code phải đọc đủ dòng/cột, chạy hết run_eda.py, và báo 0 lỗi ở mọi kiểm tra.
    Báo lỗi trên dữ liệu sạch = "báo nhầm".
Bước 2 – Dữ liệu CÀI LỖI (cả 19 cột, mỗi loại lỗi một số lượng khác nhau):
    so từng con số code báo với đáp án do tao_du_lieu_gia.py ghi lại lúc cài.
        ✅            bắt đủ, đúng cột
        ❌ bắt thiếu   code báo ít hơn số đã cài
        ❌ bắt dư      code báo nhiều hơn (đếm nhầm hoặc đếm trùng)
        ❌ chưa có kiểm tra   code không hề kiểm tra loại lỗi này

Cách chạy (từ thư mục gốc dự án):
    .venv\\Scripts\\python.exe -X utf8 03_ma-nguon\\kiem_tra_bat_loi.py

Không đụng dữ liệu thật: mọi file giả nằm trong một thư mục tạm, tự xóa khi xong
(thêm --giu-lai <thư mục> nếu muốn giữ lại để xem).
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

THU_MUC_MA = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC_MA))

import tao_du_lieu_gia as tdg  # noqa: E402  (tên loại lỗi dùng chung với bộ cài lỗi)
from eda import config as cf, quality  # noqa: E402
from eda.load import doc_du_lieu_diem  # noqa: E402


def ket_qua_code(bang, thong_tin: dict) -> tuple[dict, dict]:
    """Lấy các con số lỗi mà code EDA hiện tại báo (đúng các hàm báo cáo đang dùng).

    Tham số:
        bang, thong_tin: kết quả của load.doc_du_lieu_diem().
    Trả về:
        (kq, ghi_chu):
            kq      = {(cột, loại lỗi): số lỗi code báo} – chỉ gồm loại lỗi code CÓ kiểm tra.
            ghi_chu = các con số code báo nhưng không gắn được với một cột cụ thể.
    Vì sao cần: chấm đúng bảng báo cáo sẽ in ra (mục 1.2), không tự tính thêm.
    """
    loi = quality.kiem_tra_loi_theo_cot(bang, thong_tin)  # đúng bảng mục 1.2 của báo cáo
    kq = {(d.cot, d.loai_loi): int(d.so_luong) for d in loi.itertuples()}
    return kq, {}


def chay(lenh: list[str]) -> subprocess.CompletedProcess:
    """Chạy một lệnh Python con, lấy kết quả dạng chữ UTF-8."""
    return subprocess.run([sys.executable, "-X", "utf8", *lenh], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def dem_dong_csv(duong_dan: Path) -> tuple[int, int]:
    """Đếm số dòng dữ liệu và số cột bằng module csv chuẩn (độc lập với pandas)."""
    with open(duong_dan, encoding="utf-8-sig", newline="") as f:
        doc = csv.reader(f)
        tieu_de = next(doc)
        return sum(1 for _ in doc), len(tieu_de)


def in_bang(dong: list[list[str]], tieu_de: list[str]) -> None:
    """In bảng thẳng cột ra màn hình."""
    rong = [max(len(str(x)) for x in cot) for cot in zip(tieu_de, *dong)]
    in_dong = lambda d: print("  " + " │ ".join(str(x).ljust(w) for x, w in zip(d, rong)))  # noqa: E731
    in_dong(tieu_de)
    print("  " + "─┼─".join("─" * w for w in rong))
    for d in dong:
        in_dong(d)


def chuan_bi(thu_muc: Path, che_do: str) -> tuple[Path, list[dict], bool]:
    """Tạo dữ liệu giả, chạy run_eda.py trên đó, kiểm tra code đọc được dữ liệu.

    Tham số:
        thu_muc: thư mục chứa dữ liệu giả của bước này.
        che_do: "--sach" hoặc "--cai-loi".
    Trả về:
        (file Du_lieu.csv, đáp án lỗi (rỗng nếu sạch), True nếu mọi kiểm tra đọc đều đạt).
    """
    tao = chay([str(THU_MUC_MA / "tao_du_lieu_gia.py"), "--ra", str(thu_muc), che_do])
    if tao.returncode != 0:
        sys.exit(f"Lỗi khi tạo dữ liệu giả:\n{tao.stderr}")
    file_dl = thu_muc / "Du_lieu.csv"
    file_da = thu_muc / "dap_an_loi.json"
    dap_an = json.loads(file_da.read_text(encoding="utf-8")) if file_da.exists() else []

    so_dong, so_cot = dem_dong_csv(file_dl)
    bang, thong_tin = doc_du_lieu_diem(file_dl)
    eda = chay([str(THU_MUC_MA / "run_eda.py"), "--du-lieu", str(file_dl),
                "--tkb", str(thu_muc / "Thoi_khoa_bieu.csv"),
                "--bao-cao", str(thu_muc / "bao-cao" / "02-ket-qua-eda.md")])
    dong_cuoi = (eda.stdout.strip().splitlines() or [""])[-1]
    loi_eda = (eda.stderr.strip().splitlines() or [""])[-1]

    kiem_tra = [
        ["Đọc đủ số dòng", f"{so_dong:,}", f"{len(bang):,}", so_dong == len(bang)],
        ["Đọc đủ số cột", so_cot, thong_tin["so_cot_goc"], so_cot == thong_tin["so_cot_goc"]],
        ["run_eda.py chạy hết, ghi báo cáo", "mã thoát 0", f"mã thoát {eda.returncode}",
         eda.returncode == 0],
    ]
    print("\n  Đọc dữ liệu:")
    in_bang([[a, b, c, "✅" if ok else "❌"] for a, b, c, ok in kiem_tra],
            ["Kiểm tra", "Mong đợi", "Thực tế", "Kết quả"])
    if eda.returncode != 0:
        print(f"  run_eda.py dừng: {dong_cuoi or loi_eda}")
    return file_dl, dap_an, all(ok for *_, ok in kiem_tra)


def cham(dap_an: list[dict], kq: dict) -> list[list[str]]:
    """So từng (cột, loại lỗi) giữa đáp án và code, theo thứ tự 19 cột.

    Tham số:
        dap_an: danh sách lỗi đã cài (rỗng ở bước 1).
        kq: {(cột, loại lỗi): số code báo}.
    Trả về:
        Các dòng bảng chấm: cột | loại lỗi | đơn vị | đã cài | code báo | kết quả.
    """
    da_cai = {(d["cot"], d["loai"]): d for d in dap_an}
    dong = []
    for cot in cf.COT_BAT_BUOC:
        loai_cua_cot = [l for (c, l) in da_cai if c == cot] + \
                       [l for (c, l) in kq if c == cot and (c, l) not in da_cai]
        if not loai_cua_cot:
            dong.append([cot, "—", "", "", "", "⚠️ chưa có kiểm tra nào cho cột này"])
            continue
        for loai in loai_cua_cot:
            d = da_cai.get((cot, loai))
            cai = d["so_luong"] if d else 0
            don_vi = d["don_vi"] if d else ""
            bao = kq.get((cot, loai))
            if bao is None:
                kq_chu = "❌ chưa có kiểm tra"
            elif bao == cai:
                kq_chu = "✅"
            elif not dap_an:
                kq_chu = "❌ báo nhầm"
            else:
                kq_chu = "❌ bắt thiếu" if bao < cai else "❌ bắt dư"
            dong.append([cot, loai, don_vi, cai, "–" if bao is None else bao, kq_chu])
    return dong


def mot_buoc(ten: str, thu_muc: Path, che_do: str) -> bool:
    """Chạy trọn một bước (chuẩn bị dữ liệu, đọc, chấm, in kết quả). Trả về True nếu đạt hết."""
    print(f"\n{'=' * 78}\n{ten}\n{'=' * 78}")
    file_dl, dap_an, doc_ok = chuan_bi(thu_muc, che_do)
    bang, thong_tin = doc_du_lieu_diem(file_dl)
    kq, ghi_chu = ket_qua_code(bang, thong_tin)
    dong = cham(dap_an, kq)
    print("\n  Bắt lỗi theo từng cột:")
    in_bang(dong, ["Cột", "Loại lỗi", "Đơn vị", "Đã cài", "Code báo", "Kết quả"])
    for k, v in ghi_chu.items():
        print(f"  Ghi chú – {k}: {v}")
    dat = sum(d[-1] == "✅" for d in dong)
    can_cham = sum(d[-1] != "⚠️ chưa có kiểm tra nào cho cột này" for d in dong)
    cot_khong_kt = sum(d[-1].startswith("⚠️") for d in dong)
    print(f"\n  TÓM TẮT: {dat}/{can_cham} dòng ✅"
          + (f"; {cot_khong_kt} cột chưa có kiểm tra nào" if cot_khong_kt else ""))
    co_loi = any(d[-1].startswith("❌") for d in dong)
    if che_do == "--sach":  # bước 1 chỉ xét: đọc được + không báo nhầm
        return doc_ok and not co_loi
    return doc_ok and not co_loi and cot_khong_kt == 0


def main() -> None:
    """Chạy bước 1 (dữ liệu sạch) và bước 2 (dữ liệu cài lỗi)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Kiểm tra code bắt lỗi bằng dữ liệu giả")
    p.add_argument("--giu-lai", type=Path, help="giữ dữ liệu giả ở thư mục này thay vì xóa")
    a = p.parse_args()

    with tempfile.TemporaryDirectory() as tam:
        goc = a.giu_lai or Path(tam)
        ok1 = mot_buoc("BƯỚC 1 – Dữ liệu SẠCH: code phải đọc được và báo 0 lỗi", goc / "sach", "--sach")
        ok2 = mot_buoc("BƯỚC 2 – Dữ liệu CÀI LỖI (cả 19 cột): code phải bắt đúng từng con số",
                       goc / "cai_loi", "--cai-loi")
    print(f"\nKẾT LUẬN: bước 1 {'✅' if ok1 else '❌'} · bước 2 {'✅' if ok2 else '❌'}")
    sys.exit(0 if ok1 and ok2 else 1)


if __name__ == "__main__":
    main()
