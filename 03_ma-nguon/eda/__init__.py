"""Gói EDA (Exploratory Data Analysis – khám phá dữ liệu) cho FIT Innovation 2026.

Mỗi module lo một việc:
- config.py       : đường dẫn, tên cột, các ngưỡng (8,5 điểm A; 60%; nhóm tối thiểu 5 người...)
- load.py         : đọc CSV và chuyển kiểu dữ liệu (chữ -> số, Có/Không -> True/False)
- privacy.py      : "người gác cổng" – chặn mọi bảng/hình còn Mã SV hoặc có nhóm < 5 người
- quality.py      : kiểm tra chất lượng dữ liệu
- distribution.py : phân bố điểm theo lớp
- hypotheses.py   : kiểm tra các giả thuyết (KTTX − Thi, mốc đổi trọng số, loại lớp)
- baseline.py     : chuẩn bị cho "năng lực nền" (số môn mỗi sinh viên đã học)
- report.py       : ghi kết quả ra file Markdown + lưu hình
"""

import matplotlib

# Dùng backend "Agg": vẽ hình thẳng ra file, không mở cửa sổ.
# Phải đặt TRƯỚC khi bất kỳ module nào import matplotlib.pyplot.
matplotlib.use("Agg")
