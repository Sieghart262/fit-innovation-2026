# Đề bài Bán kết FIT Innovation 2026 – Bản lưu & phân tích

Nguồn: https://fit.neu.edu.vn/post/de-bai-chi-tiet-vong-ban-ket-fit-innovation-2026 (đăng 29/10/2026)
Hạn nộp gốc trên trang: 23h59 ngày 07/11/2026 — **BTC đã điều chỉnh, xem `06_quan-ly/ke-hoach.md`**.

## Tên đề
Xây dựng Mô hình Công nghệ Nâng cao Liêm chính Học thuật và Phân loại Trình độ Thực chất trong Hệ sinh thái Smart Campus NEU
(NEU Academic Integrity & True Competency Analytics Platform).

## Vấn đề cốt lõi (nói đơn giản)
Cùng một môn, lớp này chấm dễ (nhiều điểm A), lớp kia chấm khó. GPA danh nghĩa vì thế không công bằng.
Nhà trường cần hệ thống: (1) tìm lớp có điểm "lạ", (2) sửa điểm cho công bằng, (3) xếp loại sinh viên theo năng lực thật.

Nguyên nhân sai lệch đề bài nêu: chênh lệch độ khó đề giữa các ca thi, tiêu chí chấm không đồng nhất giữa nhóm lớp, sai lệch dữ liệu.

## Ba giải pháp bắt buộc (dây chuyền GP1 → GP2 → GP3)

| # | Giải pháp | Làm gì | Đầu ra bắt buộc |
|---|---|---|---|
| 1 | Phát hiện lớp học phần bất thường | Với mỗi lớp: điểm TB lệch so với mặt bằng ngành/khóa (Z-score, p-value); σ quá nhỏ (σ→0); tỷ lệ điểm A [8,5–10] vượt ngưỡng (vd >60%); điểm môn không tương quan với năng lực nền của SV | Bảng xếp hạng lớp nghi vấn + **Anomaly Score 0.0–1.0** + nhãn `HIGH_INFLATION` (lạm phát điểm cao) / `UNUSUALLY_STEEP` (điểm bị ép quá thấp) / `SUSPICIOUS_DISTRIBUTION` (phân phối biến dạng) |
| 2 | Hiệu chỉnh điểm | Chọn/kết hợp: (a) Z-score theo lớp `Z = (X − μc)/σc`; (b) trọng số chiết khấu 0<αc≤1, αc giảm khi Anomaly Score tăng; (c) hồi quy/ML dự báo điểm kỳ vọng X̂ từ môn cơ sở ngành, nếu \|X − X̂\| vượt khoảng tin cậy 95% → `REVIEW_REQUIRED` + đề xuất Adjusted_Score | Bảng điểm **Adjusted_Score / Normalized_GPA** |
| 3 | Phân loại năng lực thực chất | Tính **TCI** cho từng SV từ dữ liệu GP2 | Danh sách phân loại + **báo cáo giải thích (Explainable AI)** + **dashboard/Web API** biểu đồ phân phối Trước/Sau |

Ngưỡng TCI (thang 4):
- **Advanced**: TCI ≥ 3.60
- **Proficient**: 3.20 ≤ TCI < 3.60
- **Intermediate**: 2.50 ≤ TCI < 3.20
- **At-Risk / Beginner**: TCI < 2.50

## Điểm cần chú ý
- "n > 105" trong tiêu chí chấm nhiều khả năng là **n > 10⁵** (>100.000 dòng) → code phải xử lý nhanh dữ liệu lớn.
- "Điểm năng lực nền tảng" không có định nghĩa sẵn → đội tự chọn và giải thích trong báo cáo.
- TCI ở thang 4 → cần bảng quy đổi điểm 10 → chữ → thang 4 của NEU.
- Không có đáp án đúng duy nhất → điểm nằm ở **căn cứ thống kê** và **khả năng giải thích**.

## Sản phẩm nộp (qua cổng trực tuyến)
1. **Báo cáo kỹ thuật PDF ≤ 15 trang**: toán học + thuật toán 3 giải pháp; biểu đồ GPA danh nghĩa vs TCI; **bắt buộc** "Phụ lục kê khai ứng dụng AI" (công cụ, prompt, mô hình – Mục 3.4 thể lệ).
2. **GitHub + link demo**: code gọn, có `README.md`; dashboard hoặc Web API nhận dữ liệu điểm → trả kết quả phân loại.
3. **Video demo 3–5 phút**: phát hiện 1 lớp điểm cao bất thường → hiệu chỉnh → thứ hạng TCI thay đổi.

## Tiêu chí chấm (100 điểm)
| Tiêu chí | % | Ý nghĩa cho quản lý |
|---|---|---|
| Đúng đắn & sáng tạo thuật toán | 40 | Ưu tiên số 1 |
| Demo & code hoàn thiện | 30 | Chạy ổn định, biểu đồ Before/After rõ |
| Thực tiễn & mở rộng | 20 | Dễ tích hợp Smart Campus, chạy dữ liệu lớn |
| Báo cáo & Phụ lục AI | 10 | Mạch lạc, kê khai AI minh bạch |

## Cuộc thi nhắm tới gì
Đánh giá khả năng sinh viên (đóng vai kỹ sư EdTech) biến bài toán quản trị giáo dục thật thành sản phẩm dữ liệu/AI dùng được:
tư duy thống kê đúng · công bằng & giải thích được · sản phẩm chạy thật · dùng AI có trách nhiệm, minh bạch.

## Kiến thức cần bổ sung (ưu tiên từ trên xuống)
- **A. Thống kê cơ bản**: trung bình, độ lệch chuẩn, histogram, Z-score, p-value, t-test/chi-square, khoảng tin cậy 95%, tương quan. (Khan Academy Statistics, StatQuest)
- **B. Quy chế điểm NEU**: thang 10 → chữ → thang 4, GPA tích lũy theo tín chỉ.
- **C. Công cụ**: Python + pandas, scikit-learn (hồi quy, Isolation Forest), Plotly, Streamlit hoặc FastAPI, Git/GitHub, deploy (Streamlit Community Cloud / Render).
- **D. Quản lý dự án**: chốt MVP đủ 3 giải pháp trước, nâng cấp sau; chia việc; mốc kiểm tra; checklist nộp bài.
- **E. Liêm chính khi dùng AI**: đọc Mục 3.4 thể lệ; ghi nhật ký prompt từ đầu (`06_quan-ly/nhat-ky-AI.md`).
