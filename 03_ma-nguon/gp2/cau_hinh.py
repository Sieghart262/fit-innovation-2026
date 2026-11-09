"""Cấu hình Giải pháp 2: ngưỡng hiệu chỉnh và thư mục kết quả."""

from __future__ import annotations

from dataclasses import dataclass

from eda import config as cf

# Kết quả có Mã SV (điểm từng SV) → nằm trong 01_du-lieu/ nên KHÔNG bị đưa lên GitHub.
THU_MUC_KET_QUA = cf.THU_MUC_GOC / "01_du-lieu" / "ket-qua" / "gp2"

REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass
class CauHinhGP2:
    """Các ngưỡng của Giải pháp 2 (giá trị mặc định có giải thích bên cạnh)."""

    # --- Phương án A: chiết khấu α cho lớp đủ điều kiện ---
    alpha_min: float = 0.05            # đề bài yêu cầu 0 < α ≤ 1 → không để α = 0
    dieu_chinh_toi_da: float = 2.0     # mỗi lớp không bị cộng/trừ quá 2 điểm (giới hạn an toàn)

    # --- Phương án C: điểm kỳ vọng từng SV ---
    z_tin_cay: float = 1.96            # khoảng tin cậy 95%
    lech_toi_thieu_diem: float = 1.0   # và phải lệch ≥ 1 điểm mới gắn REVIEW_REQUIRED (bỏ lệch vặt)
    so_lop_khac_toi_thieu: int = 2     # SV cần ≥ 2 lớp khác mới có điểm kỳ vọng

    # --- GPA ---
    lam_tron: int = 2                  # số chữ số thập phân của điểm hiệu chỉnh
