# HỆ THỐNG GIÁM SÁT GIAO THÔNG THÔNG MINH (ITS)

Hệ thống giám sát giao thông thông minh (Intelligent Transportation System - ITS) được xây dựng trên nền tảng thị giác máy tính (Computer Vision) và học sâu (Deep Learning) nhằm thực hiện tự động hóa quy trình: nhận diện phương tiện, theo dõi quỹ đạo di chuyển, đếm lưu lượng phân loại, đo lường vận tốc thực tế và phát hiện các hành vi vi phạm quá tốc độ trong khu vực đô thị.

Dự án được tối ưu hóa và chuẩn hóa toàn diện từ mã nguồn gốc chuyên đề đồ án, đáp ứng các tiêu chuẩn về Clean Code, kiến trúc mở rộng, toàn vẹn dữ liệu và sẵn sàng vận hành thực tế.

---

## 1. MỤC TIÊU VÀ PHẠM VI HỆ THỐNG

- **Mục tiêu:** Cung cấp giải pháp giám sát giao thông tự động, giúp cơ quan quản lý giao thông hoặc các đơn vị nghiên cứu nắm bắt lưu lượng xe thời gian thực, phát hiện phương tiện chạy quá tốc độ quy định và xuất dữ liệu phục vụ phân tích.
- **Phạm vi ứng dụng:** Giao lộ đô thị, nút giao thông trọng điểm, tuyến đường nội đô có đặt camera quan sát góc cao (high-angle / top-down perspective).
- **Đối tượng giám sát:** Bốn nhóm phương tiện chính gồm xe máy, ô tô con, xe tải và xe buýt.

---

## 2. CÁC CHỨC NĂNG CHÍNH

1. **Nhận diện và theo dõi phương tiện (Object Detection & Multi-Object Tracking):**
   - Sử dụng mô hình YOLO11 kết hợp thuật toán BoT-SORT (tracker="botsort.yaml").
   - Duy trì ID phương tiện liên tục, hạn chế tối đa tình trạng nhảy ID hoặc bỏ sót xe máy có kích thước nhỏ.

2. **Đếm lưu lượng theo phân loại (Vehicle Counting & Classification):**
   - Thiết lập Vạch 1 (Counting Line) ở phía trước để ghi nhận phương tiện ngay khi tiến vào vùng quan sát.
   - Phân loại chính xác thành 4 nhóm: Xe máy, Ô tô, Xe tải, Xe buýt.

3. **Đo vận tốc vật lý thực tế (Two-Line Speed Trap Measurement):**
   - Sử dụng Vùng đo hai vạch mốc với khoảng cách hiệu chuẩn vật lý chuẩn (mặc định 8.0 mét).
   - Tính toán vận tốc vật lý dựa trên thời gian dịch chuyển thực tế (delta_t) giữa hai vạch.
   - Hỗ trợ module biến đổi phối cảnh Homography để quy đổi tọa độ pixel sang tọa độ mặt đất tính bằng mét.

4. **Phát hiện vi phạm và tự động lưu bằng chứng (Violation Detection & Evidence Capture):**
   - So sánh vận tốc chốt với ngưỡng quy định (mặc định 50.0 km/h theo quy chuẩn đô thị).
   - Tự động chụp ảnh phương tiện vi phạm, đóng khung viền cảnh báo lỗi và lưu trữ vào thư mục hệ thống.

5. **Lưu trữ dữ liệu SQLite và bảo đảm tính nhất quán (Database & Idempotency):**
   - Lưu nhật ký phương tiện vào cơ sở dữ liệu `its_database.db` với chế độ ghi WAL (Write-Ahead Logging).
   - Cơ chế session_id và khóa duy nhất ngăn chặn trùng lặp dữ liệu khi phương tiện đi qua nhiều vạch hoặc khi video phát lặp lại.

6. **Web Dashboard điều hành trực quan (Web Monitoring Interface):**
   - Giao diện trực quan phát luồng video MJPEG thời gian thực.
   - Hiển thị các thẻ chỉ số KPI, biểu đồ phân bổ phương tiện Chart.js và bằng chứng vi phạm.
   - Cho phép điều chỉnh vị trí hai vạch mốc và ngưỡng tốc độ trực tiếp trên nền web.
   - Xuất báo cáo dữ liệu giao thông định dạng CSV tiêu chuẩn.

---

## 3. KIẾN TRÚC TỔNG QUAN

Hệ thống được tổ chức thành ba tầng chính:

