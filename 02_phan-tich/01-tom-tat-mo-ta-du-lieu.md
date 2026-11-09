# Tóm tắt mô tả dữ liệu & hệ quả cho giải pháp

Nguồn: `01_du-lieu/raw/.../Mo_ta_du_lieu_diem.docx` và `Tu_dien_du_lieu.csv` (đọc ngày 06/11/2026). Chưa đọc các file dữ liệu điểm và thời khóa biểu.

## ⚠️ Điều kiện sử dụng dữ liệu (BTC quy định)
> Chỉ phân tích tổng hợp. Không xác định danh tính SV/GV; **không đưa vào dịch vụ bên ngoài**; không chia sẻ ngoài phạm vi cuộc thi.

Hệ quả cần làm rõ với BTC / tự tuân thủ:
- **Không commit dữ liệu thật lên GitHub công khai** → thêm `01_du-lieu/` vào `.gitignore`. Demo dùng dữ liệu giả lập, hoặc cho người dùng tự tải file lên.
- Deploy demo lên cloud có chứa dữ liệu thật → **hỏi BTC trước**.
- Gửi nội dung dòng dữ liệu cho công cụ AI (ChatGPT, Claude…) có thể bị coi là "đưa vào dịch vụ bên ngoài" → **hỏi BTC trước**. An toàn hơn: chỉ đưa cho AI tên cột và số liệu tổng hợp, còn code thì chạy trên máy mình.

## Các file
| File | Nội dung |
|---|---|
| `Du_lieu.csv` | Bảng chính: 1 dòng = điểm của 1 SV trong 1 lớp học phần. **38.342 lượt, 5.067 SV, 877 lớp, 93 môn**, từ 2019-2020 đến 2025-2026 |
| `Diem_thanh_phan_2019_2026.xlsx` | 4 sheet: Giai_thich, Tu_dien_du_lieu, Du_lieu (giống CSV), **Lop_hoc_phan** (tổng hợp theo lớp, 877 dòng: TB CC/KTTX/Thi/HP, tỷ lệ HP ≥4,0/≥4,5/≥8,5) |
| `Tu_dien_du_lieu.csv` | Từ điển cột |
| `Thoi_khoa_bieu.csv` | 1.170 dòng lịch học, 2020-2021 đến 2026-2027 |

## Các cột chính của `Du_lieu.csv`
Năm học · Học kỳ (1, 2, 3 = hè) · Mã môn (M###) · Nhóm môn (N1–N8) · Số TC · Là đồ án/thực tập/khóa luận · Lớp EP · Mã lớp học phần (L####) · Sĩ số lớp · Mã SV (S#####) · Khóa SV (K58–K67) · Khoa của SV (KH##) · **CC** (chuyên cần) · **KTTX1, KTTX2, KTTX (TB)** (điểm quá trình) · **Thi** (cuối kỳ) · **Điểm HP** (tổng kết, thang 10, lần 1) · Cơ cấu trọng số suy ra (10/20/70 trước HK2 2021-22, sau đó 10/40/50).

## Những điều quan trọng → ảnh hưởng trực tiếp tới thiết kế

| Sự thật trong dữ liệu | Hệ quả cho giải pháp |
|---|---|
| **Không có điểm đầu vào, không có ngành** (chỉ có khoa), không có GV, không có hình thức thi | "Năng lực nền tảng" phải **tự xây từ dữ liệu**, vd. điểm TB của SV ở *các môn khác* (bỏ môn đang xét ra). "Mặt bằng ngành" thay bằng Khoa + Khóa + Nhóm môn |
| **KTTX do GV tự chấm; Thi do 2 GV chấm** → hai thành phần không cùng chuẩn | Insight mạnh: lạm phát điểm thường nằm ở **KTTX**. Có thể dùng chênh lệch KTTX − Thi của lớp làm tín hiệu bất thường, và coi điểm Thi là "neo" khách quan hơn |
| So sánh giữa các môn khó vì không biết hình thức thi | Mặt bằng so sánh nên là **chính môn đó qua các năm/các lớp** (cùng Mã môn), không so với môn khác |
| Đồ án/thực tập/khóa luận chấm khác (2.103 dòng) | **Tách riêng**, không đưa vào phát hiện bất thường kiểu lớp thường |
| Lớp EP (2.726 dòng) | Nên so sánh riêng hoặc đưa thêm biến EP vào mô hình |
| **Điểm HP = 0 gồm cả vắng thi/bỏ học** | Loại khỏi thống kê phân phối điểm, hoặc xử lý riêng, để không làm méo σ và điểm TB |
| Ô trống ≠ điểm 0. 2019-2020 thiếu CC/KTTX; một số lớp 2025-2026 chưa có Thi/HP | Lọc theo cột có dữ liệu; ghi rõ cách xử lý trong báo cáo |
| Trọng số thay đổi từ HK2 2021-22 (KTTX 20% → 40%) | Có thể giải thích phần nào xu hướng điểm tăng theo thời gian → **phải tách khỏi "lạm phát"** |
| Chỉ có điểm lần 1 | Không cần xử lý thi lại |
| 38.342 dòng < 10⁵ | Đề yêu cầu chạy tốt khi n > 10⁵ → cần **test thêm với dữ liệu nhân bản/giả lập** để chứng minh |
| Lớp sĩ số nhỏ | Z-score/σ không ổn định → đặt ngưỡng sĩ số tối thiểu hoặc dùng kỹ thuật co về trung bình (shrinkage) |

## Thời khóa biểu – giá trị hạn chế
- Mã HP / Mã LHP **đánh mã riêng, không nối được** với Mã môn / Mã lớp của `Du_lieu.csv`. Chỉ đối chiếu được ở mức tổng hợp (Năm học, Học kỳ, Số TC).
- 1 dòng = 1 lịch học, không phải 1 lớp (1.090 lớp / 1.170 dòng).
- Có 32 dòng ghi năm học chỉ một năm (vd "2023") → phải quyết định xử lý và nêu rõ trong báo cáo.
- Năm 2026-2027 chưa có điểm.
- → Đề xuất: dùng ở mức phụ (bối cảnh, tỷ lệ lớp học buổi sáng/chiều theo học kỳ…), **không phải trọng tâm**.
