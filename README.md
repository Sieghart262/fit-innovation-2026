# FIT Innovation 2026 – Vòng Bán kết

**NEU Academic Integrity & True Competency Analytics Platform**: hệ thống phân tích điểm gồm 3 giải pháp nối tiếp và một dashboard.

| Giải pháp | Làm gì | Đầu ra |
|---|---|---|
| **GP1** | Phát hiện lớp học phần có điểm bất thường | Anomaly Score 0–1, nhãn `HIGH_INFLATION` / `UNUSUALLY_STEEP` / `SUSPICIOUS_DISTRIBUTION`, lời giải thích từng lớp |
| **GP2** | Hiệu chỉnh điểm | `Adjusted_Score`, `Normalized_GPA`, cờ `REVIEW_REQUIRED` |
| **GP3** | Xếp mức năng lực thực chất | TCI (thang 4), 4 mức Advanced / Proficient / Intermediate / At-Risk, lời giải thích từng SV |
| **Dashboard** | Xem và dùng kết quả trên trình duyệt | Biểu đồ trước/sau, tra cứu, tải dữ liệu mới, lịch sử, báo cáo HTML |

> **Demo trực tuyến:** https://neu-tci-demo.streamlit.app/ (khởi động trống; đăng nhập vai trò Nhà trường rồi tải file điểm CSV lên, hoặc bấm "Phân tích dữ liệu mẫu" để thử bằng dữ liệu giả). **Mật khẩu vai trò Nhà trường** nằm trong file `thong-tin-demo.txt` gửi kèm bài nộp cho Ban tổ chức; file này không có trên GitHub.

> **Người không biết lập trình:** đọc [HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md). Chỉ cần bấm đúp `cai-dat.bat` một lần, sau đó bấm đúp `mo-dashboard.bat` mỗi khi dùng.

## Quy tắc bắt buộc về dữ liệu
- **Không đưa dữ liệu BTC lên GitHub.** Toàn bộ thư mục `01_du-lieu/` đã nằm trong `.gitignore`: dữ liệu gốc, dữ liệu giả, kết quả chạy và lịch sử phân tích.
- **Không đưa dữ liệu vào dịch vụ bên ngoài,** ví dụ công cụ AI online hay host demo. Bản demo công khai dùng dữ liệu giả. Lời giải thích từng lớp, từng SV được sinh bằng mẫu câu, không gọi AI bên ngoài.
- **Chỉ phân tích tổng hợp.** Không cố xác định danh tính SV hay giảng viên.
- **Số liệu công bố ra ngoài** (báo cáo PDF, video, chế độ xem công khai của dashboard) phải ẩn nhóm dưới 5 người, Mã SV và bảng từng lớp. Dùng `03_ma-nguon/eda/privacy.py`.
- **Chỉ giữ trên máy, không đưa lên GitHub:** `06_quan-ly/nhat-ky-AI.md`, `CLAUDE.md`, `.claude/`.

## Cấu trúc thư mục
```
00_de-bai/            đề bài và phân tích đề
01_du-lieu/           (không có trên GitHub) dữ liệu BTC, dữ liệu giả, kết quả, lịch sử phân tích
02_phan-tich/         kết quả EDA (số liệu tổng hợp) và nhận xét
03_ma-nguon/          code
  eda/                  đọc dữ liệu, kiểm tra chất lượng, privacy
  gp1/  gp2/  gp3/      3 giải pháp (mỗi gói có cau_hinh, quy_trinh, kiem_chung, xuat)
  dashboard/            app.py (các trang), giao_dien.py (kiểu dáng), bao_cao.py (báo cáo HTML/ZIP)
  kho_ket_qua.py        kết quả đang dùng, reset, phân tích file mới, lịch sử
  run_eda.py  run_gp1.py  run_gp2.py  run_gp3.py
  tao_du_lieu_gia.py  kiem_tra_bat_loi.py
06_quan-ly/           kế hoạch, phân công
.streamlit/           giao diện dashboard (nền sáng, màu chủ đạo)
cai-dat.bat  mo-dashboard.bat  chay-phan-tich.bat   file bấm đúp cho người không biết code
```

