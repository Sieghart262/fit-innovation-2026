"""Quản lý kết quả phân tích: kết quả đang dùng, reset, phân tích file mới (riêng hoặc gộp) và lịch sử.

Cách tổ chức thư mục (đều nằm trong 01_du-lieu/ nên không lên GitHub):
    ket-qua/                 kết quả ĐANG DÙNG – dashboard hiển thị thư mục này cho mọi người
        gp1/ gp2/ gp3/       kết quả 3 giải pháp (do ghi_tat_ca ghi)
        thong_tin.json       tên dữ liệu, thời điểm, cách tạo, vài con số tóm tắt
        du_lieu_dau_vao.csv  file điểm đã dùng để phân tích (khi có) – cần cho lựa chọn "gộp"
    lich-su-phan-tich/<id>/  mỗi lần phân tích là một bản sao đầy đủ như trên

Quy tắc (quyết định của đội):
    - Reset: kết quả đang dùng được CẤT vào lịch sử rồi mới xóa khỏi ket-qua/ → dashboard trống.
    - Phân tích file mới: chọn "phân tích riêng" (thay dữ liệu đang dùng) hoặc "gộp thêm" (ghép với
      file điểm đang dùng rồi phân tích lại). Kết quả mới thay cho mọi người xem dashboard.
    - Mọi lần phân tích đều được lưu vào lịch sử. Phân tích lỗi thì không đụng tới kết quả đang dùng.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import threading
import time
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd

from eda import config as cf
from eda.load import LoiDuLieu, doc_csv, doc_du_lieu_diem, kiem_tra_ten_cot
from gp1 import cau_hinh as ch1, xuat as x1
from gp1.du_lieu import chuan_bi
from gp2 import cau_hinh as ch2, xuat as x2
from gp3 import cau_hinh as ch3, xuat as x3
from gp3.quy_trinh import chay_gp3

THU_MUC_KET_QUA = cf.THU_MUC_GOC / "01_du-lieu" / "ket-qua"
TEN_THONG_TIN = "thong_tin.json"
TEN_DU_LIEU = "du_lieu_dau_vao.csv"
THU_MUC_CON = ["gp1", "gp2", "gp3"]

# Chỉ cho một lần ghi kết quả (phân tích file mới / reset) chạy tại một thời điểm, kể cả khi
# nhiều người cùng mở dashboard: hai lần ghi chồng lên nhau sẽ xóa/chép đè file của nhau.
_KHOA_GHI = threading.Lock()


def _thu_lai(ham, *args, so_lan: int = 20, cho: float = 0.25, **kwargs):
    """Gọi ham(*args), thử lại khi Windows báo file đang bị khóa (PermissionError).

    Tham số:
        ham: thao tác file (đổi tên, xóa, chép...); so_lan: số lần thử tối đa; cho: giây chờ giữa hai lần.
    Trả về:
        Kết quả của ham.
    Vì sao cần: trên Windows, file vừa ghi thường bị phần mềm diệt virus/tìm kiếm, hoặc một người
    khác đang mở dashboard, giữ trong chốc lát. Xóa hay đổi tên đúng lúc đó sẽ lỗi PermissionError
    dù dữ liệu không sai; chờ một chút rồi làm lại là được (trước đây người dùng phải tự bấm lại).
    """
    for lan in range(so_lan):
        try:
            return ham(*args, **kwargs)
        except PermissionError:
            if lan == so_lan - 1:
                raise
            time.sleep(cho)


def _xoa_thu_muc(p: Path) -> None:
    """Xóa hẳn một thư mục (thử lại khi bị khóa). Không lặng lẽ để sót file như ignore_errors."""
    if p.exists():
        _thu_lai(shutil.rmtree, p)

CACH_LENH = "Chạy lệnh run_gp3.py"
CACH_RIENG = "Tải file lên – phân tích riêng"
CACH_GOP = "Tải file lên – gộp với dữ liệu đang dùng"


def thu_muc_lich_su(ket_qua: Path) -> Path:
    """Thư mục lịch sử nằm cạnh thư mục kết quả đang dùng (vd 01_du-lieu/lich-su-phan-tich)."""
    return ket_qua.parent / "lich-su-phan-tich"


def ghi_tat_ca(kq: dict, kc: dict | None, cfg1, cfg2, cfg3, goc: Path) -> None:
    """Ghi kết quả của cả 3 giải pháp vào goc/gp1, goc/gp2, goc/gp3.

    Tham số:
        kq: kết quả chay_gp3();
        kc: bảng kiểm chứng của từng giải pháp {"gp1": ..., "gp2": ..., "gp3": ...}, hoặc None;
        cfg1-3: cấu hình; goc: thư mục gốc.
    Vì sao cần: dashboard đọc đủ 3 thư mục; dùng chung cho dòng lệnh (run_gp3.py) và cho phần
    tải file mới trên dashboard, nên kết quả hai nơi luôn cùng một dạng.
    """
    kc = kc or {}
    t1, t2, t3 = goc / "gp1", goc / "gp2", goc / "gp3"
    hs, (xh, doc) = x1.diem_nong(kq["kq_gp1"]), x1.xu_huong(kq["kq_gp1"])
    h1 = x1.ve_bieu_do(kq["kq_gp1"], kq["diem_lop"], kq["ds_moc"], xh, t1 / "charts")
    x1.ghi_ket_qua(kq["kq_gp1"], hs, xh, doc, kc.get("gp1"), cfg1, t1)
    x1.ghi_bao_cao(kq["kq_gp1"], hs, doc, kc.get("gp1"), kq["b"], h1, t1)
    h2 = x2.ve_bieu_do(kq["sv"], kq["lop"], t2 / "charts")
    x2.ghi_ket_qua(kq, kc.get("gp2"), cfg2, t2)
    x2.ghi_bao_cao(kq, kc.get("gp2"), h2, t2)
    h3 = x3.ve_bieu_do(kq["phan_loai"], t3 / "charts")
    x3.ghi_ket_qua(kq, kc.get("gp3"), cfg3, t3)
    x3.ghi_bao_cao(kq, kc.get("gp3"), h3, t3)


def tom_tat_kq(kq: dict) -> dict:
    """Vài con số tóm tắt của một lần phân tích (để hiện trong lịch sử)."""
    sv = kq["phan_loai"]
    return {"so_sv": int(sv["TCI"].notna().sum()), "so_lop": int(len(kq["kq_gp1"])),
            "so_lop_bat_thuong": int(kq["kq_gp1"]["anomaly_type"].isin(ch1.NHAN_BAT_THUONG).sum()),
            "so_lop_hieu_chinh": int(kq["lop"]["dich_chuyen"].ne(0).sum()),
            "so_sv_doi_muc": int(sv["doi_muc"].ne("Giữ nguyên").sum())}


def tom_tat_tu_file(goc: Path) -> dict:
    """Đếm lại các con số tóm tắt từ file kết quả (dùng cho kết quả cũ chưa có thong_tin.json)."""
    try:
        lop = pd.read_csv(goc / "gp1" / "chi_so_chi_tiet.csv", encoding="utf-8-sig", usecols=["anomaly_type"])
        hc = pd.read_csv(goc / "gp2" / "hieu_chinh_theo_lop.csv", encoding="utf-8-sig")
        sv = pd.read_csv(goc / "gp3" / "phan_loai_sinh_vien.csv", encoding="utf-8-sig", usecols=["TCI", "Thay đổi mức"])
    except (OSError, ValueError):
        return {}
    return {"so_sv": int(sv["TCI"].notna().sum()), "so_lop": int(len(lop)),
            "so_lop_bat_thuong": int(lop["anomaly_type"].isin(ch1.NHAN_BAT_THUONG).sum()),
            "so_lop_hieu_chinh": int(hc[hc.columns[-1]].ne(0).sum()),
            "so_sv_doi_muc": int(sv["Thay đổi mức"].ne("Giữ nguyên").sum())}


def ghi_thong_tin(goc: Path, ten: str, cach_tao: str, file_du_lieu: str, tom_tat: dict) -> dict:
    """Ghi thong_tin.json cho một bộ kết quả.

    Tham số:
        goc: thư mục kết quả; ten: tên dễ đọc của dữ liệu (thường là tên file);
        cach_tao: một trong CACH_LENH / CACH_RIENG / CACH_GOP;
        file_du_lieu: TEN_DU_LIEU nếu file điểm nằm ngay trong thư mục, hoặc đường dẫn tuyệt đối;
        tom_tat: kết quả tom_tat_kq().
    Trả về:
        dict thông tin đã ghi (có "id" duy nhất theo thời điểm).
    """
    bay_gio = datetime.now()
    tt = {"id": bay_gio.strftime("%Y%m%d-%H%M%S-%f"), "ten": ten, "thoi_gian": bay_gio.isoformat(timespec="seconds"),
          "cach_tao": cach_tao, "file_du_lieu": file_du_lieu, **tom_tat}
    goc.mkdir(parents=True, exist_ok=True)
    (goc / TEN_THONG_TIN).write_text(json.dumps(tt, ensure_ascii=False, indent=1), encoding="utf-8")
    return tt


def doc_thong_tin(goc: Path) -> dict | None:
    """Đọc thong_tin.json; trả về None nếu chưa có (vd kết quả tạo bằng phiên bản cũ)."""
    p = goc / TEN_THONG_TIN
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    except (json.JSONDecodeError, OSError):
        return None


def co_ket_qua(goc: Path) -> bool:
    """True nếu thư mục có đủ kết quả để dashboard hiển thị."""
    return (goc / "gp3" / "phan_loai_sinh_vien.csv").exists()


def file_du_lieu(goc: Path) -> Path | None:
    """File điểm đã dùng để tạo bộ kết quả này (cần cho lựa chọn "gộp"); None nếu không xác định được."""
    tt = doc_thong_tin(goc)
    if tt and tt.get("file_du_lieu"):
        p = goc / tt["file_du_lieu"] if tt["file_du_lieu"] == TEN_DU_LIEU else Path(tt["file_du_lieu"])
        return p if p.exists() else None
    if (goc / TEN_DU_LIEU).exists():
        return goc / TEN_DU_LIEU
    return None


def luu_lich_su(goc: Path, lich_su: Path) -> Path | None:
    """Sao chép bộ kết quả đang có vào lịch sử (nếu chưa có ở đó).

    Tham số:
        goc: thư mục kết quả đang dùng; lich_su: thư mục lịch sử.
    Trả về:
        Thư mục của mục lịch sử, hoặc None nếu không có kết quả nào để lưu.
    Vì sao cần: reset hay phân tích file mới đều không được làm mất kết quả cũ. Mục lịch sử
    mang theo cả file điểm đầu vào nên tự đứng được một mình.
    """
    if not co_ket_qua(goc):
        return None
    tt = doc_thong_tin(goc)
    if tt is None:  # kết quả cũ chưa có thông tin → tạo thông tin từ thời điểm sửa file
        mtime = datetime.fromtimestamp((goc / "gp3" / "phan_loai_sinh_vien.csv").stat().st_mtime)
        tt = {"id": mtime.strftime("%Y%m%d-%H%M%S-000000"), "ten": "Kết quả phân tích trước đây",
              "thoi_gian": mtime.isoformat(timespec="seconds"), "cach_tao": CACH_LENH, "file_du_lieu": "",
              **tom_tat_tu_file(goc)}
    dich = lich_su / tt["id"]
    if (dich / TEN_THONG_TIN).exists():
        return dich
    tam = lich_su / f".{tt['id']}.dang-luu"
    _xoa_thu_muc(tam)
    for con in THU_MUC_CON:
        if (goc / con).exists():
            _thu_lai(shutil.copytree, goc / con, tam / con, dirs_exist_ok=True)
    nguon = file_du_lieu(goc)
    if nguon is not None:
        _thu_lai(shutil.copy2, nguon, tam / TEN_DU_LIEU)
    tt = {**tt, "file_du_lieu": TEN_DU_LIEU if nguon is not None else ""}
    (tam / TEN_THONG_TIN).write_text(json.dumps(tt, ensure_ascii=False, indent=1), encoding="utf-8")
    _thu_lai(tam.rename, dich)  # đổi tên sau cùng: mục lịch sử chỉ xuất hiện khi đã sao chép xong
    return dich


def xoa_ket_qua(goc: Path) -> None:
    """Xóa kết quả đang dùng (chỉ các thư mục/tệp do hệ thống tạo, không đụng tệp khác)."""
    for con in THU_MUC_CON:
        _xoa_thu_muc(goc / con)
    for ten in (TEN_THONG_TIN, TEN_DU_LIEU):
        _thu_lai((goc / ten).unlink, missing_ok=True)


def reset(goc: Path, lich_su: Path) -> Path | None:
    """Cất kết quả đang dùng vào lịch sử rồi xóa khỏi dashboard.

    Trả về:
        Thư mục mục lịch sử vừa lưu (None nếu dashboard vốn đã trống).
    """
    with _KHOA_GHI:
        da_luu = luu_lich_su(goc, lich_su)
        xoa_ket_qua(goc)
    return da_luu


def gop_file(cu: Path, moi: Path, ra: Path) -> dict:
    """Ghép file điểm đang dùng với file mới thành một file.

    Tham số:
        cu: file điểm đang dùng; moi: file mới tải lên; ra: nơi ghi file đã ghép.
    Trả về:
        dict: so_dong_cu, so_dong_moi, so_dong_thay (dòng cũ bị thay vì file mới có cùng lớp + SV),
        so_dong_sau_gop.
    Vì sao cần: nhà trường muốn phân tích thêm một nhóm dữ liệu cùng với dữ liệu hiện có. Nếu cùng
    một SV trong cùng một lớp xuất hiện ở cả hai file thì lấy dòng của file mới (coi là bản cập nhật).
    """
    a, b = doc_csv(cu), doc_csv(moi)
    kiem_tra_ten_cot(a, cf.COT_BAT_BUOC, cu.name)
    kiem_tra_ten_cot(b, cf.COT_BAT_BUOC, moi.name)
    a, b = a[cf.COT_BAT_BUOC], b[cf.COT_BAT_BUOC]
    gop = pd.concat([a, b], ignore_index=True)
    khoa = [cf.COT_MA_LOP, cf.COT_MA_SV]
    co_khoa = gop[khoa].notna().all(axis=1)
    trung = co_khoa & gop.duplicated(khoa, keep="last")
    gop = gop[~trung]
    gop.to_csv(ra, index=False, encoding="utf-8-sig")
    return {"so_dong_cu": len(a), "so_dong_moi": len(b), "so_dong_thay": int(trung.sum()), "so_dong_sau_gop": len(gop)}


def phan_tich_moi(noi_dung: bytes, ten_file: str, gop: bool, goc: Path, lich_su: Path) -> dict:
    """Phân tích một file điểm mới và đưa kết quả lên dashboard (thay kết quả đang dùng).

    Các bước:
        1. Ghi file vào thư mục tạm; nếu "gộp" thì ghép với file điểm đang dùng.
        2. Chạy Giải pháp 1 → 3 và ghi kết quả vào thư mục tạm.
        3. Chỉ khi mọi bước trên thành công: cất kết quả đang dùng vào lịch sử, thay bằng kết quả mới,
           rồi lưu luôn kết quả mới vào lịch sử.
    Tham số:
        noi_dung: nội dung file CSV; ten_file: tên file; gop: True = gộp với dữ liệu đang dùng;
        goc: thư mục kết quả đang dùng; lich_su: thư mục lịch sử.
    Trả về:
        dict thông tin của lần phân tích (thong_tin.json) cộng số dòng khi gộp.
    Lỗi:
        LoiDuLieu khi file không đúng cấu trúc, hoặc chọn "gộp" khi chưa có dữ liệu đang dùng.
    """
    cu = file_du_lieu(goc) if gop else None
    if gop and cu is None:
        raise LoiDuLieu("Chưa có dữ liệu đang dùng (hoặc không tìm thấy file điểm của dữ liệu đang dùng) "
                        "nên không gộp được. Hãy chọn \"Phân tích riêng\".")
    # ignore_cleanup_errors: thư mục tạm bị khóa lúc dọn dẹp thì bỏ qua, không làm hỏng lần phân tích đã xong
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
        tam = Path(t)
        moi = tam / "file_moi.csv"
        moi.write_bytes(noi_dung)
        dau_vao = tam / TEN_DU_LIEU
        thong_tin_gop = {}
        if gop:
            thong_tin_gop = gop_file(cu, moi, dau_vao)
            tt_cu = doc_thong_tin(goc) or {}
            ten = f"{tt_cu.get('ten', 'Dữ liệu đang dùng')} + {ten_file}"
        else:
            shutil.copy2(moi, dau_vao)
            ten = ten_file
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                bang = doc_du_lieu_diem(dau_vao)[0]
            except LoiDuLieu as loi:  # báo bằng tên file người dùng tải lên, không phải tên file tạm
                raise LoiDuLieu(str(loi).replace(TEN_DU_LIEU, ten_file)) from None
            kq = chay_gp3(chuan_bi(bang))
            ra = tam / "ket-qua"
            ghi_tat_ca(kq, None, ch1.CauHinh(), ch2.CauHinhGP2(), ch3.CauHinhGP3(), ra)
        shutil.copy2(dau_vao, ra / TEN_DU_LIEU)
        tt = ghi_thong_tin(ra, ten, CACH_GOP if gop else CACH_RIENG, TEN_DU_LIEU, tom_tat_kq(kq))

        with _KHOA_GHI:
            luu_lich_su(goc, lich_su)        # cất kết quả đang dùng (nếu chưa có trong lịch sử)
            xoa_ket_qua(goc)
            goc.mkdir(parents=True, exist_ok=True)
            # Chép (không "move"): chép làm lại được an toàn khi bị khóa giữa chừng; thư mục tạm tự dọn sau
            for p in ra.iterdir():
                if p.is_dir():
                    _thu_lai(shutil.copytree, p, goc / p.name, dirs_exist_ok=True)
                else:
                    _thu_lai(shutil.copy2, p, goc / p.name)
            luu_lich_su(goc, lich_su)        # lưu luôn kết quả mới vào lịch sử
    return {**tt, **thong_tin_gop}


def danh_sach_lich_su(lich_su: Path) -> list[tuple[Path, dict]]:
    """Các mục lịch sử (mới nhất trước): [(thư mục, thông tin)]."""
    if not lich_su.exists():
        return []
    muc = [(p, doc_thong_tin(p)) for p in lich_su.iterdir() if p.is_dir() and not p.name.startswith(".")]
    muc = [(p, tt) for p, tt in muc if tt and co_ket_qua(p)]
    muc = [(p, tt if "so_sv" in tt else {**tt, **tom_tat_tu_file(p)}) for p, tt in muc]  # mục cũ thiếu số tóm tắt
    return sorted(muc, key=lambda x: x[1].get("thoi_gian", ""), reverse=True)
