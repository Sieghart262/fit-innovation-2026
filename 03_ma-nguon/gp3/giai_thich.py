"""Lời giải thích (Explainable) cho từng SV, sinh bằng mẫu câu.

Không dùng mô hình AI bên ngoài: BTC cấm đưa dữ liệu vào dịch vụ bên ngoài, và mẫu câu
cố định giúp lời giải thích luôn khớp đúng với con số đã tính.
"""

from __future__ import annotations

import pandas as pd

from gp1 import cau_hinh as ch1
from . import cau_hinh as ch3


def _so(x: float, le: int = 2) -> str:
    """Viết số kiểu Việt Nam (dấu phẩy thập phân, bỏ số 0 thừa)."""
    s = f"{x:.{le}f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _nghia(nhan: object) -> str:
    """Nghĩa ngắn của một nhãn Giải pháp 1, vd "lạm phát điểm cao"."""
    return ch1.Y_NGHIA_NHAN.get(nhan, str(nhan)).split(" (")[0].lower()


def _ly_do_mon(r) -> str:
    """Một ý giải thích cho một môn có điểm thang 4 thay đổi sau hiệu chỉnh.

    Tham số:
        r: một dòng của bảng mon_cua_sinh_vien() (dạng namedtuple).
    Trả về:
        Câu giải thích. Trường hợp thường: cùng một lần học trước và sau. Trường hợp SV học lại
        và việc hiệu chỉnh làm đổi lần có điểm cao nhất: nêu rõ cả hai lớp để con số không lệch nhau.
    """
    giam = r.d4_sau < r.d4_truoc
    thang4 = (f"thang 4 {'giảm' if giam else 'tăng'} từ {_so(r.d4_truoc, 1)} ({r.chu_truoc}) "
              f"{'còn' if giam else 'lên'} {_so(r.d4_sau, 1)} ({r.chu_sau})")
    if r.lop_truoc == r.class_id:
        return (f"Môn {r.course} (lớp {r.class_id}, {r.year}): {_so(r.hp_truoc, 1)} → {_so(r.Adjusted_Score)} điểm, "
                f"{thang4} vì lớp được xác định {r.nhan_lop_gp1} ({_nghia(r.nhan_lop_gp1)})")
    return (f"Môn {r.course} (SV học nhiều lần): trước hiệu chỉnh tính lần ở lớp {r.lop_truoc} "
            f"({_so(r.hp_truoc, 1)} điểm), sau hiệu chỉnh tính lần ở lớp {r.class_id} ({_so(r.Adjusted_Score)} điểm), "
            f"{thang4}; nhãn Giải pháp 1 của hai lớp: {r.lop_truoc} – {r.nhan_lop_truoc}, "
            f"{r.class_id} – {r.nhan_lop_gp1}")


def giai_thich(sv: pd.DataFrame, mon: pd.DataFrame, cfg: ch3.CauHinhGP3) -> pd.Series:
    """Viết lời giải thích cho mọi SV: mức trước/sau, các môn ảnh hưởng nhiều nhất, cờ rà soát, độ tin cậy.

    Tham số:
        sv: bảng từ tinh_tci() đã qua bo_sung_sinh_vien().
        mon: bảng từ mon_cua_sinh_vien().
        cfg: cấu hình.
    Trả về:
        Series (cùng chỉ số với sv) chứa lời giải thích tiếng Việt.
    Vì sao cần: đề yêu cầu báo cáo giải thích lý do phân loại (Explainable AI); phòng đào tạo
    phải trả lời được "vì sao SV này bị xếp mức này".
    """
    doi = mon[mon["anh_huong_tc"].fillna(0).ne(0)].copy()
    doi["_do_lon"] = doi["anh_huong_tc"].abs()
    doi = doi.sort_values(["student", "_do_lon"], ascending=[True, False])
    ly_do = (doi.groupby("student").head(cfg.so_ly_do_toi_da)
             .assign(_y=lambda x: [_ly_do_mon(r) for r in x.itertuples()])
             .groupby("student")["_y"].agg("; ".join))
    so_doi = doi.groupby("student").size()

    ra = []
    for r in sv.itertuples():
        vang = (f"{r.so_luot_vang_thi} lượt vắng thi (HP = 0) không được tính" if r.so_luot_vang_thi else "")
        if r.so_mon == 0:
            ra.append("Không có môn nào có điểm hợp lệ nên chưa tính được TCI" + (f"; {vang}." if vang else "."))
            continue
        y = [f"GPA thang 4 danh nghĩa {_so(r.GPA4_goc)} ({r.muc_truoc}) → TCI {_so(r.TCI)} ({r.muc_sau}), "
             f"tính trên {r.so_mon} môn / {_so(r.so_tc, 0)} tín chỉ"]
        n_doi = int(so_doi.get(r.student, 0))
        if n_doi:
            y.append(f"{n_doi} môn đổi điểm thang 4 do lớp bị hiệu chỉnh ở Giải pháp 2. "
                     f"Ảnh hưởng nhiều nhất: {ly_do[r.student]}")
        elif r.so_mon_hieu_chinh:
            y.append(f"{r.so_mon_hieu_chinh} môn được hiệu chỉnh nhẹ nhưng không đổi điểm chữ → TCI = GPA danh nghĩa")
        else:
            y.append("Không môn nào thuộc lớp bị hiệu chỉnh → TCI = GPA danh nghĩa")
        if r.so_mon_review:
            y.append(f"{r.so_mon_review} môn có điểm khác hẳn năng lực thể hiện ở các môn khác (REVIEW_REQUIRED) "
                     f"– chỉ cần rà soát, không làm đổi TCI")
        if vang:
            y.append(vang[0].upper() + vang[1:])
        if r.do_tin_cay == ch3.DO_TIN_CAY_THAP:
            y.append(f"Độ tin cậy thấp: chỉ có {r.so_mon} môn trong dữ liệu (< {cfg.so_mon_tin_cay})")
        ra.append(". ".join(y) + ".")
    return pd.Series(ra, index=sv.index)