```
[ Tầng Thu Thập & Thị Giác Máy Tính ]
  Camera / Video File MP4 -> YOLO11 + BoT-SORT Tracking -> Vùng đo 2 vạch mốc (Speed Trap)
                                     |
                                     v
[ Tầng Xử Lý Nghiệp Vụ & Lưu Trữ ]
  ITSTracker -> Kiểm tra qua vạch -> Tính tốc độ -> Bắt vi phạm -> Chụp ảnh bằng chứng
                                     |
                                     v
                        SQLite Database (its_database.db)
                                     |
                                     v
[ Tầng Cung Cấp Dịch Vụ & Giao Diện ]
  FastAPI Server (REST API + MJPEG Streaming) -> Web Dashboard (TailwindCSS + Chart.js)
```

---

## 4. CÔNG NGHỆ SỬ DỤNG

- **Ngôn ngữ lập trình:** Python 3.10 - 3.14
- **Thị giác máy tính & Deep Learning:** OpenCV (opencv-python), Ultralytics YOLO11, PyTorch
- **Thuật toán Tracking:** BoT-SORT (kết hợp Kalman Filter, ReID và Camera Motion Compensation)
- **Cơ sở dữ liệu:** SQLite3 (tích hợp chế độ WAL, chỉ mục tra cứu và Unique Constraints)
- **Web Backend:** FastAPI, Uvicorn, Pydantic v2
- **Web Frontend:** HTML5, TailwindCSS CDN, Font Awesome 6, Chart.js
- **Kiểm thử tự động:** Pytest, HTTPX

---

## 5. YÊU CẦU MÔI TRƯỜNG

- Hệ điều hành: Windows 10/11, Linux Ubuntu 20.04+, macOS.
- Python: Phiên bản 3.10 trở lên.
- Bộ nhớ RAM: Tối thiểu 4 GB (khuyến nghị 8 GB trở lên).
- CPU/GPU: Có thể chạy tốt trên CPU đa nhân; hỗ trợ tăng tốc CUDA nếu có card đồ họa NVIDIA.

Các thư viện cần thiết được cài đặt qua lệnh:
```bash
pip install ultralytics opencv-python torch torchvision fastapi uvicorn pydantic pytest httpx
```

---

## 6. CẤU TRÚC THƯ MỤC DỰ ÁN

```
D:\ITS-GiamSatXe\
|-- its_core/                       # Gói xử lý nghiệp vụ lõi
|   |-- __init__.py
|   |-- config.py                   # Cấu hình tham số, ngưỡng vận tốc và danh mục xe
|   |-- tracker.py                  # Module nhận diện, theo dõi BoT-SORT và tính vận tốc
|   |-- pipeline.py                 # Điều phối luồng đọc video và xử lý khung hình
|   |-- database.py                 # Quản lý cơ sở dữ liệu SQLite và tính toán KPI
|   |-- homography.py               # Biến đổi phối cảnh mặt phẳng sang hệ tọa độ mét
|-- its_dashboard/                  # Ứng dụng Web Dashboard giám sát
|   |-- server.py                   # Web server FastAPI, REST API và luồng MJPEG
|   |-- templates/
|       |-- index.html              # Giao diện điều hành TailwindCSS + Chart.js
|-- tests/                          # Bộ kiểm thử tự động (Automated Test Suite)
|   |-- __init__.py
|   |-- test_speed_calculation.py   # Kiểm thử phép tính vận tốc và điều kiện vật lý
|   |-- test_line_crossing.py       # Kiểm thử logic qua vạch và chuyển trạng thái
|   |-- test_database.py            # Kiểm thử tính toàn vẹn và truy vấn CSDL
|   |-- test_api.py                 # Kiểm thử các API endpoint của Dashboard
|-- snapshots/                      # Thư mục lưu trữ ảnh bằng chứng vi phạm
|-- vehicles_counting-master/       # Dữ liệu gốc (video NgaTuGa.mp4, weights yolo11n.pt)
|-- its_database.db                 # Tệp tin cơ sở dữ liệu SQLite
|-- Output_upgraded.mp4             # Video kết quả sau khi xử lý hoàn chỉnh
|-- run_dashboard.py                # Điểm khởi chạy giao diện Web Dashboard
|-- run_pipeline.py                 # Điểm khởi chạy chương trình CLI xử lý video
|-- README.md                       # Tài liệu hướng dẫn tổng quan và vận hành
|-- MO_TA_HE_THONG.md               # Tài liệu đặc tả kiến trúc và luồng nghiệp vụ
|-- HUONG_DAN_SU_DUNG.md            # Hướng dẫn vận hành chi tiết cho người dùng
|-- KIEM_THU.md                     # Kế hoạch và kết quả kiểm thử hệ thống
```

---

## 7. HƯỚNG DẪN CÀI ĐẶT VÀ VẬN HÀNH

### 7.1. Chạy giao diện Web Dashboard (Khuyên dùng)

Đây là phương thức vận hành chính, cung cấp đầy đủ màn hình video trực tiếp, bảng chỉ số KPI và chức năng điều chỉnh:

```bash
python run_dashboard.py
```

