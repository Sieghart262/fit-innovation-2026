"""Chuẩn bị dữ liệu cho Giải pháp 1: đổi tên cột ngắn, tách SV vắng thi, xác định
cơ cấu điểm và tình trạng dữ liệu của từng lớp.

Module này KHÔNG in dữ liệu ra màn hình.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda import config as cf
from . import cau_hinh as ch

# Tên cột ngắn dùng trong Giải pháp 1 (giữ theo bản gốc của thành viên nhóm).
TEN_NGAN = {
    cf.COT_NAM_HOC: "year", cf.COT_HOC_KY: "sem", cf.COT_MA_MON: "course",
    cf.COT_NHOM_MON: "group", cf.COT_SO_TC: "credits", cf.COT_DO_AN: "is_project",
    cf.COT_EP: "is_ep", cf.COT_MA_LOP: "class_id", cf.COT_MA_SV: "student",
    cf.COT_CC: "cc", cf.COT_KTTX: "kttx", cf.COT_THI: "exam", cf.COT_HP: "hp",
    cf.COT_TRONG_SO: "weights", "nam_bat_dau": "year_start",
}


def chuan_bi(bang: pd.DataFrame) -> pd.DataFrame:
    """Lấy các cột cần dùng từ bảng do eda.load.doc_du_lieu_diem() trả về.

    Tham số:
        bang: bảng điểm đã đọc, chuyển kiểu và có cột phụ (nam_bat_dau...).
    Trả về:
        Bảng mới chỉ gồm các cột Giải pháp 1 cần, tên cột ngắn (xem TEN_NGAN).
    Vì sao cần: dùng lại phần đọc dữ liệu đã kiểm thử của EDA (xử lý BOM, chuẩn
    hóa tiếng Việt, đếm ô lỗi) thay vì đọc CSV lần nữa.
    """
    d = bang[list(TEN_NGAN)].rename(columns=TEN_NGAN).copy()
    d["is_project"] = d["is_project"].astype(bool)
    d["is_ep"] = d["is_ep"].astype(bool)
    return d


def lam_sach(d: pd.DataFrame) -> pd.DataFrame:
    """Đánh dấu SV vắng thi và điểm hợp lệ.

    Tham số:
        d: bảng từ chuan_bi() (có thể đã bị cài bất thường khi kiểm chứng).
    Trả về:
        Bản sao có thêm cột absent (vắng thi/bỏ học) và valid (điểm dùng để phân tích).
    Vì sao cần: HP = 0 kèm Thi = 0/trống là SV vắng thi, không phản ánh cách
    giảng viên chấm, nên tách khỏi phân phối điểm của lớp.
    """
    d = d.copy()
    d["absent"] = d["hp"].eq(0) & (d["exam"].isna() | d["exam"].eq(0))
    d["valid"] = d["hp"].notna() & ~d["absent"]
    return d


def tinh_trang_lop(d: pd.DataFrame, cfg: ch.CauHinh) -> pd.DataFrame:
    """Xác định cơ cấu điểm và tình trạng dữ liệu của từng lớp.

    Quy tắc (chỉ xét điểm hợp lệ):
        - Lớp không có điểm hợp lệ nào                → INCOMPLETE_DATA (chưa có HP).
        - Dưới một nửa số SV có CC/KTTX               → cơ cấu "Chỉ có Thi" (vd nhiều lớp 2019-2020),
          trong đó nếu HP < 0,9 × Thi ở các SV không có CC/KTTX → INCOMPLETE_DATA (chưa nhập
          điểm quá trình; vd HP ≈ 0,5 × Thi ở một số lớp 2025-2026).
        - Còn lại                                      → cơ cấu "Có điểm quá trình".
    Tham số:
        d: bảng đã qua lam_sach().
        cfg: cấu hình.
    Trả về:
        Bảng 1 dòng/lớp: class_id, co_cau, ty_le_hp_thi (trung vị HP/Thi), du_lieu_chua_du (True/False),
        ly_do_chua_du.
    Vì sao cần: lớp "chỉ có Thi" có mặt bằng điểm khác lớp có điểm quá trình nên chỉ
    được so với nhau; lớp chưa nhập đủ điểm sẽ có HP thấp giả tạo và không được coi
    là "ép điểm".
    """
    v = d[d["valid"]]
    co_qt_dong = v["cc"].notna() | v["kttx"].notna()
    ty_le_qt = co_qt_dong.groupby(v["class_id"]).mean()
    khong_qt_thi = v[~co_qt_dong & (v["exam"] > 0)]   # SV không có CC/KTTX nhưng có điểm thi
    ty_le = (khong_qt_thi["hp"] / khong_qt_thi["exam"]).groupby(khong_qt_thi["class_id"]).median()

    lop = pd.DataFrame(index=pd.Index(d["class_id"].unique(), name="class_id"))
    lop["ty_le_co_qua_trinh"] = ty_le_qt.reindex(lop.index)
    lop["ty_le_hp_thi"] = ty_le.reindex(lop.index)
    khong_diem = lop["ty_le_co_qua_trinh"].isna()     # không có điểm hợp lệ nào
    chi_thi = lop["ty_le_co_qua_trinh"] < 0.5
    thieu_qt = chi_thi & (lop["ty_le_hp_thi"] < cfg.ty_le_hp_thi_thieu)

    lop["co_cau"] = np.where(chi_thi, ch.CO_CAU_CHI_THI, ch.CO_CAU_DU)
    lop["du_lieu_chua_du"] = khong_diem | thieu_qt
    lop["ly_do_chua_du"] = np.select(
        [khong_diem, thieu_qt],
        ["Chưa có điểm HP hợp lệ",
         "Phần lớn SV không có CC/KTTX và HP chỉ bằng khoảng "
         + (lop["ty_le_hp_thi"].round(2).astype(str)) + " × Thi → điểm quá trình chưa được nhập"],
        default="")
    return lop.reset_index()
