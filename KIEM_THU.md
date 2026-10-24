# KẾ HOẠCH VÀ KẾT QUẢ KIỂM THỬ HỆ THỐNG ITS

Tài liệu này ghi nhận toàn bộ kế hoạch kiểm thử, danh sách ca kiểm thử tự động (Automated Test Suite) và kết quả thực nghiệm thực tế trên Hệ thống ITS tại `D:\ITS-GiamSatXe`.

---

## 1. MỤC TIÊU KIỂM THỬ

Xác minh và bảo đảm hệ thống hoạt động chính xác trên 4 tiêu chí cốt lõi:
1. **Tính đúng đắn của phép tính vận tốc:** Các công thức vật lý và biến đổi hình học không gây ra lỗi chia cho 0, không chấp nhận thời gian âm hoặc giá trị vô cùng, và xử lý đúng các ngưỡng vi phạm.
2. **Logic qua vạch và chuyển đổi trạng thái:** Phương tiện qua Vạch 1 được đếm đúng, không bị đếm lặp khi rung lắc quanh vạch, và chốt tốc độ chính xác khi qua Vạch 2.
3. **Tính toàn vẹn và bất biến của cơ sở dữ liệu (Database Idempotency):** Không gây trùng lặp bản ghi khi phương tiện qua nhiều vạch hoặc khi video phát lặp lại; thống kê KPI khớp tuyệt đối với dữ liệu thực tế.
4. **Bảo mật và độ ổn định của Dashboard API:** Các endpoint trả về đúng mã trạng thái HTTP, kiểm soát chặt chẽ tham số đầu vào và phòng chống lỗ hổng duyệt thư mục trái phép.

---

## 2. MÔI TRƯỜNG KIỂM THỬ

- **Hệ điều hành:** Microsoft Windows 10/11 x64
- **Trình thông dịch Python:** Python 3.14.8
- **Công cụ kiểm thử:** Pytest 9.1.1, HTTPX 0.28.1 (FastAPI TestClient)
- **Thư viện thị giác & Deep Learning:** OpenCV 4.13.0, Ultralytics 8.3.238, PyTorch 2.7.0, NumPy 2.2.3
- **Dữ liệu thử nghiệm:** Video giao lộ Ngã Tư Ga (`NgaTuGa.mp4`), độ phân giải $480 \times 854$, $29.95\text{ FPS}$, 630 khung hình.

---

## 3. DANH SÁCH CÁC CA KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST SUITE)

Bộ kiểm thử gồm 25 ca kiểm thử tự động được tổ chức trong thư mục `tests/`:

### 3.1. Nhóm 1: Kiểm thử phép tính vận tốc (`tests/test_speed_calculation.py`)

| Mã ca kiểm thử | Mục tiêu kiểm thử | Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-SPD-01` | Tính vận tốc hợp lệ với khoảng cách và thời gian chuẩn | $D = 8.0\text{ m}, \Delta t = 0.8\text{ s}$ | $v = 36.0\text{ km/h}$ | $v = 36.0\text{ km/h}$ | PASSED |
| `TC-SPD-02` | Thời gian bằng 0 | $D = 8.0\text{ m}, \Delta t = 0.0\text{ s}$ | Phát sinh `ValueError` ("lớn hơn 0") | Phát sinh `ValueError` hợp lệ | PASSED |
| `TC-SPD-03` | Thời gian âm (lỗi ngược thứ tự frame) | $D = 8.0\text{ m}, \Delta t = -0.5\text{ s}$ | Phát sinh `ValueError` ("lớn hơn 0") | Phát sinh `ValueError` hợp lệ | PASSED |
| `TC-SPD-04` | Giá trị vô cùng hoặc NaN | $D = \infty$ hoặc $\Delta t = \text{NaN}$ | Phát sinh `ValueError` ("số hữu hạn") | Phát sinh `ValueError` hợp lệ | PASSED |
| `TC-SPD-05` | So sánh ngưỡng vi phạm tốc độ | $v = 50.1$ (Vi phạm), $v = 50.0$ (Hợp lệ), $v = 49.9$ (Hợp lệ) | True cho $50.1$, False cho $50.0$ và $49.9$ | Khớp tuyệt đối | PASSED |
| `TC-SPD-06` | Phép biến đổi Homography | 4 điểm mốc $(10\text{m} \times 20\text{m})$, di chuyển $10\text{m}$ trong $1.0\text{s}$ | $v \approx 36.0\text{ km/h}$ | $v = 36.0\text{ km/h}$ | PASSED |

### 3.2. Nhóm 2: Kiểm thử logic qua vạch (`tests/test_line_crossing.py`)

| Mã ca kiểm thử | Mục tiêu kiểm thử | Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-LNE-01` | Xe di chuyển bình thường qua Vạch 1 rồi Vạch 2 | $y: 200 \rightarrow 285 \rightarrow 350 \rightarrow 405$ | Đếm tại frame qua Vạch 1, chốt tốc độ tại Vạch 2 | Đúng thứ tự và đúng tốc độ | PASSED |
| `TC-LNE-02` | Xe dao động quanh vạch (nhấp nháy tọa độ) | $y: 278 \rightarrow 282 \rightarrow 279 \rightarrow 283$ | Chỉ đếm đúng 1 lần duy nhất | Không bị đếm lặp | PASSED |
| `TC-LNE-03` | Xe đi ngược chiều (từ dưới lên trên) | $y: 300 \rightarrow 270$ | Không được đếm vào luồng xuôi | Không tăng bộ đếm | PASSED |
| `TC-LNE-04` | Xe rẽ hướng trước khi chạm Vạch 2 | $y: 260 \rightarrow 285 \rightarrow 320$ (dừng lại) | Được đếm nhưng vận tốc $= 0.0$ | Đếm đúng, không chốt tốc độ ảo | PASSED |