Sau khi máy chủ khởi động, mở trình duyệt web (Chrome, Edge, Firefox) và truy cập địa chỉ:
```
http://127.0.0.1:8000
```

Tham số tùy chọn:
```bash
python run_dashboard.py --host 0.0.0.0 --port 8000
```

### 7.2. Chạy xử lý video qua dòng lệnh (CLI Pipeline)

Phương thức này phù hợp cho việc xử lý hàng loạt tệp video hoặc chạy trên máy chủ không có giao diện đồ họa:

- Chạy xem trực tiếp màn hình OpenCV:
  ```bash
  python run_pipeline.py
  ```

- Chạy chế độ ẩn (Headless), không mở cửa sổ màn hình:
  ```bash
  python run_pipeline.py --no-display
  ```

- Xử lý số lượng khung hình giới hạn (ví dụ 150 khung hình):
  ```bash
  python run_pipeline.py --max-frames 150
  ```

- Chỉ định video nguồn và tệp kết quả khác:
  ```bash
  python run_pipeline.py --video duong_dan_video.mp4 --output video_dau_ra.mp4 --speed-limit 50
  ```

---

## 8. DỮ LIỆU ĐẦU RA VÀ LƯU TRỮ

| Thành phần | Vị trí lưu trữ | Mô tả |
| :--- | :--- | :--- |
| Video kết quả | `Output_upgraded.mp4` | Video đã được chú thích bounding box, quỹ đạo di chuyển, vùng đo và bảng HUD |
| Cơ sở dữ liệu | `its_database.db` | CSDL SQLite lưu trữ nhật ký phương tiện và bảng thống kê |
| Ảnh bằng chứng | `snapshots/` | Tệp ảnh JPG chụp phương tiện vi phạm tốc độ kèm theo thông tin lỗi |
| Báo cáo xuất bản | `its_traffic_report.csv` | File báo cáo CSV được xuất qua nút bấm trên Dashboard |

---

## 9. XỬ LÝ CÁC VẤN ĐỀ THƯỜNG GẶP

1. **Lỗi không tìm thấy mô hình (`FileNotFoundError: yolo11n.pt`):**
   - Kiểm tra tệp `vehicles_counting-master/yolo11n.pt` có tồn tại hay không. Nếu chưa có, hệ thống sẽ tự động tải từ Ultralytics hoặc bạn cần đặt file vào đúng thư mục.

2. **Lỗi font tiếng Việt trên Windows Console:**
   - Hệ thống đã tích hợp cơ chế tự động thiết lập UTF-8 qua `sys.stdout.reconfigure(encoding='utf-8')`. Nếu vẫn bị lỗi, hãy chạy lệnh `chcp 65001` trên PowerShell/CMD trước khi khởi chạy.

3. **Cổng 8000 đã bị sử dụng bởi ứng dụng khác:**
   - Khởi động với cổng khác: `python run_dashboard.py --port 8080`.

4. **Cơ sở dữ liệu bị khóa (`sqlite3.OperationalError: database is locked`):**
   - Hệ thống đã bật chế độ WAL (Write-Ahead Logging) và thời gian timeout 15 giây để ngăn chặn khóa dữ liệu. Nếu vẫn xảy ra, kiểm tra xem có chương trình DB Browser nào đang mở file database mà chưa commit không.

---

## 10. GIỚI HẠN HIỆN TẠI CỦA HỆ THỐNG

- **Góc quay camera:** Phép đo vận tốc hiện tại phù hợp nhất với camera có góc quay cố định nhìn xuôi hoặc chéo từ trên cao xuống. Camera di động hoặc lia góc quay liên tục sẽ làm biến đổi khoảng cách tham chiếu.
- **Che khuất cục bộ:** Khi các phương tiện có kích thước lớn như xe tải hoặc xe buýt che hoàn toàn xe máy trong suốt đoạn giữa hai vạch, hệ thống có thể bị ngắt quãng quãng đường theo dõi.
- **Điều kiện ánh sáng:** Video ban đêm hoặc thời tiết mưa lớn có thể làm giảm độ tin cậy của mô hình nhận diện COCO mặc định.

---

## 11. LIÊN KẾT TÀI LIỆU CHI TIẾT

- [MO_TA_HE_THONG.md](file:///d:/ITS-GiamSatXe/MO_TA_HE_THONG.md): Tài liệu đặc tả kiến trúc, luồng nghiệp vụ và đặc tả API.
- [HUONG_DAN_SU_DUNG.md](file:///d:/ITS-GiamSatXe/HUONG_DAN_SU_DUNG.md): Hướng dẫn vận hành chi tiết từng bước cho người dùng.
- [KIEM_THU.md](file:///d:/ITS-GiamSatXe/KIEM_THU.md): Kế hoạch kiểm thử và kết quả xác minh các ca kiểm thử tự động.
