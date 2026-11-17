# Kịch bản video demo (khoảng 4 phút)

**Yêu cầu của đề:** video 3–5 phút, đi đủ 3 bước: phát hiện một lớp điểm cao bất thường → hiệu chỉnh điểm → mức năng lực TCI của sinh viên thay đổi.

**Dữ liệu:** video công khai nên **chỉ dùng dữ liệu giả** (`01_du-lieu/video-demo/Du_lieu_demo.csv`). Dữ liệu được sinh ngẫu nhiên, đúng 19 cột như dữ liệu của BTC. Số liệu trên dữ liệu thật nằm trong báo cáo PDF.

**Nhân vật chính của video** (dữ liệu giả, seed 2026; chạy lại `tao_du_lieu_demo.py` thì vẫn ra đúng các mã này):

| | Mã | Số liệu cần nói |
|---|---|---|
| Lớp chấm dễ | **L0537**, môn M001, 2025-2026 HK2 | Nhãn `HIGH_INFLATION`, mức độ bất thường 0,91. Điểm TB lớp 7,99, các lớp tương đương 7,23. Tỷ lệ A 39%, mốc 8%. KTTX − Thi = +2,2 điểm, mức thường +0,8 |
| Hiệu chỉnh | α = 0,09 | Mỗi sinh viên của lớp bị trừ 0,61 điểm |
| Sinh viên | **S00377** | GPA danh nghĩa 3,62 (Advanced) → TCI 3,48 (Proficient). Môn M001: 8,5 (A) → 7,89 (B) |

---

## Chuẩn bị trước khi quay

1. **Tạo dữ liệu demo:** chạy lệnh dưới (mất khoảng 10 giây). Có thể bỏ qua, vì file bấm đúp ở bước 2 tự tạo nếu chưa có.
   ```
   .venv\Scripts\python.exe -X utf8 05_video-demo\tao_du_lieu_demo.py
   ```
2. **Mở dashboard demo:** bấm đúp `05_video-demo\mo-dashboard-demo.bat`. Trình duyệt tự mở `http://localhost:8502`.
   - **Không dùng `mo-dashboard.bat` ở thư mục gốc**, vì file đó hiện dữ liệu thật và lịch sử thật.
3. **Đăng nhập Nhà trường** (mật khẩu `demo`) → tab **Phân tích dữ liệu mới** → **Reset dashboard** → xác nhận. Dashboard trống, sẵn sàng cho cảnh 2.
4. **Trình duyệt:**
   - Toàn màn hình (F11), phóng to 110–125% (Ctrl +) cho chữ dễ đọc.
   - Đóng các tab khác và tắt thông báo Windows.
   - Bấm **Đăng xuất** để bắt đầu video từ chế độ công khai.
5. **Công cụ quay:**
   - Xbox Game Bar: **Win + Alt + R** để bắt đầu/dừng quay; video lưu ở `Video\Captures`.
   - Hoặc OBS Studio.
   - Thu tiếng bằng micro; quay thử 10 giây để kiểm tra âm lượng.
6. **Mẹo:**
   - Quay từng cảnh riêng rồi ghép lại (Clipchamp có sẵn trên Windows 11). Nói sai thì chỉ quay lại một cảnh.
   - Di chuột chậm, dừng 1–2 giây ở chỗ đang nói tới.

---

## Các cảnh

### Cảnh 1 – Mở đầu (0:00–0:25)
**Màn hình:** trang Tổng quan, chế độ công khai (hoặc một slide tiêu đề có tên đội).

**Lời thoại:**
> Xin chào Ban giám khảo, chúng em là đội *We are here for the free food*. Cùng một môn học, có lớp được chấm rộng tay, có lớp bị chấm khắt khe, nên GPA danh nghĩa chưa phản ánh đúng năng lực của sinh viên. Hệ thống của đội giải quyết bài toán này bằng ba bước nối tiếp: phát hiện lớp chấm bất thường, hiệu chỉnh điểm, rồi xếp mức năng lực thực chất TCI. Video này dùng dữ liệu mô phỏng, đúng định dạng 19 cột của Ban tổ chức.

### Cảnh 2 – Nhà trường tải dữ liệu lên (0:25–1:00)
**Thao tác:**
1. Thanh bên trái: **Đăng nhập vai trò Nhà trường** → nhập mật khẩu → Enter.
2. Tab **Phân tích dữ liệu mới**.
3. Kéo `Du_lieu_demo.csv` vào ô **File điểm (CSV)**.
4. Chọn **Phân tích riêng** → bấm **Phân tích**. Chờ khoảng 10 giây.

**Lời thoại:**
> Phòng đào tạo đăng nhập với vai trò Nhà trường và tải lên file điểm của 1.500 sinh viên, 583 lớp học phần. Hệ thống kiểm tra định dạng, rồi chạy cả ba giải pháp trong vài giây.

### Cảnh 3 – Tổng quan (1:00–1:25)
**Thao tác:** tab **Tổng quan**. Di chuột qua 4 thẻ số liệu, rồi qua biểu đồ cột Trước/Sau.

**Lời thoại:**
> Kết quả: 21 lớp có dấu hiệu bất thường, 20 lớp được hiệu chỉnh điểm, và 33 sinh viên đổi mức năng lực. Cột xanh là mức theo GPA danh nghĩa, cột cam là mức theo TCI sau hiệu chỉnh. Giờ chúng ta xem cụ thể một lớp.