## 1. Cài đặt (làm một lần)
Cần Python 3.11 trở lên; đội đã thử với 3.14. Các lệnh chạy ở **thư mục gốc dự án**.

```bash
git clone https://github.com/Sieghart262/fit-innovation-2026.git
cd fit-innovation-2026
git switch develop
python -m venv .venv
.venv/Scripts/pip install -r 03_ma-nguon/requirements.txt
```

Trên Windows có thể bấm đúp `cai-dat.bat` thay cho 2 lệnh cuối.

## 2. Đặt dữ liệu BTC
Nhận dữ liệu qua kênh nội bộ của nhóm, **không qua GitHub**. Chép vào đúng chỗ dưới đây và giữ nguyên tên file:

```
01_du-lieu/raw/Du_lieu_Ban_Ket_FIT_Innovation/Du_lieu.csv
01_du-lieu/raw/Du_lieu_Ban_Ket_FIT_Innovation/Thoi_khoa_bieu.csv
```

Không bắt buộc: có thể bỏ qua bước này và tải file điểm lên ngay trên dashboard (mục 4).

## 3. Chạy phân tích

| Lệnh | Làm gì | Kết quả ở |
|---|---|---|
| `.venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp3.py` | **Chạy cả 3 giải pháp** (đầu vào của dashboard). Kết quả cũ được cất vào lịch sử trước khi ghi đè | `01_du-lieu/ket-qua/gp1`, `gp2`, `gp3` và `01_du-lieu/lich-su-phan-tich/` |
| `.venv/Scripts/python.exe -X utf8 03_ma-nguon/run_eda.py` | Kiểm tra chất lượng dữ liệu, EDA | `02_phan-tich/02-ket-qua-eda.md` |
| `.venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp1.py` | Chỉ GP1 | `01_du-lieu/ket-qua/gp1/` |
| `.venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp2.py` | GP1 + GP2, chỉ ghi kết quả GP2 | `01_du-lieu/ket-qua/gp2/` |

- **Thêm `--kiem-chung`** để chạy thêm phần kiểm chứng bằng mô phỏng: cài bất thường biết trước vào dữ liệu rồi đo xem code có bắt đúng không. Với `run_gp3.py`, cờ này kiểm chứng cả 3 giải pháp (khoảng 2–3 phút). Không có cờ thì bảng kiểm chứng cũ bị xóa, vì không còn khớp với kết quả mới.
- **Thêm `--du-lieu <file.csv>` và `--ra <thư mục>`** để chạy với file khác, ví dụ dữ liệu giả.
- **Kết quả lặp lại được:** cùng dữ liệu thì luôn ra cùng kết quả, vì seed cố định.
- **Màn hình chỉ in số liệu tổng hợp,** không in dòng điểm nào.

## 4. Dashboard
```bash
$env:FIT_MAT_KHAU_NHA_TRUONG = "<mật khẩu tự đặt>"
.venv/Scripts/streamlit.exe run 03_ma-nguon/dashboard/app.py
```

Phải chạy từ thư mục gốc để Streamlit đọc được `.streamlit/config.toml`. Trên Windows có thể bấm đúp `mo-dashboard.bat`: file này hỏi mật khẩu rồi tự mở trình duyệt.

| Vai trò | Thấy gì |
|---|---|
| **Công khai** | Chỉ số liệu tổng hợp; nhóm dưới 5 SV hiện "<5"; không có bảng từng lớp hay từng SV |
| **Nhà trường** (cần mật khẩu) | Thêm: danh sách lớp kèm lý do, tra cứu SV, phân tích dữ liệu mới, lịch sử phân tích |

