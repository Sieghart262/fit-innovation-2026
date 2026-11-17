# Hướng dẫn sử dụng

Hệ thống phân tích điểm của sinh viên, gồm 3 việc:
1. **Tìm lớp chấm điểm bất thường:** lớp chấm quá dễ, quá khắt khe, hoặc điểm trong lớp giống nhau bất thường.
2. **Hiệu chỉnh điểm** của các lớp đó cho công bằng.
3. **Xếp mức năng lực** của từng sinh viên theo điểm đã hiệu chỉnh.

Kết quả hiện trên một **dashboard**, tức một trang web mở bằng trình duyệt ngay trên máy của bạn.

Hướng dẫn này dành cho **người không biết lập trình**. Bạn chỉ cần bấm đúp vào 3 file có sẵn trong thư mục dự án:

| File | Làm gì | Khi nào |
|---|---|---|
| `cai-dat.bat` | Cài các thứ cần thiết | **Một lần** trên mỗi máy |
| `mo-dashboard.bat` | Mở dashboard | Mỗi lần muốn xem |
| `chay-phan-tich.bat` | Phân tích file điểm đặt sẵn trong thư mục dự án | Không bắt buộc, vì có thể tải file điểm lên ngay trên dashboard |

---

## 1. Cài Python (chỉ làm một lần)
Máy cần **Windows 10 hoặc 11** và có **Internet** khi cài đặt.

1. Vào trang https://www.python.org/downloads/ và bấm nút **Download Python** (màu vàng).
2. Mở file vừa tải về.
3. Ở màn hình đầu tiên, **tích ô "Add python.exe to PATH"** ở phía dưới, rồi bấm **Install Now**. Nếu quên tích ô này, các bước sau sẽ báo lỗi.
4. Chờ cài xong rồi bấm **Close**.

## 2. Cài đặt dự án (chỉ làm một lần)
1. Mở thư mục dự án, tức thư mục có các file `cai-dat.bat`, `mo-dashboard.bat`.
2. Bấm đúp **`cai-dat.bat`**. Một cửa sổ đen hiện lên và tự cài, mất khoảng 2–5 phút.
3. Khi thấy dòng **"CÀI ĐẶT XONG"**, nhấn phím bất kỳ để đóng cửa sổ.

> Nếu Windows hiện cảnh báo "Windows protected your PC", bấm **More info** rồi **Run anyway**. Các file `.bat` chỉ chạy lệnh trong thư mục dự án.

## 3. Mở dashboard
1. Bấm đúp **`mo-dashboard.bat`**.
2. Cửa sổ hỏi **mật khẩu**:
   - Gõ một mật khẩu tùy ý rồi nhấn Enter. Mật khẩu này dùng để đăng nhập vai trò **Nhà trường** trên dashboard; chỉ cần nhớ trong lần chạy này.
   - Nếu chỉ cần xem số liệu tổng hợp thì bỏ trống và nhấn Enter.
3. Trình duyệt tự mở dashboard. Nếu không tự mở, mở trình duyệt và vào **http://localhost:8501**.
4. **Giữ cửa sổ đen mở** trong lúc dùng. Đóng cửa sổ đen là tắt dashboard.

## 4. Dùng dashboard

### Hai vai trò
| Vai trò | Thấy gì |
|---|---|
| **Công khai** (mặc định) | Chỉ số liệu tổng hợp. Nhóm dưới 5 sinh viên hiện "<5". Không có danh sách từng lớp hay từng sinh viên. |
| **Nhà trường** | Xem hết: từng lớp, từng sinh viên, tải dữ liệu mới, lịch sử phân tích. |

Để vào vai trò Nhà trường: ở thanh bên trái, bấm **"Đăng nhập vai trò Nhà trường"**, gõ mật khẩu đã đặt ở mục 3, rồi bấm **Đăng nhập**.

### Các trang
| Trang | Dùng để |
|---|---|
| **Tổng quan** | Bao nhiêu sinh viên ở mỗi mức năng lực, trước và sau hiệu chỉnh; bao nhiêu sinh viên đổi mức |
| **Lớp học phần** | Bao nhiêu lớp có dấu hiệu bất thường. Nhà trường lọc được theo kết luận, năm học, môn, và chọn một lớp để xem **vì sao** lớp đó bị đánh giá như vậy |
| **Hiệu chỉnh điểm** | Lớp nào được cộng hoặc trừ điểm, bao nhiêu điểm |
| **Tra cứu sinh viên** (nhà trường) | Gõ mã sinh viên để xem mức năng lực, lý do và điểm từng môn trước/sau hiệu chỉnh |
| **Phân tích dữ liệu mới** (nhà trường) | Reset dashboard, tải file điểm mới lên để phân tích |
| **Lịch sử phân tích** (nhà trường) | Xem lại và tải về mọi lần phân tích trước |

### Bốn mức năng lực
| Mức | Ý nghĩa | Điều kiện |
|---|---|---|
| Advanced | Xuất sắc | Từ 3,60 |
| Proficient | Khá, giỏi | Từ 3,20 đến dưới 3,60 |
| Intermediate | Trung bình | Từ 2,50 đến dưới 3,20 |
| At-Risk | Cần hỗ trợ | Dưới 2,50 |

Điểm xét là **TCI**: điểm trung bình thang 4 tính từ điểm đã hiệu chỉnh. Sinh viên không có môn nào có điểm hợp lệ được ghi **"Chưa đủ dữ liệu"**.

