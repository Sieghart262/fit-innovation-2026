"""Cấu hình Giải pháp 1: tên nhãn, ngưỡng và thư mục kết quả.

Mọi ngưỡng nằm trong lớp CauHinh để đội chỉnh ở MỘT chỗ và ghi lại trong báo cáo.
"""

from __future__ import annotations

from dataclasses import dataclass

from eda import config as cf

# ---------------------------------------------------------------------------
# Thư mục kết quả – nằm trong 01_du-lieu/ nên KHÔNG bị đưa lên GitHub
# (kết quả theo lớp tính từ dữ liệu BTC, gồm cả lớp nhỏ – chỉ dành cho nhà trường).
# ---------------------------------------------------------------------------
THU_MUC_KET_QUA = cf.THU_MUC_GOC / "01_du-lieu" / "ket-qua" / "gp1"

# ---------------------------------------------------------------------------
# Nhãn
# ---------------------------------------------------------------------------
# 3 nhãn theo đề BTC
HIGH = "HIGH_INFLATION"            # lạm phát điểm cao
STEEP = "UNUSUALLY_STEEP"          # điểm bị ép quá thấp
DIST = "SUSPICIOUS_DISTRIBUTION"   # phân phối biến dạng
NHAN_BAT_THUONG = [HIGH, STEEP, DIST]

# Nhãn bổ sung của đội
NORMAL = "NORMAL"                  # bình thường
REVIEW = "NEEDS_REVIEW"            # lệch so với mốc nhưng CHƯA có bằng chứng do cách chấm
IT_DU_LIEU = "INSUFFICIENT_DATA"   # lớp có ≤ 5 điểm hợp lệ
CHUA_DU = "INCOMPLETE_DATA"        # dữ liệu chưa đầy đủ (chưa nhập điểm quá trình / chưa có HP)
KHONG_MOC = "NO_REFERENCE"         # không đủ lớp để so sánh

Y_NGHIA_NHAN = {
    HIGH: "Lạm phát điểm cao (lệch lên + có bằng chứng do cách chấm)",
    STEEP: "Điểm bị ép quá thấp (lệch xuống + có bằng chứng do cách chấm)",
    DIST: "Phân phối biến dạng (σ quá nhỏ, KTTX trùng Thi, dồn điểm...)",
    REVIEW: "Lệch so với mốc nhưng chưa có bằng chứng độc lập → chỉ xem xét, không sửa điểm",
    NORMAL: "Bình thường",
    IT_DU_LIEU: "Ít dữ liệu (≤ 5 điểm hợp lệ) → không gắn cờ, giữ nguyên điểm",
    CHUA_DU: "Dữ liệu chưa đầy đủ → không chấm bất thường",
    KHONG_MOC: "Không đủ lớp cùng môn/nhóm môn, cùng giai đoạn, cùng cơ cấu điểm để so",
}

# Cơ cấu điểm của lớp (chỉ so lớp với lớp cùng cơ cấu)
CO_CAU_CHI_THI = "Chỉ có Thi"
CO_CAU_DU = "Có điểm quá trình"

# Loại lớp để so sánh: đồ án chỉ so với đồ án
SS_DO_AN = "Đồ án/TT/KL"
SS_THUONG = "Lớp học (thường + EP)"


@dataclass
class CauHinh:
    """Các ngưỡng của Giải pháp 1 (giá trị mặc định có giải thích bên cạnh)."""

    # --- Dữ liệu ---
    max_it_du_lieu: int = 5          # lớp có ≤ 5 điểm hợp lệ → INSUFFICIENT_DATA (quyết định của đội)
    ty_le_hp_thi_thieu: float = 0.9  # lớp không có CC/KTTX mà HP < 0,9 × Thi → chưa nhập điểm quá trình

    # --- Mốc so sánh ---
    cua_so_nam: int = 1              # so với lớp trong ±1 năm học (cửa sổ 3 năm) vì điểm tăng dần qua các năm
    min_lop_moc: int = 3             # cần ≥ 3 lớp khác để làm mốc

    # --- Ngưỡng điểm ---
    diem_a: float = cf.NGUONG_DIEM_A  # điểm A: ≥ 8,5
    diem_dat: float = cf.NGUONG_DAT   # đạt học phần

    # --- Bước 1: độ lệch ---
    z_lech: float = 2.0              # |z| ≈ 2 → điểm lệch = 0,5 (tâm của hàm sigmoid)
    lech_toi_thieu: float = 0.5      # điểm lệch ≥ 0,5 → coi là "lớp lệch"
    fdr_alpha: float = 0.05          # mức ý nghĩa sau hiệu chỉnh Benjamini–Hochberg

    # --- Bước 2: bằng chứng ---
    bang_chung_toi_thieu: float = 0.5  # độ mạnh bằng chứng ≥ 0,5 → "có bằng chứng"
    min_sv_nang_luc: int = 5         # cần ≥ 5 SV có năng lực nền mới dùng bằng chứng năng lực
    min_phu_nang_luc: float = 0.3    # và ≥ 30% SV của lớp có năng lực nền
    so_lop_khac_nang_luc: int = 2    # SV cần ≥ 2 lớp khác mới có năng lực nền
    co_rut_nang_luc: float = 1.0     # hệ số co rút (shrinkage) năng lực nền về 0
    chenh_kttx_thi_toi_thieu: float = 0.5  # chênh KTTX−Thi phải khác mốc ≥ 0,5 điểm mới tính
    sigma_tuyet_doi: float = 0.5     # σ < 0,5 coi như σ → 0 (nếu mốc không thấp như vậy)
    sigma_ti_le_thap: float = 0.6    # σ lớp < 60% σ mốc bắt đầu bị nghi
    rho_thap: float = 0.20           # tương quan với năng lực nền thấp hơn mức này bị nghi

    # --- Bước 3: chấm điểm ---
    w_quy_tac: float = 0.80          # trọng số điểm quy tắc
    w_ml: float = 0.20               # trọng số điểm Isolation Forest (kiểm tra chéo)
    nguong_ml_cao: float = 0.60      # điểm Isolation Forest ≥ 0,6 → "học máy cũng nghi"
    random_state: int = 42
