"""Cấu hình chung: đường dẫn, tên cột và các ngưỡng dùng trong toàn bộ EDA.

Vì sao tách riêng file này? Khi BTC đổi tên cột hoặc đội muốn đổi ngưỡng
(ví dụ tỷ lệ điểm A từ 60% sang 50%), chỉ cần sửa MỘT chỗ ở đây.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Đường dẫn
# ---------------------------------------------------------------------------
# __file__ là file config.py này. parents[0] = eda/, parents[1] = 03_ma-nguon/,
# parents[2] = thư mục gốc dự án ("fit innovation pick").
THU_MUC_GOC = Path(__file__).resolve().parents[2]

THU_MUC_DU_LIEU = THU_MUC_GOC / "01_du-lieu" / "raw" / "Du_lieu_Ban_Ket_FIT_Innovation"
FILE_DIEM = THU_MUC_DU_LIEU / "Du_lieu.csv"
FILE_TKB = THU_MUC_DU_LIEU / "Thoi_khoa_bieu.csv"

THU_MUC_PHAN_TICH = THU_MUC_GOC / "02_phan-tich"
FILE_BAO_CAO = THU_MUC_PHAN_TICH / "02-ket-qua-eda.md"
TEN_THU_MUC_HINH = "hinh"  # hình lưu ở 02_phan-tich/hinh/

# ---------------------------------------------------------------------------
# Tên cột trong Du_lieu.csv (lấy đúng theo Tu_dien_du_lieu.csv)
# ---------------------------------------------------------------------------
COT_NAM_HOC = "Năm học"
COT_HOC_KY = "Học kỳ"
COT_MA_MON = "Mã môn"
COT_NHOM_MON = "Nhóm môn"
COT_SO_TC = "Số TC"
COT_DO_AN = "Là đồ án/thực tập/khóa luận"
COT_EP = "Lớp mang mã EP"
COT_MA_LOP = "Mã lớp học phần"
COT_SI_SO = "Sĩ số lớp (trong dữ liệu)"
COT_MA_SV = "Mã SV"
COT_KHOA_SV = "Khóa SV"
COT_KHOA = "Khoa của SV"
COT_CC = "CC"
COT_KTTX1 = "KTTX1"
COT_KTTX2 = "KTTX2"
COT_KTTX = "KTTX (TB)"
COT_THI = "Thi"
COT_HP = "Điểm HP (thang 10)"
COT_TRONG_SO = "Cơ cấu trọng số suy ra (CC/KTTX/Thi, %)"

# Tất cả các cột phải có trong file (thiếu cột nào là dừng ngay).
COT_BAT_BUOC = [
    COT_NAM_HOC, COT_HOC_KY, COT_MA_MON, COT_NHOM_MON, COT_SO_TC, COT_DO_AN, COT_EP,
    COT_MA_LOP, COT_SI_SO, COT_MA_SV, COT_KHOA_SV, COT_KHOA, COT_CC, COT_KTTX1,
    COT_KTTX2, COT_KTTX, COT_THI, COT_HP, COT_TRONG_SO,
]
COT_DIEM = [COT_CC, COT_KTTX1, COT_KTTX2, COT_KTTX, COT_THI, COT_HP]  # các cột điểm thang 10
COT_SO_NGUYEN = [COT_HOC_KY, COT_SO_TC, COT_SI_SO]                  # cột số không phải điểm
COT_CO_KHONG = [COT_DO_AN, COT_EP]                                   # cột Có/Không

# Cột KHÔNG được để trống (theo mô tả). Các cột còn lại được phép trống:
# điểm (CC, KTTX, Thi, HP), Khóa SV (~0,1%) và Cơ cấu trọng số (~36%).
COT_KHONG_DUOC_TRONG = [
    COT_NAM_HOC, COT_HOC_KY, COT_MA_MON, COT_NHOM_MON, COT_SO_TC, COT_DO_AN, COT_EP,
    COT_MA_LOP, COT_SI_SO, COT_MA_SV, COT_KHOA,
]

# Định dạng đúng của các cột mã/văn bản (biểu thức chính quy, lấy theo file mô tả).
DINH_DANG = {
    COT_NAM_HOC: r"\d{4}-\d{4}",            # 2019-2020 (năm sau = năm trước + 1, kiểm tra riêng)
    COT_MA_MON: r"M\d{3}",                  # M001
    COT_NHOM_MON: r"N[1-8]",                # N1…N8
    COT_MA_LOP: r"L\d{4}",                  # L0001
    COT_MA_SV: r"S\d{5}",                   # S00001
    # K50…K67. Mô tả BTC ghi K58–K67, nhưng dữ liệu có SV khóa cũ (K54, K56, K57) chỉ xuất hiện
    # trong 2019-2020 → 2021-2022: SV học lại/ra trường muộn, hợp lệ (đội đã kiểm tra 17/11/2026).
    COT_KHOA_SV: r"K(5\d|6[0-7])",
    COT_KHOA: r"KH\d{2}|KH-khác",           # KH01… hoặc KH-khác
    COT_TRONG_SO: r"\d+/\d+/\d+",           # 10/20/70
}

# Khoảng giá trị hợp lệ của cột số: (nhỏ nhất, lớn nhất, phải là số nguyên?)
KHOANG_HOP_LE = {
    COT_HOC_KY: (1, 3, True),
    COT_SO_TC: (1, 10, True),
    COT_SI_SO: (1, None, True),
    **{c: (0, 10, False) for c in [COT_CC, COT_KTTX1, COT_KTTX2, COT_KTTX, COT_THI, COT_HP]},
}

# Tên loại lỗi trong bảng "lỗi theo từng cột" (tao_du_lieu_gia.py dùng chung để ghi đáp án).
LOI_TRONG = "trống (cột bắt buộc)"
LOI_DINH_DANG = "sai định dạng"
LOI_CHU = "không đọc được (chữ thay vì số)"
LOI_NGOAI = "ngoài khoảng cho phép"
LOI_LA = "giá trị lạ (không phải Có/Không)"
LOI_LAN = "lớp lẫn nhiều năm/kỳ/môn"
LOI_SI_SO = "sĩ số ghi ≠ số dòng của lớp"
LOI_TRUNG = "trùng cặp (lớp, SV)"
LOI_TONG = "tổng trọng số ≠ 100"

# Cột của Thoi_khoa_bieu.csv (chỉ dùng để so kích thước với mô tả).
COT_TKB_MA_LHP = "Mã LHP"

# ---------------------------------------------------------------------------
# Con số BTC ghi trong file mô tả – dùng để đối chiếu
# ---------------------------------------------------------------------------
MO_TA_KY_VONG = {
    "so_dong": 38_342,
    "so_cot": 19,
    "so_sv": 5_067,
    "so_lop": 877,
    "so_mon": 93,
    "so_dong_do_an": 2_103,
    "so_dong_ep": 2_726,
    "so_dong_hoc_ky_3": 563,
    "tkb_so_dong": 1_170,
    "tkb_so_cot": 18,
    "tkb_so_lop": 1_090,
}

# ---------------------------------------------------------------------------
# Ngưỡng (theo đề bài và quy định đào tạo)
# ---------------------------------------------------------------------------
NGUONG_DIEM_A = 8.5          # điểm A: [8,5 – 10]
NGUONG_TY_LE_A = 0.60        # đề bài: tỷ lệ A > 60% là đáng nghi
NGUONG_DAT = 4.5             # đạt học phần khi HP ≥ 4,5
NGUONG_NHOM_TOI_THIEU = 5    # quy tắc riêng tư: không công bố nhóm dưới 5 người
NGUONG_Z = 2.0               # |z| > 2 ≈ khác thường (chỉ ~5% nếu phân phối chuẩn)
SO_LOP_KHAC_TOI_THIEU = 3    # cần ít nhất 3 lớp KHÁC cùng môn mới tính được z
MOC_DOI_TRONG_SO = (2021, 2) # HK2 năm học 2021-2022: trọng số đổi 10/20/70 -> 10/40/50

# ---------------------------------------------------------------------------
# Nhãn dùng chung
# ---------------------------------------------------------------------------
LOAI_THUONG = "Lớp thường"
LOAI_EP = "Lớp EP"
LOAI_DO_AN = "Đồ án/TT/KL"

GIAI_DOAN_TRUOC = "Trước HK2 2021-22"
GIAI_DOAN_SAU = "Từ HK2 2021-22"
GIAI_DOAN_KHONG_RO = "Không rõ"
