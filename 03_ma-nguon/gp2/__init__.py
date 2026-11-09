"""Giải pháp 2 – Hiệu chỉnh điểm (Adjusted_Score / Normalized_GPA).

Theo quyết định của đội:
    - Phương án A sửa điểm cả lớp, chỉ cho lớp "đủ điều kiện hiệu chỉnh" ở Giải pháp 1
      (lệch so với mốc + có bằng chứng do cách chấm), theo cả hai chiều trừ/cộng.
    - Phương án C tính điểm kỳ vọng từng SV, chỉ gắn cờ REVIEW_REQUIRED, không tự đổi điểm.
    - GPA hệ 10 trước/sau; quy đổi thang 4 để ở Giải pháp 3.

Các module: cau_hinh, hieu_chinh (A), ky_vong (C), gpa, quy_trinh, kiem_chung, xuat.
Chạy: 03_ma-nguon/run_gp2.py
"""