### Cảnh 4 – Giải pháp 1: phát hiện lớp L0537 (1:25–2:30)
**Thao tác:**
1. Tab **Lớp học phần**. Dừng ở biểu đồ "Số lớp theo kết luận".
2. Ô **Mã môn** chọn **M001** để lọc; bảng hiện lớp **L0537**.
3. Ô **Chọn một lớp trong danh sách trên** chọn **L0537**. Di chuột qua từng dòng lý do.

**Lời thoại:**
> Lớp L0537 môn M001 bị gắn nhãn HIGH_INFLATION, mức độ bất thường 0,91. Hệ thống không so lớp này với toàn trường, mà chỉ so với các lớp cùng môn, cùng cơ cấu điểm, trong khoảng một năm học. Điểm trung bình lớp là 7,99, trong khi các lớp tương đương chỉ 7,23. Tỷ lệ điểm A là 39%, trong khi mốc chỉ 8%.
>
> Nhưng điểm cao chưa chắc là chấm dễ, vì có thể lớp tập trung sinh viên giỏi. Vì vậy hệ thống chỉ kết luận khi có thêm bằng chứng độc lập. Ở đây có hai bằng chứng. Thứ nhất, chính những sinh viên này ở các môn khác chỉ ở mức bình thường, nhưng ở lớp này lại cao vọt. Thứ hai, điểm quá trình do giảng viên lớp tự chấm cao hơn điểm thi tới 2,2 điểm, trong khi ở các lớp tương đương chỉ 0,8. Lớp chỉ lệch mà không có bằng chứng thì chỉ được đánh dấu "cần xem xét", không bị sửa điểm.

### Cảnh 5 – Giải pháp 2: hiệu chỉnh điểm (2:30–3:10)
**Thao tác:**
1. Tab **Hiệu chỉnh điểm**. Mở **Điểm được hiệu chỉnh như thế nào?**.
2. Trong biểu đồ "Mức hiệu chỉnh của từng lớp", di chuột vào thanh **L0537** để hiện mức −0,61.

**Lời thoại:**
> Chỉ những lớp vừa lệch vừa có bằng chứng mới được hiệu chỉnh, theo công thức: điểm mới bằng điểm cũ trừ một trừ alpha nhân delta. Delta là phần lệch do cách chấm, được lấy thận trọng. Alpha càng nhỏ khi lớp càng bất thường. Với lớp L0537, alpha bằng 0,09, nên mỗi sinh viên bị trừ 0,61 điểm. Mọi sinh viên trong lớp bị trừ như nhau, nên thứ hạng trong lớp không đổi, và không lớp nào bị sửa quá 2 điểm.

### Cảnh 6 – Giải pháp 3: mức TCI của sinh viên thay đổi (3:10–4:00)
**Thao tác:**
1. Tab **Tra cứu sinh viên**, nhập **S00377** → **Tra cứu**.
2. Dừng ở 4 thẻ số liệu, rồi ở phần "Vì sao sinh viên được xếp mức này?".
3. Cuộn xuống bảng **Điểm từng môn**, chỉ vào dòng **M001 – L0537**.

**Lời thoại:**
> Sinh viên S00377 học lớp L0537. Theo GPA danh nghĩa, bạn đạt 3,62, thuộc mức Advanced. Sau hiệu chỉnh, điểm môn M001 giảm từ 8,5, điểm A, xuống 7,89, điểm B. Vì vậy TCI là 3,48 và sinh viên chuyển sang mức Proficient. Hệ thống ghi rõ lý do bằng lời: môn nào, lớp nào, vì sao bị hiệu chỉnh. Phòng đào tạo trả lời được câu hỏi của sinh viên mà không cần đọc mô hình. Lời giải thích được sinh bằng mẫu câu, không gọi AI bên ngoài, nên dữ liệu không rời khỏi máy.

### Cảnh 7 – Chế độ công khai và kết thúc (4:00–4:30)
**Thao tác:** bấm **Đăng xuất**, quay về tab **Tổng quan** và **Lớp học phần**.

**Lời thoại:**
> Ở chế độ công khai, người xem chỉ thấy số liệu tổng hợp. Nhóm dưới 5 sinh viên được hiện là "nhỏ hơn 5", và không có danh sách từng lớp, để không suy ra được giảng viên. Đội đã kiểm chứng hệ thống bằng mô phỏng: cài sai lệch biết trước vào các lớp bình thường và đo xem hệ thống có bắt đúng mà không sửa oan lớp có sinh viên giỏi thật hay không. Kết quả chi tiết trên dữ liệu thật có trong báo cáo kỹ thuật. Cảm ơn Ban giám khảo đã theo dõi.

---

## Kiểm tra trước khi nộp
- [ ] Dài 3–5 phút.
- [ ] Có đủ 3 bước: lớp HIGH_INFLATION → hiệu chỉnh → SV đổi mức TCI.
- [ ] Không lộ dữ liệu thật: không có `Du_lieu.csv` thật, không có lịch sử phân tích thật, không có thư mục `01_du-lieu/raw` trên màn hình.
- [ ] Không lộ mật khẩu thật (chỉ dùng `demo`).
- [ ] Tiếng rõ, không có thông báo cá nhân nào hiện lên màn hình.
