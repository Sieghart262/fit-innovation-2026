"""Đọc dữ liệu và chuyển kiểu.

Nguyên tắc: đọc MỌI cột dưới dạng chữ trước, rồi tự chuyển từng cột sang số
một cách có kiểm soát. Nhờ vậy ta đếm được bao nhiêu ô "không đọc được"
(ví dụ ô ghi "vắng" thay vì số) – thông tin này đưa vào phần chất lượng dữ liệu.

Module này KHÔNG in dữ liệu ra màn hình.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as cf


class LoiDuLieu(Exception):
    """Lỗi khi file dữ liệu không đúng như mô tả (thiếu file, thiếu cột...).

    Thông báo lỗi chỉ được chứa tên file/tên cột, KHÔNG chứa giá trị dữ liệu.
    """


def chuan_hoa_chu(gia_tri: object) -> str:
    """Chuẩn hóa một chuỗi tiếng Việt về dạng Unicode NFC và bỏ khoảng trắng thừa.

    Tham số:
        gia_tri: chuỗi (hoặc giá trị bất kỳ) cần chuẩn hóa.
    Trả về:
        Chuỗi đã chuẩn hóa.
    Vì sao cần: chữ "ọ" có thể được lưu theo 2 cách khác nhau trong máy tính
    (một ký tự, hoặc "o" + dấu nặng). Nhìn giống hệt nhau nhưng máy so sánh
    thì khác → tên cột "Mã môn" có thể không khớp. NFC gộp về một cách viết.
    """
    return unicodedata.normalize("NFC", str(gia_tri)).strip()


def doan_ky_tu_ngan_cot(duong_dan: Path) -> str:
    """Đoán ký tự ngăn cột của CSV (",", ";" hoặc tab) chỉ từ DÒNG TIÊU ĐỀ.

    Tham số:
        duong_dan: đường dẫn tới file CSV.
    Trả về:
        Ký tự ngăn cột cho ra nhiều cột nhất.
    Vì sao cần: file mô tả của BTC không ghi rõ ký tự ngăn cột. Excel tiếng Việt
    hay lưu CSV bằng dấu ";". Đọc với nrows=0 nghĩa là chỉ đọc tên cột, không
    đọc dòng dữ liệu nào. Ký tự đúng là ký tự tách được nhiều cột nhất (ký tự sai
    gần như chỉ cho 1 cột).
    """
    tot_nhat, so_cot_max = ",", 0
    for ky_tu in [",", ";", "\t"]:
        try:
            so_cot = pd.read_csv(duong_dan, encoding="utf-8-sig", sep=ky_tu, nrows=0).shape[1]
        except (pd.errors.ParserError, UnicodeDecodeError):
            continue
        if so_cot > so_cot_max:
            tot_nhat, so_cot_max = ky_tu, so_cot
    return tot_nhat


def doc_csv(duong_dan: Path) -> pd.DataFrame:
    """Đọc một file CSV, giữ mọi cột ở dạng chữ, chuẩn hóa tên cột.

    Tham số:
        duong_dan: đường dẫn tới file CSV.
    Trả về:
        DataFrame (bảng) với mọi ô là chữ; ô trống thành NaN (giá trị thiếu).
    Vì sao cần: BTC ghi file mã hóa UTF-8 có BOM (ký tự ẩn ở đầu file để Excel
    hiểu tiếng Việt). encoding="utf-8-sig" giúp bỏ ký tự ẩn đó, nếu không thì
    tên cột đầu tiên sẽ bị dính ký tự lạ. Ký tự ngăn cột được tự đoán.
    """
    if not duong_dan.exists():
        raise LoiDuLieu(f"Không tìm thấy file: {duong_dan}")
    bang = pd.read_csv(duong_dan, encoding="utf-8-sig", dtype=str,
                       sep=doan_ky_tu_ngan_cot(duong_dan))
    bang.columns = [chuan_hoa_chu(c) for c in bang.columns]
    return bang


def kiem_tra_ten_cot(bang: pd.DataFrame, cot_bat_buoc: list[str], ten_file: str) -> None:
    """Dừng chương trình nếu file thiếu cột bắt buộc.

    Tham số:
        bang: bảng vừa đọc.
        cot_bat_buoc: danh sách tên cột phải có.
        ten_file: tên file (để ghi vào thông báo lỗi).
    Trả về:
        Không trả về gì; nếu thiếu cột thì báo LoiDuLieu kèm danh sách tên cột
        đang có (chỉ tên cột, không có dữ liệu) để mình sửa config.py.
    Vì sao cần: phát hiện sớm khi tên cột thực tế khác từ điển dữ liệu,
    thay vì để chương trình chạy sai lặng lẽ.
    """
    thieu = [c for c in cot_bat_buoc if c not in bang.columns]
    if thieu:
        raise LoiDuLieu(
            f"File {ten_file} thiếu cột: {thieu}. "
            f"Các cột đang có: {list(bang.columns)}. Hãy sửa tên trong eda/config.py."
        )


def chuyen_so(cot: pd.Series) -> tuple[pd.Series, int]:
    """Chuyển một cột chữ sang số thực, đếm số ô không chuyển được.

    Tham số:
        cot: cột dữ liệu dạng chữ.
    Trả về:
        (cột số, số ô có chữ nhưng không đọc được thành số).
    Vì sao cần: điểm phải là số mới tính được trung bình, độ lệch chuẩn.
    Chấp nhận cả dấu phẩy thập phân kiểu Việt Nam ("8,5" -> 8.5).
    """
    chu = cot.str.strip().str.replace(",", ".", regex=False)
    so = pd.to_numeric(chu, errors="coerce")  # coerce: ô không phải số -> NaN
    co_chu = chu.notna() & (chu != "")
    so_o_loi = int((co_chu & so.isna()).sum())
    return so, so_o_loi


def chuyen_co_khong(cot: pd.Series) -> tuple[pd.Series, int]:
    """Chuyển cột "Có/Không" sang True/False, đếm số ô có giá trị lạ.

    Tham số:
        cot: cột dạng chữ ("Có", "Không", ...).
    Trả về:
        (cột True/False – ô trống hoặc lạ coi là False, số ô có giá trị lạ).
    Vì sao cần: dùng để tách lớp EP và học phần đồ án/thực tập khỏi lớp thường,
    vì chúng chấm điểm theo cách khác (file mô tả đã lưu ý).
    """
    ban_do = {"có": True, "co": True, "1": True, "true": True, "x": True,
              "không": False, "khong": False, "0": False, "false": False}
    chu = cot.map(lambda x: chuan_hoa_chu(x).lower() if pd.notna(x) else x)
    ket_qua = chu.map(ban_do)
    so_o_la = int((chu.notna() & ket_qua.isna()).sum())
    return ket_qua.eq(True), so_o_la  # .eq(True): NaN -> False


def them_cot_phu(bang: pd.DataFrame) -> pd.DataFrame:
    """Thêm các cột tính sẵn dùng cho nhiều phân tích.

    Các cột thêm:
        nam_bat_dau : 2019 cho "2019-2020".
        ky_so       : nam_bat_dau*10 + học kỳ (vd 20212) – để sắp xếp các kỳ theo thời gian.
        nhan_ky     : nhãn dễ đọc "2021-2022 HK2".
        giai_doan   : trước / từ HK2 2021-22 (mốc đổi trọng số điểm).
        loai_lop    : Đồ án/TT/KL, Lớp EP hoặc Lớp thường.
    Tham số:
        bang: bảng điểm đã chuyển kiểu.
    Trả về:
        Chính bảng đó, có thêm các cột trên.
    Vì sao cần: giả thuyết "điểm tăng sau khi đổi trọng số" và việc tách loại lớp
    cần các cột này; tính một lần ở đây cho mọi module dùng chung.
    """
    nam = bang[cf.COT_NAM_HOC].str.extract(r"^(\d{4})")[0]  # lấy 4 chữ số đầu
    bang["nam_bat_dau"] = pd.to_numeric(nam, errors="coerce")
    bang["ky_so"] = bang["nam_bat_dau"] * 10 + bang[cf.COT_HOC_KY]

    hoc_ky_chu = bang[cf.COT_HOC_KY].map(lambda x: str(int(x)) if pd.notna(x) else "?")
    bang["nhan_ky"] = bang[cf.COT_NAM_HOC].fillna("?") + " HK" + hoc_ky_chu

    moc = cf.MOC_DOI_TRONG_SO[0] * 10 + cf.MOC_DOI_TRONG_SO[1]  # 20212
    bang["giai_doan"] = np.where(
        bang["ky_so"].isna(), cf.GIAI_DOAN_KHONG_RO,
        np.where(bang["ky_so"] < moc, cf.GIAI_DOAN_TRUOC, cf.GIAI_DOAN_SAU),
    )

    # np.select: xét điều kiện theo thứ tự, điều kiện đầu tiên đúng sẽ thắng.
    # Đồ án ưu tiên hơn EP (một học phần đồ án của lớp EP vẫn tính là đồ án).
    bang["loai_lop"] = np.select(
        [bang[cf.COT_DO_AN], bang[cf.COT_EP]],
        [cf.LOAI_DO_AN, cf.LOAI_EP],
        default=cf.LOAI_THUONG,
    )
    return bang


def doc_du_lieu_diem(duong_dan: Path = cf.FILE_DIEM) -> tuple[pd.DataFrame, dict]:
    """Đọc Du_lieu.csv, kiểm tra cột, chuyển kiểu và thêm cột phụ.

    Tham số:
        duong_dan: đường dẫn tới Du_lieu.csv (mặc định lấy từ config.py).
    Trả về:
        (bảng điểm đã xử lý, thông tin phụ) – thông tin phụ gồm:
            "so_cot_goc": số cột ban đầu của file,
            "o_loi": {tên cột: số ô không đọc được},
            "o_trong": {tên cột: số ô trống trong file gốc}.
    Vì sao cần: đây là điểm vào duy nhất để lấy dữ liệu; mọi phân tích khác
    đều dùng bảng do hàm này trả về nên cách xử lý luôn thống nhất.
    """
    bang = doc_csv(duong_dan)
    kiem_tra_ten_cot(bang, cf.COT_BAT_BUOC, duong_dan.name)
    so_cot_goc = bang.shape[1]

    # Ô chỉ có khoảng trắng cũng coi là trống. Đếm ô trống TRƯỚC khi chuyển kiểu,
    # vì sau khi chuyển, ô trống và ô chữ lỗi đều thành NaN, không phân biệt được.
    for cot in cf.COT_BAT_BUOC:
        bang[cot] = bang[cot].str.strip().replace("", np.nan)
    o_trong = {cot: int(bang[cot].isna().sum()) for cot in cf.COT_BAT_BUOC}

    o_loi: dict[str, int] = {}
    for cot in cf.COT_DIEM + cf.COT_SO_NGUYEN:
        bang[cot], o_loi[cot] = chuyen_so(bang[cot])
    for cot in cf.COT_CO_KHONG:
        bang[cot], o_loi[cot] = chuyen_co_khong(bang[cot])
    bang = them_cot_phu(bang)
    return bang, {"so_cot_goc": so_cot_goc, "o_loi": o_loi, "o_trong": o_trong}


def doc_thoi_khoa_bieu(duong_dan: Path = cf.FILE_TKB) -> pd.DataFrame | None:
    """Đọc Thoi_khoa_bieu.csv (chỉ để đối chiếu kích thước với mô tả).

    Tham số:
        duong_dan: đường dẫn tới file thời khóa biểu.
    Trả về:
        Bảng thời khóa biểu (dạng chữ), hoặc None nếu không có file.
    Vì sao cần: yêu cầu 1 – kiểm tra số dòng/cột so với mô tả. File này không
    nối được với bảng điểm nên chưa dùng cho phân tích khác.
    """
    if not duong_dan.exists():
        return None
    return doc_csv(duong_dan)
