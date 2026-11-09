# Nhận xét kết quả EDA (dữ liệu thật)

- **Nguồn:** `02_phan-tich/02-ket-qua-eda.md` và các hình trong `02_phan-tich/hinh/`. Báo cáo do người dùng tự chạy trên máy lúc 21:23 ngày 07/11/2026.
- **Người viết:** Claude Code (Claude Opus 5.5), ghi ngày 08/11/2026. Chỉ đọc báo cáo số liệu tổng hợp, **không đọc dòng dữ liệu điểm**.
- **Các mã lớp/môn nêu bên dưới** là mã đã ẩn danh của BTC, lấy từ bảng tổng hợp (nhóm ≥ 5 SV).

**Tóm tắt:** Dữ liệu sạch, khớp mô tả. Điểm tăng theo thời gian, nhưng trong cùng một môn thì gần như không đổi. Rủi ro lớn nhất là năng lực nền chỉ tính tin cậy được cho một phần sinh viên.

---

## 1. Chất lượng dữ liệu

| Hạng mục | Kết quả | Ghi chú / việc cần làm |
|---|---|---|
| Đối chiếu mô tả (mục 1.1) | Toàn ✅: 38.342 dòng, 5.067 SV, 877 lớp, 93 môn. Thời khóa biểu khớp | – |
| Khóa SV (mục 1.2) | 73 ô bị báo "sai định dạng" | Dữ liệu có K56 và K57, trong khi mô tả ghi K58–K67. Có lẽ mô tả chưa đầy đủ chứ dữ liệu không sai. Đề xuất mở rộng quy ước thành K56–K67 (chờ xác nhận) |
| Khoa của SV (mục 1.2) | 36 ô trống | Mô tả không nhắc tới. Nhỏ, nhưng cần ghi vào báo cáo PDF |
| Thi trống (mục 1.3) | Khoảng 10% mỗi năm trong 2020–2023, trong khi HP chỉ trống khoảng 2% | Khoảng 1.800 lượt có HP nhưng không có điểm Thi; 542 lượt trong đó có HP = 0 với Thi trống. Cần tìm hiểu thêm |
| HK3 2025-26 | 35 SV. HP trung bình 3,49 trong khi Thi trung bình 6,98; không có KTTX | Điểm HP có vẻ chưa nhập đủ → loại khỏi phân tích xu hướng |
| HK3 2022-23 | Chỉ 5 SV | Quá ít → loại khỏi phân tích xu hướng |

## 2. Phân bố điểm theo lớp

- **Mặt bằng lớp thường:**
  - HP trung bình 7,67.
  - Tỷ lệ điểm A của mỗi lớp: trung vị 30%, trung bình 35,5%.
- **Tỷ lệ lớp có trên 60% điểm A:**
  - lớp thường 17,2%;
  - lớp EP 29%;
  - đồ án / thực tập / khóa luận 78%.
- **Ngưỡng cố định 60% không dùng được**
  - Tỷ lệ lớp thường vượt 60% tăng từ **2,4%** (2019-20) lên **35,2%** (2025-26).
  - Nếu giữ ngưỡng cố định, khoảng một phần ba số lớp năm gần nhất sẽ bị gắn cờ.
  - → Giải pháp 1 cần ngưỡng **tương đối**: so với các lớp khác cùng môn và cùng giai đoạn.
- **KTTX và Thi (hình 03)**
  - KTTX dồn vào các số tròn 7, 8, 9 và cao hơn Thi khoảng 1 điểm.
  - Thi trải rộng hơn.
  - Đây đúng là dấu hiệu của điểm do giảng viên tự chấm, so với điểm thi tập trung.
- **Mẫu đáng ngờ: KTTX trung bình bằng y hệt Thi trung bình (hình 05)**
  - Các lớp có σ nhỏ nhất (σ 0,2–0,36, tỷ lệ A 90–100%) đều có TB KTTX = TB Thi, đúng tới 3 chữ số.
  - Các lớp: L0751, L0605, L0325, L0521, L0377, L0453, L0647, L0687, L0739.
  - Các lớp này thuộc các môn M034, M051, M067.
  - Có thể liên quan tới cơ cấu trọng số 10/0/90 (174 + 937 lượt), tức KTTX được chép từ Thi.
  - → Đây là ứng viên cho nhãn `SUSPICIOUS_DISTRIBUTION`, nhưng **phải kiểm tra ở từng dòng trước khi gắn nhãn**, vì có thể chỉ là cách nhập điểm.
- **Môn dễ ở mọi lớp**
  - M013 và M008 nhiều năm liền nằm trong top tỷ lệ A.
  - Nếu môn nào cũng dễ ở mọi lớp thì so với "lớp khác cùng môn" sẽ không phát hiện được.
  - → Cần thêm một mốc so sánh thứ hai: cùng Nhóm môn hoặc cùng Khoa.

## 3. Giả thuyết

### A. Chênh lệch KTTX − Thi (mục 3.1)
- **Số liệu chính:**
  - Chênh lệch trung bình là 1,049 điểm.
  - 35 lớp có z > 2 và 22 lớp có z < −2.
  - Chênh lệch trung bình tăng từ 0,896 trước mốc lên 1,101 sau mốc.
- **Ngược dự đoán:** tương quan giữa chênh lệch và tỷ lệ A là ρ = −0,518. Lớp nhiều điểm A lại có chênh lệch **nhỏ**, vì điểm Thi của các lớp đó cũng cao.
  - → Chênh lệch và tỷ lệ A là **hai tín hiệu bổ sung cho nhau**. Anomaly Score cần kết hợp cả hai, không dùng cái này thay cái kia.
