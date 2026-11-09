"""Quy tắc riêng tư – "người gác cổng" cho mọi output.

Mọi bảng và hình trước khi ghi ra báo cáo PHẢI đi qua kiem_tra_an_toan().
Hàm này chặn (báo lỗi, không ghi gì) nếu:
  1. Bảng còn cột Mã SV (kể cả khi Mã SV nằm ở chỉ mục – index).
  2. Có ô nào trông giống mã sinh viên (dạng S + 5 chữ số, ví dụ S00001).
  3. Có nhóm dưới 5 người, hoặc người viết code quên khai báo bảng đếm theo cột nào.

Vì sao cần cho bài thi: BTC yêu cầu chỉ phân tích tổng hợp, không xác định danh tính
sinh viên. Nhóm quá nhỏ (vd lớp 2 người) thì "điểm trung bình lớp" gần như là điểm
của từng người → phải ẩn đi. Đặt quy tắc thành code giúp không ai lỡ tay vi phạm.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from . import config as cf


class LoiRiengTu(Exception):
    """Lỗi khi một output vi phạm quy tắc riêng tư. Chương trình sẽ dừng, không ghi báo cáo."""


# Mẫu nhận diện mã sinh viên: chữ S + đúng 5 chữ số, đứng riêng (\b = ranh giới từ).
_MAU_MA_SV = re.compile(r"\bS\d{5}\b")


def _chuan_hoa_ten(ten: object) -> str:
    """Chuẩn hóa tên cột để so sánh (NFC, bỏ khoảng trắng, chữ thường).

    Tham số:
        ten: tên cột.
    Trả về:
        Tên đã chuẩn hóa.
    Vì sao cần: để "Mã SV", "mã sv " hay bản Unicode khác đều bị nhận ra.
    """
    return unicodedata.normalize("NFC", str(ten)).strip().lower()


_COT_CAM = {_chuan_hoa_ten(cf.COT_MA_SV)}


def _co_gia_tri_giong_ma_sv(gia_tri: pd.Series | pd.Index) -> bool:
    """Kiểm tra một cột (hoặc chỉ mục) có giá trị nào giống mã sinh viên không.

    Tham số:
        gia_tri: cột hoặc chỉ mục cần kiểm tra.
    Trả về:
        True nếu có ít nhất một giá trị khớp mẫu S#####.
    Vì sao cần: phòng trường hợp Mã SV bị đổi tên cột (vd "id") nhưng giá trị vẫn lộ ra.
    """
    chu = pd.Series(gia_tri, dtype="object").astype(str)
    return bool(chu.str.contains(_MAU_MA_SV, regex=True).any())


def kiem_tra_an_toan(
    bang: pd.DataFrame,
    ten_bang: str,
    cot_dem: str | None = None,
    ly_do_khong_dem: str | None = None,
) -> pd.DataFrame:
    """Chặn bảng nếu còn Mã SV hoặc có nhóm dưới 5 người.

    Tham số:
        bang: bảng sắp đưa vào báo cáo (hoặc dữ liệu nguồn của một hình).
        ten_bang: tên bảng, để thông báo lỗi dễ hiểu.
        cot_dem: tên cột chứa số người của mỗi dòng (vd "so_sv", "n").
            Mọi giá trị trong cột này phải ≥ 5.
        ly_do_khong_dem: dùng khi bảng không có "nhóm người" (vd bảng đếm số lớp
            theo sĩ số, hoặc chỉ số toàn bộ dữ liệu). Bắt buộc ghi lý do – để người
            viết code phải suy nghĩ trước khi bỏ qua bước đếm.
    Trả về:
        Chính bảng đó nếu an toàn (để có thể viết gọn: bc.bang(kiem_tra_an_toan(...))).
    Vì sao cần: là chốt chặn cuối cùng trước khi bất kỳ số liệu nào rời khỏi máy.
    """
    # 1. Cột cấm (xét cả tên cột và tên chỉ mục)
    ten_cac_cot = [c for c in list(bang.columns) + list(bang.index.names) if c is not None]
    for ten in ten_cac_cot:
        if _chuan_hoa_ten(ten) in _COT_CAM:
            raise LoiRiengTu(f"Bảng '{ten_bang}' còn cột '{ten}' (Mã SV). Không được xuất.")

    # 2. Giá trị giống mã sinh viên (chỉ cần xét cột dạng chữ)
    for ten in bang.columns:
        cot = bang[ten]
        if pd.api.types.is_numeric_dtype(cot) or pd.api.types.is_bool_dtype(cot):
            continue
        if _co_gia_tri_giong_ma_sv(cot):
            raise LoiRiengTu(f"Bảng '{ten_bang}', cột '{ten}' có giá trị giống mã sinh viên.")
    for muc in range(bang.index.nlevels):
        chi_muc = bang.index.get_level_values(muc)
        if not pd.api.types.is_numeric_dtype(chi_muc) and _co_gia_tri_giong_ma_sv(chi_muc):
            raise LoiRiengTu(f"Bảng '{ten_bang}': chỉ mục có giá trị giống mã sinh viên.")

    # 3. Nhóm nhỏ
    if cot_dem is None:
        if not ly_do_khong_dem:
            raise LoiRiengTu(
                f"Bảng '{ten_bang}': phải khai báo cot_dem (cột số người) "
                "hoặc ly_do_khong_dem (vì sao bảng không có nhóm người)."
            )
        return bang
    if cot_dem not in bang.columns:
        raise LoiRiengTu(f"Bảng '{ten_bang}': không có cột đếm '{cot_dem}'.")
    dem = pd.to_numeric(bang[cot_dem], errors="coerce")
    so_nhom_nho = int((dem.isna() | (dem < cf.NGUONG_NHOM_TOI_THIEU)).sum())
    if so_nhom_nho:
        raise LoiRiengTu(
            f"Bảng '{ten_bang}' có {so_nhom_nho} nhóm dưới {cf.NGUONG_NHOM_TOI_THIEU} người. "
            "Hãy gọi loc_nhom_nho() trước khi xuất."
        )
    return bang


def loc_nhom_nho(bang: pd.DataFrame, cot_dem: str) -> tuple[pd.DataFrame, int]:
    """Bỏ các dòng có ít hơn 5 người, trả về bảng còn lại và số dòng đã ẩn.

    Tham số:
        bang: bảng có cột đếm số người.
        cot_dem: tên cột đếm.
    Trả về:
        (bảng đã lọc, số nhóm bị ẩn). Số nhóm bị ẩn được ghi vào báo cáo cho minh bạch.
    Vì sao cần: thay vì dừng cả chương trình, ta ẩn đúng các nhóm nhỏ rồi tiếp tục.
    """
    giu_lai = pd.to_numeric(bang[cot_dem], errors="coerce") >= cf.NGUONG_NHOM_TOI_THIEU
    return bang[giu_lai].copy(), int((~giu_lai).sum())