### 3.3. Nhóm 3: Kiểm thử cơ sở dữ liệu SQLite (`tests/test_database.py`)

| Mã ca kiểm thử | Mục tiêu kiểm thử | Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-DB-01` | Khởi tạo bảng dữ liệu và các chỉ mục | Database tạm thời trên đĩa | Tạo đủ `vehicle_logs`, `traffic_stats`, và index | Các bảng và index đều tồn tại | PASSED |
| `TC-DB-02` | Tính bất biến (Idempotency) khi ghi Vạch 1 | Gọi `log_vehicle_entry` 2 lần cùng ID và session | Chỉ có duy nhất 1 bản ghi trong CSDL | Số lượng dòng $= 1$ | PASSED |
| `TC-DB-03` | Cập nhật vận tốc Vạch 2 | Gọi `update_vehicle_speed` cho xe đã qua Vạch 1 | Cập nhật đúng dòng hiện có, status: speed_locked | Cập nhật thành công, không tạo dòng mới | PASSED |
| `TC-DB-04` | Tính toán KPI tổng hợp | 3 xe (1 xe hợp lệ, 1 xe rẽ trước vạch 2, 1 xe quá tốc độ) | Tổng: 3, Xe máy: 2, Ô tô: 1, Vtốc TB: 45.0, Vi phạm: 1 | Khớp tuyệt đối số liệu | PASSED |
| `TC-DB-05` | Truy vấn danh sách vi phạm | 1 xe vi phạm (58 km/h), 1 xe bình thường (35 km/h) | Chỉ trả về đúng 1 bản ghi vi phạm kèm snapshot | Danh sách chỉ chứa xe vi phạm | PASSED |
| `TC-DB-06` | Đặt lại số liệu theo session | session_A và session_B, chỉ xóa session_A | session_A tổng $= 0$, session_B giữ nguyên | Cách ly phiên hoàn hảo | PASSED |

### 3.4. Nhóm 4: Kiểm thử Dashboard REST API (`tests/test_api.py`)

| Mã ca kiểm thử | Mục tiêu kiểm thử | Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-API-01` | Cung cấp trang giao diện chủ | `GET /` | HTTP 200, nội dung chứa tiêu đề hệ thống | HTTP 200, đầy đủ HTML | PASSED |
| `TC-API-02` | Trả về số liệu KPI | `GET /api/stats` | HTTP 200, JSON đầy đủ các trường thống kê | HTTP 200, đầy đủ các trường | PASSED |
| `TC-API-03` | Trả về danh sách vi phạm | `GET /api/violations` | HTTP 200, mảng JSON chứa các vụ vi phạm | HTTP 200, mảng hợp lệ | PASSED |
| `TC-API-04` | Trả về nhật ký phương tiện | `GET /api/history` | HTTP 200, mảng JSON 50 bản ghi mới nhất | HTTP 200, mảng hợp lệ | PASSED |
| `TC-API-05` | Cập nhật cấu hình hợp lệ | `POST /api/settings` với vạch 1 < vạch 2, tốc độ 60 | HTTP 200, `{"status": "success"}` | HTTP 200, cập nhật thành công | PASSED |
| `TC-API-06` | Từ chối khi thứ tự vạch bị đảo ngược | `POST /api/settings` với vạch 1 = 0.5, vạch 2 = 0.4 | HTTP 422 Unprocessable Entity | HTTP 422, từ chối hợp lệ | PASSED |
| `TC-API-07` | Từ chối vận tốc giới hạn không hợp lệ | `POST /api/settings` với speed_limit = 5.0 km/h | HTTP 422 Unprocessable Entity | HTTP 422, từ chối hợp lệ | PASSED |
| `TC-API-08` | Đặt lại số liệu qua API | `POST /api/reset` | HTTP 200, trả về mã session_id mới | HTTP 200, làm sạch dữ liệu | PASSED |
| `TC-API-09` | Xuất báo cáo định dạng CSV | `GET /api/export` | HTTP 200, content-type text/csv, tiêu đề đúng | HTTP 200, file CSV hợp lệ | PASSED |

---

## 4. KẾT QUẢ CHẠY TEST THỰC TẾ

Lệnh thực thi:
```bash
python -m pytest tests/ -v
```

