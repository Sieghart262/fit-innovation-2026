"""Giải pháp 3 – Phân loại năng lực thực chất (TCI) và dashboard.

    TCI = trung bình có trọng số tín chỉ của điểm thang 4 (bảng quy đổi NEU) tính từ điểm đã
    hiệu chỉnh ở Giải pháp 2; xếp 4 mức Advanced / Proficient / Intermediate / At-Risk theo đề.
    Có lời giải thích từng SV (mẫu câu, không dùng AI bên ngoài) và độ tin cậy (< 3 môn → thấp).

Các module: cau_hinh, tci, giai_thich, quy_trinh (chạy GP1 → GP3), kiem_chung, xuat.
Chạy: 03_ma-nguon/run_gp3.py (ghi kết quả cả 3 giải pháp); dashboard: 03_ma-nguon/dashboard/app.py
"""