- **Phân tích dữ liệu mới:**
  - **Reset** cất kết quả đang dùng vào lịch sử rồi làm trống dashboard.
  - **Tải file CSV 19 cột** lên, chọn *phân tích riêng* hoặc *gộp* với dữ liệu đang hiển thị. Kết quả mới hiện cho mọi người xem; nếu phân tích lỗi thì giữ nguyên kết quả cũ.
- **Lịch sử phân tích:** lưu mọi lần phân tích. Với mỗi lần có thể xem trước, tải **báo cáo HTML** (một file, đủ biểu đồ và lời giải thích, in ra PDF được) hoặc tải **ZIP** toàn bộ kết quả.
- **Biến môi trường tùy chọn:** `FIT_KET_QUA` (thư mục kết quả) và `FIT_LICH_SU` (thư mục lịch sử), dùng khi demo bằng dữ liệu giả.

## 5. Phương pháp tóm tắt
- **GP1:**
  - Một lớp chỉ bị gắn `HIGH_INFLATION` / `UNUSUALLY_STEEP` khi **vừa lệch** so với các lớp tương đương **vừa có bằng chứng độc lập** do cách chấm. Lớp tương đương là lớp cùng môn (hoặc cùng nhóm môn), cùng cơ cấu điểm, cách nhau không quá 1 năm học.
  - Có 3 loại bằng chứng:
    - SV ở lớp này cao/thấp hơn chính họ ở các lớp khác;
    - KTTX lệch Thi **đúng chiều** và vượt mức thường ≥ 1 điểm;
    - phân phối biến dạng (σ quá nhỏ, KTTX trùng Thi…).
  - Lớp chỉ lệch mà không có bằng chứng thì gắn `NEEDS_REVIEW` và không sửa điểm.
- **GP2:**
  - `Adjusted_Score = Điểm − (1 − α) × Δ`, chỉ áp cho lớp đủ điều kiện ở GP1.
  - α = 1 − Anomaly Score. Δ là phần lệch do cách chấm, lấy thận trọng.
  - Mỗi lớp không bị cộng/trừ quá 2 điểm.
  - Điểm kỳ vọng từng SV chỉ dùng để gắn cờ `REVIEW_REQUIRED`, không tự đổi điểm.
- **GP3:**
  - TCI là trung bình có trọng số tín chỉ của điểm thang 4 (bảng quy đổi NEU) tính từ `Adjusted_Score`.
  - Có tính đồ án/thực tập/khóa luận. Không tính lượt vắng thi.
  - SV học dưới 3 môn có độ tin cậy "Thấp".

## 6. Thử với dữ liệu giả
Dữ liệu giả hoàn toàn ngẫu nhiên, dùng được cho demo công khai.

```bash
.venv/Scripts/python.exe -X utf8 03_ma-nguon/tao_du_lieu_gia.py
.venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp3.py --du-lieu 01_du-lieu/gia-lap/Du_lieu.csv --ra 01_du-lieu/gia-lap/ket-qua
.venv/Scripts/python.exe -X utf8 03_ma-nguon/kiem_tra_bat_loi.py
```

- **`kiem_tra_bat_loi.py`** cài lỗi vào cả 19 cột, rồi kiểm tra phần kiểm tra chất lượng dữ liệu có bắt đủ lỗi không.
- **Muốn mở dashboard với dữ liệu giả:** đặt `$env:FIT_KET_QUA = "01_du-lieu/gia-lap/ket-qua"` trước khi chạy Streamlit.

## 7. Quy trình làm việc với Git
- **`main`** là bản ổn định; **`develop`** là nơi gộp code của cả nhóm.
- **Mỗi phần việc** tách một nhánh riêng từ `develop`. Làm xong thì mở PR vào `develop`.
- **Trước khi commit,** chạy `git status` và kiểm tra không có file trong `01_du-lieu/`, không có `nhat-ky-AI.md` hay `CLAUDE.md`.
