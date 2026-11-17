"""Cấu hình Giải pháp 3: bảng quy đổi thang 4 của NEU, ngưỡng xếp mức TCI, thư mục kết quả."""

from __future__ import annotations

from dataclasses import dataclass

from eda import config as cf

# Bảng xếp loại SV có Mã SV → nằm trong 01_du-lieu/ nên KHÔNG bị đưa lên GitHub.
THU_MUC_KET_QUA = cf.THU_MUC_GOC / "01_du-lieu" / "ket-qua" / "gp3"

# Quy đổi thang 10 → chữ → thang 4 theo quy chế NEU (qua môn khi HP ≥ 4,5).
# (ngưỡng dưới, điểm chữ, thang 4), xét từ trên xuống; điểm được làm tròn 1 chữ số trước khi xét.
BANG_QUY_DOI = [
    (9.0, "A+", 4.0),
    (8.5, "A", 4.0),
    (8.0, "B+", 3.5),
    (7.0, "B", 3.0),
    (6.5, "C+", 2.5),
    (5.5, "C", 2.0),
    (5.0, "D+", 1.5),
    (4.5, "D", 1.0),
    (0.0, "F", 0.0),
]

# Mức năng lực theo đề BTC: (ngưỡng dưới của TCI, tên mức), xét từ trên xuống.
MUC_NANG_LUC = [
    (3.60, "Advanced"),
    (3.20, "Proficient"),
    (2.50, "Intermediate"),
    (0.00, "At-Risk"),
]
THU_TU_MUC = [m for _, m in MUC_NANG_LUC]  # Advanced → At-Risk
CHUA_DU_DU_LIEU = "Chưa đủ dữ liệu"        # SV không có môn nào có điểm hợp lệ → chưa tính được TCI

DO_TIN_CAY_THAP = "Thấp"
DO_TIN_CAY_DU = "Bình thường"


@dataclass
class CauHinhGP3:
    """Các ngưỡng của Giải pháp 3."""

    so_mon_tin_cay: int = 3          # SV học dưới 3 môn → độ tin cậy thấp (quyết định của đội)
    so_ly_do_toi_da: int = 3         # lời giải thích nêu tối đa 3 môn ảnh hưởng nhiều nhất