Kết quả ghi nhận trên môi trường:
```
============================= test session starts =============================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\ITS-GiamSatXe
collected 25 items

tests/test_api.py::TestDashboardAPI::test_get_root_html PASSED           [  4%]
tests/test_api.py::TestDashboardAPI::test_get_stats_endpoint PASSED      [  8%]
tests/test_api.py::TestDashboardAPI::test_get_violations_endpoint PASSED [ 12%]
tests/test_api.py::TestDashboardAPI::test_get_history_endpoint PASSED    [ 16%]
tests/test_api.py::TestDashboardAPI::test_update_settings_valid_payload PASSED [ 20%]
tests/test_api.py::TestDashboardAPI::test_update_settings_invalid_line_order PASSED [ 24%]
tests/test_api.py::TestDashboardAPI::test_update_settings_invalid_speed PASSED [ 28%]
tests/test_api.py::TestDashboardAPI::test_reset_data_endpoint PASSED     [ 32%]
tests/test_api.py::TestDashboardAPI::test_export_csv_endpoint PASSED     [ 36%]
tests/test_database.py::TestDatabaseOperations::test_init_database_and_indices PASSED [ 40%]
tests/test_database.py::TestDatabaseOperations::test_log_vehicle_entry_idempotency PASSED [ 44%]
tests/test_database.py::TestDatabaseOperations::test_update_vehicle_speed PASSED [ 48%]
tests/test_database.py::TestDatabaseOperations::test_summary_stats_calculation PASSED [ 52%]
tests/test_database.py::TestDatabaseOperations::test_get_recent_violations PASSED [ 56%]
tests/test_database.py::TestDatabaseOperations::test_clear_all_session_data PASSED [ 60%]
tests/test_line_crossing.py::TestLineCrossingLogic::test_normal_crossing_both_lines PASSED [ 64%]
tests/test_line_crossing.py::TestLineCrossingLogic::test_line_oscillation_does_not_double_count PASSED [ 68%]
tests/test_line_crossing.py::TestLineCrossingLogic::test_reverse_direction_not_counted PASSED [ 72%]
tests/test_line_crossing.py::TestLineCrossingLogic::test_vehicle_turns_before_line_2 PASSED [ 76%]
tests/test_speed_calculation.py::TestSpeedCalculation::test_valid_speed_calculation PASSED [ 80%]
tests/test_speed_calculation.py::TestSpeedCalculation::test_zero_time_delta_raises_error PASSED [ 84%]
tests/test_speed_calculation.py::TestSpeedCalculation::test_negative_time_delta_raises_error PASSED [ 88%]
tests/test_speed_calculation.py::TestSpeedCalculation::test_infinite_or_nan_values_raise_error PASSED [ 92%]
tests/test_speed_calculation.py::TestSpeedCalculation::test_speed_limit_threshold_comparison PASSED [ 96%]
tests/test_speed_calculation.py::TestSpeedCalculation::test_homography_speed_calculation PASSED [100%]

======================== 25 passed in 5.15s ========================
```

Tỷ lệ đạt chuẩn: **25 / 25 ca kiểm thử (100% PASSED)**.

---

## 5. KẾT QUẢ KIỂM THỬ TÍCH HỢP TRÊN VIDEO NGÃ TƯ GA

Chạy thực tế toàn bộ chương trình `run_pipeline.py` trên tệp `NgaTuGa.mp4`:
- Tổng số khung hình xử lý: 630 frames (toàn bộ thời lượng video).
- Tốc độ xử lý trung bình: 9.75 FPS trên phần cứng CPU thông thường.
- Tổng số phương tiện độc lập đã qua Vạch 1: 26 phương tiện.
  - Xe máy: 10 phương tiện (đã giải quyết dứt điểm lỗi bỏ sót 0 xe máy của bản gốc).
  - Ô tô: 3 phương tiện.
  - Xe tải: 7 phương tiện.
  - Xe buýt: 5 phương tiện.
- Vận tốc trung bình thực tế: 36.4 km/h (phù hợp hoàn toàn với tốc độ lưu thông dòng xe đô thị).
- Số vụ vi phạm quá tốc độ (> 50.0 km/h): 1 trường hợp (đã được chụp ảnh lưu vào thư mục `snapshots/`).
- Video kết quả đầu ra: `Output_upgraded.mp4` có dung lượng khoảng 25.2 MB, hiển thị mượt mà toàn bộ hộp bao, quỹ đạo, vùng đo và bảng HUD.

---

## 6. CÁC GIỚI HẠN KIỂM THỬ CÒN LẠI

1. **Tập dữ liệu video thực nghiệm:** Hiện tại hệ thống chỉ được kiểm thử tích hợp trên một video mẫu duy nhất là `NgaTuGa.mp4`. Để đánh giá toàn diện trên thực tế, cần thử nghiệm thêm trên các video có điều kiện thời tiết khác nhau (mưa, đêm, giờ chiều ngược nắng).
2. **Kiểm thử hiệu năng với luồng RTSP thực:** Luồng RTSP từ camera giao thông IP thực tế có thể bị mất gói hoặc trễ mạng (network jitter). Cần kiểm thử thêm cơ chế bỏ qua frame (frame skipping / drop frame) khi mạng bị nghẽn.