- **z cao chưa chắc là chênh lệch lớn:** ví dụ L0244 chỉ chênh 0,95 điểm nhưng z = 5,56, vì các lớp khác cùng môn gần như không chênh.
  - → Kết hợp z với một **ngưỡng chênh lệch tối thiểu** tính bằng điểm.

### B. Đổi trọng số ở HK2 2021-22 (mục 3.2)
- **Tính chung toàn trường:**
  - HP tăng 0,433 điểm (p < 0,001).
  - Tỷ lệ A tăng từ 28,7% lên 40,1%.
- **Chỉ so cùng một môn:**
  - HP trung bình chỉ tăng **0,016 điểm**.
  - 18 môn tăng, 18 môn giảm.
  - Kiểm định Wilcoxon cho p = 0,834.
  - → **Không có bằng chứng** rằng đổi trọng số làm tăng điểm trong cùng một môn.
- **Kết luận:** điểm tăng chung chủ yếu vì hai giai đoạn **học những môn khác nhau**.
  - → Mốc so sánh của Giải pháp 1 phải là cùng môn, không phải toàn trường.
- **Lưu ý khi viết báo cáo:**
  - Chỉ 36 trong 93 môn có mặt ở cả hai giai đoạn.
  - Mốc đổi không rõ ràng: cơ cấu 10/40/50 xuất hiện cả trước mốc (621 lượt), còn 10/20/70 vẫn còn sau mốc (627 lượt).
    - → Nên chia giai đoạn theo **cơ cấu trọng số suy ra của từng lớp**, không theo ngày.
  - Đỉnh điểm số khoảng 2020-21 HK3 đến 2021-22 HK1 trùng thời kỳ học trực tuyến vì COVID.
    - Đây chỉ là **giả thuyết**, vì dữ liệu không ghi hình thức thi.

### C. Loại lớp (mục 3.3)
- **Lớp EP:** HP cao hơn lớp thường 0,34 điểm.
- **Đồ án / thực tập / khóa luận:**
  - HP cao hơn lớp thường 0,94 điểm.
  - Tỷ lệ A 74%.
  - 11,2% lượt có HP = 0.
- → **Phải tách riêng** nhóm đồ án / thực tập / khóa luận, không so chung với lớp thường.

## 4. Năng lực nền (mục 4): rủi ro lớn nhất
- **Mỗi SV học rất ít môn trong dữ liệu:**
  - Trung vị chỉ **3 môn**/SV; 25% SV chỉ có 1 môn.
  - Lý do: dữ liệu chỉ gồm các môn do một khoa phụ trách.
- **Ít SV đủ môn khác để tính năng lực nền:**

  | Điều kiện | % SV đạt | % lượt điểm |
  |---|---|---|
  | Có ≥ 3 môn khác | 38,8% | 84,1% |
  | Có ≥ 5 môn khác | 28,9% | 77,8% |

- **Theo khóa:** K59 và K60 có nhiều môn nhất; K66 và K67 có ít nhất.
- **Hệ quả:** tiêu chí "lệch năng lực nền" của Giải pháp 1 và chỉ số TCI của Giải pháp 3 chỉ tin cậy được với một phần SV. Cần:
  - đặt số môn tối thiểu;
  - kéo điểm của SV ít môn về gần trung bình (shrinkage);
  - kèm mức độ tin cậy, và ghi "chưa đủ dữ liệu" cho SV có quá ít môn.

## 5. Hệ quả cho thiết kế

| Giải pháp | Điều chỉnh rút ra từ EDA |
|---|---|
| GP1 – Phát hiện lớp bất thường | <ul><li>Dùng ngưỡng tương đối (so với lớp khác cùng môn và cùng giai đoạn) thay cho ngưỡng cố định 60%.</li><li>Thêm mốc so sánh thứ hai (cùng Nhóm môn hoặc Khoa) để phát hiện môn dễ ở mọi lớp.</li><li>Anomaly Score kết hợp tỷ lệ A, z của chênh lệch KTTX − Thi (kèm ngưỡng chênh lệch tối thiểu) và σ nhỏ.</li><li>Tách riêng đồ án và EP.</li><li>Lớp có KTTX trung bình bằng Thi trung bình: kiểm tra ở từng dòng trước khi gắn `SUSPICIOUS_DISTRIBUTION`.</li></ul> |
| GP2 – Hiệu chỉnh điểm | <ul><li>Hiệu chỉnh theo cùng môn và cùng cơ cấu trọng số, vì xu hướng toàn trường chủ yếu do khác môn.</li><li>Loại HK3 2025-26 và HK3 2022-23 khỏi phần ước lượng.</li></ul> |
| GP3 – TCI | <ul><li>Đặt số môn tối thiểu và dùng shrinkage.</li><li>Kèm mức tin cậy cho từng SV, và nhãn "chưa đủ dữ liệu" cho SV có quá ít môn.</li><li>Nêu rõ giới hạn này trong báo cáo giải thích.</li></ul> |

## 6. Phân tích đề xuất làm tiếp (chưa làm, chờ duyệt)
1. **Lớp có KTTX bằng Thi:** đếm tỷ lệ dòng có KTTX = Thi trong mỗi lớp, và xem có liên quan tới cơ cấu 10/0/90 không.
2. **Lượt có HP nhưng không có Thi:** tìm hiểu khoảng 1.800 lượt này, xem chúng thuộc loại lớp nào, cơ cấu trọng số nào, năm nào.
3. **So sánh giai đoạn:** so theo cơ cấu trọng số suy ra của từng lớp thay vì theo ngày.
4. **Quy ước Khóa SV:** mở rộng thành K56–K67 trong `config.py`, sau khi xác nhận K56 và K57 là hợp lệ.