## 5. Phân tích một file điểm mới (vai trò Nhà trường)
Vào trang **Phân tích dữ liệu mới**.

**Nếu muốn bắt đầu lại từ đầu** thì bấm **Reset dashboard**, rồi bấm **Đồng ý reset**.
- Dashboard sẽ trống với mọi người xem.
- Kết quả cũ **không bị mất**: nó được cất vào **Lịch sử phân tích**.

**Để phân tích một file mới:**
1. **Chuẩn bị file:** file **CSV** có đủ **19 cột**, tên cột giống hệt file điểm gốc. Bấm **"Tải file mẫu"** để có file chứa đúng dòng tên cột.
   - Nếu dữ liệu đang ở dạng Excel: mở bằng Excel, chọn **File → Save As → "CSV UTF-8 (Comma delimited)"**.
2. **Tải file lên:** kéo thả vào ô "File điểm", hoặc bấm **Upload**.
3. **Chọn cách phân tích:**
   - **Phân tích riêng file này:** dashboard chỉ dùng dữ liệu trong file mới.
   - **Gộp thêm vào dữ liệu đang hiển thị:** ghép file mới với dữ liệu đang có rồi phân tích lại toàn bộ. Nếu cùng một sinh viên trong cùng một lớp có ở cả hai file thì dùng dòng của file mới.
4. **Bấm Phân tích** và chờ khoảng 30 giây. Dashboard tự chuyển sang kết quả mới, với **mọi người xem**.

Nếu file sai cấu trúc, dashboard báo rõ lỗi (ví dụ thiếu cột nào) và **giữ nguyên kết quả cũ**.

> File chỉ được xử lý trên máy đang chạy dashboard, không gửi đi đâu.

### 19 cột bắt buộc (đúng thứ tự tên này)
Năm học · Học kỳ · Mã môn · Nhóm môn · Số TC · Là đồ án/thực tập/khóa luận · Lớp mang mã EP · Mã lớp học phần · Sĩ số lớp (trong dữ liệu) · Mã SV · Khóa SV · Khoa của SV · CC · KTTX1 · KTTX2 · KTTX (TB) · Thi · Điểm HP (thang 10) · Cơ cấu trọng số suy ra (CC/KTTX/Thi, %)

## 6. Lịch sử phân tích và tải báo cáo (vai trò Nhà trường)
Trang **Lịch sử phân tích** liệt kê mọi lần phân tích: thời gian, tên dữ liệu, số sinh viên, số lớp. Chọn một lần trong danh sách rồi:
- **Tải báo cáo đầy đủ (HTML):** một file duy nhất, có đủ biểu đồ và lời giải thích như trên dashboard. Mở bằng trình duyệt; muốn có PDF thì bấm **Ctrl + P → Save as PDF**.
- **Tải toàn bộ file kết quả (ZIP):** có thêm danh sách xếp mức từng sinh viên, điểm đã hiệu chỉnh và file điểm đầu vào. Các file CSV mở được bằng Excel.
- **Bật "Xem trước lần phân tích này"** để xem lại các trang Tổng quan, Lớp học phần, Hiệu chỉnh điểm của lần đó.

## 7. Phân tích file điểm đặt sẵn (không bắt buộc)
Cách này dành cho trường hợp muốn phân tích mà không cần mở dashboard.
1. Chép file **`Du_lieu.csv`** vào thư mục: `01_du-lieu\raw\Du_lieu_Ban_Ket_FIT_Innovation\`.
2. Bấm đúp **`chay-phan-tich.bat`** và chờ khoảng 1 phút, đến khi thấy chữ **"XONG"**.
3. Mở dashboard (mục 3). Nếu dashboard đang mở thì chỉ cần tải lại trang trình duyệt (phím F5).

Kết quả cũ (nếu có) được tự cất vào Lịch sử phân tích trước khi thay bằng kết quả mới.

## 8. Lỗi thường gặp
| Hiện tượng | Cách xử lý |
|---|---|
| Cửa sổ báo "Máy chưa có Python" | Làm lại mục 1, nhớ tích ô **Add python.exe to PATH** |
| Cửa sổ báo "Chưa cài đặt" | Bấm đúp `cai-dat.bat` trước |
| Trình duyệt báo "This site can't be reached" | Cửa sổ đen của `mo-dashboard.bat` đã bị đóng; bấm đúp lại file này |
| Không thấy trang "Phân tích dữ liệu mới" | Chưa đăng nhập vai trò Nhà trường (mục 4) |
| Đăng nhập báo "Chưa đặt mật khẩu" | Lúc mở `mo-dashboard.bat` đã bỏ trống mật khẩu. Đóng cửa sổ đen rồi mở lại và gõ mật khẩu |
| File tải lên báo "thiếu cột" | So tên cột với file mẫu (mục 5); lưu lại dạng "CSV UTF-8" |
| Báo lỗi "không phải mã hóa UTF-8" | Mở file bằng Excel → Save As → "CSV UTF-8 (Comma delimited)" |

## 9. Lưu ý về dữ liệu
- Dữ liệu điểm và mọi kết quả chỉ nằm trong thư mục `01_du-lieu\` trên máy này. **Không** gửi thư mục này qua email, mạng xã hội hay đưa lên Internet.
- Báo cáo và file tải về từ vai trò Nhà trường là **tài liệu nội bộ**, vì có mã lớp và mã sinh viên.
- Muốn trình diễn công khai thì dùng chế độ **Công khai** của dashboard, hoặc dùng dữ liệu giả.
