"""Yêu cầu 4 – Chuẩn bị "năng lực nền tảng".

Dữ liệu KHÔNG có điểm đầu vào, nên năng lực nền của một SV phải tự xây từ chính
điểm các môn khác của SV đó. Ví dụ: muốn đánh giá điểm môn M001 của SV có "khớp"
với năng lực không, ta lấy TB các môn KHÁC của SV làm mốc.

Cách này chỉ dùng được nếu SV học đủ nhiều môn. Module này đo xem điều đó có đúng không.

Lưu ý riêng tư: so_mon_moi_sv() trả về dữ liệu theo từng SV – CHỈ dùng nội bộ,
không bao giờ đưa thẳng vào báo cáo. Các hàm còn lại chỉ trả về số tổng hợp.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cf
from .report import tao_hinh


def _luot_hoc_phan_thuong(bang: pd.DataFrame) -> pd.DataFrame:
    """Lọc các lượt điểm không phải đồ án/TT/KL và có Điểm HP.

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        Bảng con đã lọc.
    Vì sao cần: đồ án chấm theo từng SV, không nên dùng làm "năng lực nền".
    """
    return bang[(bang["loai_lop"] != cf.LOAI_DO_AN) & bang[cf.COT_HP].notna()]


def so_mon_moi_sv(bang: pd.DataFrame) -> pd.Series:
    """Đếm số môn khác nhau mỗi SV đã có điểm (không tính đồ án).

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        Series: chỉ mục là Mã SV, giá trị là số môn. ⚠️ CHỈ DÙNG NỘI BỘ – có Mã SV.
    Vì sao cần: đầu vào cho các bảng tổng hợp bên dưới.
    """
    return _luot_hoc_phan_thuong(bang).groupby(cf.COT_MA_SV)[cf.COT_MA_MON].nunique()


def mo_ta_so_mon(so_mon: pd.Series) -> pd.DataFrame:
    """Phân vị (5%, 10%, 25%, trung vị, 75%, 90%, 95%) và TB của số môn mỗi SV.

    Tham số:
        so_mon: kết quả của so_mon_moi_sv().
    Trả về:
        Bảng: chi_so | gia_tri. Không có Mã SV.
    Vì sao cần: biết SV "điển hình" học bao nhiêu môn. Cố ý KHÔNG ghi min/max vì đó là
    giá trị của đúng một người.
    """
    phan_vi = so_mon.quantile([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
    dong = [{"chi_so": "Số SV", "gia_tri": int(so_mon.size)},
            {"chi_so": "TB số môn", "gia_tri": float(so_mon.mean())}]
    dong += [{"chi_so": f"Phân vị {int(q * 100)}%", "gia_tri": float(v)} for q, v in phan_vi.items()]
    return pd.DataFrame(dong)


def phan_bo_so_mon(so_mon: pd.Series) -> pd.DataFrame:
    """Đếm số SV theo khoảng số môn đã học.

    Tham số:
        so_mon: kết quả của so_mon_moi_sv().
    Trả về:
        Bảng: so_mon | so_sv (cần lọc nhóm < 5 trước khi xuất).
    Vì sao cần: thấy có bao nhiêu SV chỉ học 1–2 môn – nhóm này không thể ước lượng
    năng lực nền đáng tin, cần cách xử lý riêng (vd dùng TB của khóa/khoa).
    """
    moc = [0, 1, 2, 4, 9, 14, 19, 29, np.inf]
    nhan = ["1", "2", "3–4", "5–9", "10–14", "15–19", "20–29", "30+"]
    nhom = pd.cut(so_mon, bins=moc, labels=nhan)
    return nhom.value_counts().reindex(nhan).rename_axis("so_mon").reset_index(name="so_sv")


def kha_thi_nang_luc_nen(bang: pd.DataFrame, so_mon: pd.Series) -> pd.DataFrame:
    """Đo tỷ lệ SV / lượt điểm đủ điều kiện tính năng lực nền theo cách "leave-one-out".

    Với mỗi ngưỡng k (1, 3, 5): một lượt điểm (SV, môn) "đủ điều kiện" nếu SV đó có
    ít nhất k môn KHÁC để tính TB làm mốc.
    Tham số:
        bang: bảng điểm đã xử lý.
        so_mon: kết quả của so_mon_moi_sv().
    Trả về:
        Bảng: so_mon_khac_toi_thieu | so_sv | ty_le_sv | ty_le_luot.
    Vì sao cần: tiêu chí 3 của Giải pháp 1 (bất tương quan giữa điểm môn và năng lực
    nền) chỉ áp dụng được cho phần dữ liệu đủ điều kiện. Bảng này cho biết phần đó lớn cỡ nào.
    """
    luot = _luot_hoc_phan_thuong(bang)
    mon_khac_moi_luot = luot[cf.COT_MA_SV].map(so_mon) - 1  # trừ chính môn đang xét
    dong = []
    for k in (1, 3, 5):
        du_sv = so_mon >= k + 1
        dong.append({"so_mon_khac_toi_thieu": k, "so_sv": int(du_sv.sum()),
                     "ty_le_sv": float(du_sv.mean()),
                     "ty_le_luot": float((mon_khac_moi_luot >= k).mean())})
    return pd.DataFrame(dong)


def so_mon_theo_khoa_sv(bang: pd.DataFrame, so_mon: pd.Series) -> pd.DataFrame:
    """Số môn TB và trung vị mỗi SV, chia theo khóa tuyển sinh (K58–K67).

    Tham số:
        bang: bảng điểm đã xử lý.
        so_mon: kết quả của so_mon_moi_sv().
    Trả về:
        Bảng: khoa_sv | so_sv | tb_so_mon | trung_vi_so_mon (cần lọc nhóm < 5).
    Vì sao cần: khóa mới (K66, K67) học ít môn hơn → năng lực nền kém tin cậy hơn;
    TCI của các khóa này cần diễn giải thận trọng.
    """
    khoa = _luot_hoc_phan_thuong(bang).groupby(cf.COT_MA_SV)[cf.COT_KHOA_SV].first()
    theo_sv = pd.DataFrame({"khoa_sv": khoa.fillna("(trống)"), "so_mon": so_mon})
    # groupby theo khoa_sv làm Mã SV biến mất khỏi kết quả – chỉ còn số tổng hợp.
    return theo_sv.groupby("khoa_sv").agg(
        so_sv=("so_mon", "size"), tb_so_mon=("so_mon", "mean"),
        trung_vi_so_mon=("so_mon", "median")).reset_index()


def ve_so_mon(bang_so_mon: pd.DataFrame):
    """Vẽ cột số SV theo khoảng số môn đã học.

    Tham số:
        bang_so_mon: bảng từ phan_bo_so_mon() (đã ẩn nhóm nhỏ).
    Trả về:
        Hình matplotlib.
    Vì sao cần: hình minh họa cho phần "năng lực nền" trong báo cáo.
    """
    fig, ax = tao_hinh("Số sinh viên theo số môn đã học (không tính đồ án)", "Số môn", "Số SV")
    ax.bar(bang_so_mon["so_mon"].astype(str), bang_so_mon["so_sv"], color="#C44E52")
    return fig
