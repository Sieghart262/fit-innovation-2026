"""Giải pháp 1 – Phát hiện lớp học phần có điểm bất thường.

Dựa trên bản đề xuất của một thành viên nhóm (grade_anomaly_detection.py), chỉnh theo
các quyết định của đội:
    - Chỉ gắn HIGH_INFLATION / UNUSUALLY_STEEP khi lớp vừa LỆCH so với mốc vừa có
      BẰNG CHỨNG độc lập rằng độ lệch do cách chấm; lệch mà không có bằng chứng → NEEDS_REVIEW.
    - Mốc: cùng môn → cùng nhóm môn; cùng loại lớp, cùng cơ cấu điểm, trong ±1 năm học.
      Không so với môn khác nhóm.
    - Lớp chưa nhập đủ điểm (vd chưa có điểm quá trình) → INCOMPLETE_DATA, không phải "ép điểm".
    - Lớp ≤ 5 điểm hợp lệ → INSUFFICIENT_DATA nhưng vẫn có mặt trong kết quả.

Các module:
    cau_hinh   – nhãn, ngưỡng, thư mục kết quả
    du_lieu    – chuẩn bị dữ liệu, cơ cấu điểm, lớp dữ liệu chưa đủ
    nang_luc   – năng lực nền của SV (leave-one-class-out)
    dac_trung  – chỉ số thống kê từng lớp
    so_sanh    – so với mốc, p-chart, KS, KTTX − Thi
    cham_diem  – lệch + bằng chứng → nhãn, Anomaly Score, giải thích, Isolation Forest
    quy_trinh  – nối các bước
    kiem_chung – mô phỏng cài bất thường để đo độ chính xác
    xuat       – CSV, biểu đồ, báo cáo
Chạy: 03_ma-nguon/run_gp1.py
"""
