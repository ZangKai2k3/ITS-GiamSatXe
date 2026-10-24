# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG GIÁM SÁT GIAO THÔNG ITS

Tài liệu này hướng dẫn chi tiết từng bước dành cho cán bộ điều hành, quản trị viên hoặc người dùng không chuyên về lập trình để khởi động, vận hành, theo dõi và khai thác dữ liệu từ Hệ thống ITS.

---

## 1. CHUẨN BỊ MÔI TRƯỜNG

Trước khi khởi động ứng dụng, hãy đảm bảo máy tính đã được cài đặt:
- Hệ điều hành: Windows 10/11 hoặc Linux / macOS.
- Trình duyệt web hiện đại: Google Chrome, Microsoft Edge hoặc Mozilla Firefox.
- Python phiên bản 3.10 trở lên đã được cài đặt và thêm vào biến môi trường PATH.

Kiểm tra bằng cách mở PowerShell hoặc Command Prompt:
```bash
python --version
```

---

## 2. KHỞI ĐỘNG HỆ THỐNG

### 2.1. Khởi động Web Dashboard (Giao diện chính)

1. **Vị trí thao tác:** Cửa sổ dòng lệnh (PowerShell hoặc Terminal) tại thư mục gốc của dự án: `D:\ITS-GiamSatXe`.
2. **Hành động:** Nhập dòng lệnh sau và nhấn phím Enter:
   ```bash
   python run_dashboard.py
   ```
3. **Kết quả mong đợi:** Màn hình console hiển thị thông báo khởi động:
   ```
   =================================================================
      KHỞI ĐỘNG HỆ THỐNG ITS WEB DASHBOARD
      Địa chỉ truy cập: http://127.0.0.1:8000
      Bấm Ctrl+C để dừng máy chủ
   =================================================================
   ```
4. **Cách xử lý nếu gặp lỗi:** Nếu thông báo lỗi "Address already in use", có nghĩa cổng 8000 đã bị ứng dụng khác chiếm dụng. Khởi động lại với cổng 8080:
   ```bash
   python run_dashboard.py --port 8080
   ```

### 2.2. Mở giao diện Web

1. **Hành động:** Mở trình duyệt web và nhập địa chỉ:
   ```
   http://127.0.0.1:8000
   ```
2. **Kết quả mong đợi:** Giao diện trung tâm điều hành ITS màu tối (Dark Mode) xuất hiện với đầy đủ màn hình camera, các thẻ KPI thống kê và biểu đồ phân bổ phương tiện.

---

## 3. QUAN SÁT VIDEO VÀ ĐỌC CÁC CHỈ SỐ

### 3.1. Màn hình video thời gian thực
- **Vị trí:** Ở bên trái giao diện, khung "Video Giám Sát Real-Time".
- **Ý nghĩa các ký hiệu trên màn hình:**
  - **Vạch 1 màu vàng:** Vạch đếm phương tiện và bắt đầu đo tốc độ. Phương tiện đi xuống chạm vạch này sẽ được hệ thống ghi nhận ngay lập tức.
  - **Vạch 2 màu xanh lơ:** Vạch chốt tốc độ và phát hiện vi phạm. Phương tiện chạy qua đây sẽ được hệ thống tính toán vận tốc thực tế dựa trên quãng đường 8.0 mét.
  - **Khung hộp bao (Bounding Box):**
    - Khung xanh lá cây: Phương tiện xe máy hợp lệ.
    - Khung cam / tím: Phương tiện ô tô / xe tải hợp lệ.
    - Khung màu đỏ: Phương tiện chạy quá tốc độ quy định (> 50 km/h).
  - **Thẻ thông tin trên xe:** Hiển thị ID phương tiện, loại xe và tốc độ (ví dụ: `#24 Xe máy | 32.5 km/h [Chốt]`).
  - **Bảng HUD góc trái:** Hiển thị tổng số xe đã qua vạch và chi tiết từng loại xe.

### 3.2. Bảng thẻ chỉ số KPI
Nằm ở hàng trên cùng của giao diện, gồm 6 thẻ chỉ số được đồng bộ từ cơ sở dữ liệu:
1. **Tổng Phương Tiện:** Tổng số phương tiện độc lập đã được ghi nhận qua Vạch 1.
2. **Xe máy:** Số lượng và tỷ lệ phần trăm lưu lượng xe 2 bánh.
3. **Ô tô:** Số lượng và tỷ lệ phần trăm xe ô tô con.
4. **Xe tải / Buýt:** Tổng lưu lượng phương tiện vận tải hàng hóa và hành khách.
5. **Tốc độ TB:** Vận tốc trung bình thực tế tính bằng km/h của tất cả các phương tiện đã qua Vạch 2.
6. **Quá tốc độ:** Tổng số lượng trường hợp vi phạm chạy quá tốc độ cho phép.

---

## 4. ĐIỀU CHỈNH VỊ TRÍ VẠCH ĐO VÀ NGƯỠNG TỐC ĐỘ

Khi camera thay đổi góc quan sát hoặc cần tinh chỉnh phạm vi đo tốc độ:

1. **Vị trí thao tác:** Khung điều khiển ngay bên dưới màn hình video.
2. **Các tham số điều chỉnh:**
   - **Vạch 1 [Trước] (Đếm xe):** Kéo thanh trượt để điều chỉnh độ cao Vạch 1 (khoảng hợp lệ: 18% - 45% chiều cao ảnh).
   - **Vạch 2 [Sau] (Chốt tốc độ):** Kéo thanh trượt để điều chỉnh độ cao Vạch 2 (khoảng hợp lệ: 35% - 65% chiều cao ảnh).
   - **Giới hạn tốc độ:** Nhập giá trị vận tốc tối đa cho phép tại đoạn đường (ví dụ: 40 km/h, 50 km/h hoặc 60 km/h).
3. **Hành động:** Bấm vào nút **Cập Nhật Vùng Đo** (màu xanh cyan).
4. **Kết quả mong đợi:** Hộp thoại thông báo "Đã cập nhật Vạch Đếm Xe & Vạch Tính Tốc Độ thành công!" xuất hiện, và hai đường kẻ trên màn hình video sẽ tự động dịch chuyển đến vị trí mới.
5. **Lưu ý quan trọng:** Vạch 1 bắt buộc phải nằm ở phía trước (độ cao nhỏ hơn) Vạch 2 ít nhất 5%. Nếu kéo Vạch 1 thấp hơn hoặc bằng Vạch 2, hệ thống sẽ từ chối cập nhật để tránh sai lệch phép tính vận tốc.

---

## 5. TRA CỨU VÀ XEM ẢNH BẰNG CHỨNG VI PHẠM

### 5.1. Xem danh sách vi phạm
- **Vị trí:** Khung "Bằng Chứng Vi Phạm Quá Tốc Độ" ở cột bên phải giao diện.
- **Thông tin hiển thị:** Ảnh thu nhỏ phương tiện vi phạm, mã định danh track ID, loại xe, thời gian vi phạm và tốc độ đo được đóng khung đỏ.

### 5.2. Phóng to ảnh bằng chứng
1. **Hành động:** Nhấn chuột trái trực tiếp vào hình ảnh thu nhỏ của phương tiện vi phạm.
2. **Kết quả mong đợi:** Cửa sổ hộp thoại phóng to (Image Modal) sẽ mở ra, hiển thị rõ ràng biển cảnh báo vi phạm và hộp bao đỏ quanh phương tiện.
3. **Đóng cửa sổ:** Nhấn vào dấu "x" ở góc trên phải hoặc nhấn chuột vào vùng tối bên ngoài ảnh để đóng cửa sổ.

---

## 6. XUẤT BÁO CÁO GIAO THÔNG RA TỆP CSV

1. **Vị trí thao tác:** Nút **Xuất CSV** (màu xanh dương) nằm ở thanh tiêu đề góc trên bên phải của trang web.
2. **Hành động:** Nhấn chuột vào nút "Xuất CSV".
3. **Kết quả mong đợi:** Trình duyệt sẽ tự động tải xuống tệp tin có tên `its_traffic_report.csv`.
4. **Kiểm tra tệp tin:** Mở tệp bằng Microsoft Excel, Notepad hoặc Google Sheets. Tệp tin được mã hóa với chuẩn UTF-8 BOM, đảm bảo hiển thị đầy đủ các cột bằng tiếng Việt có dấu:
   - STT
   - Track ID
   - Loại Phương Tiện
   - Vận Tốc (km/h)
   - Vi Phạm Quá Tốc Độ
   - Hướng Di Chuyển
   - Trạng Thái
   - Thời Gian Ghi Nhận

---

## 7. ĐẶT LẠI SỐ LIỆU (RESET DATA)

Khi cần bắt đầu một ca trực giám sát mới hoặc muốn xóa số liệu cũ:

1. **Vị trí thao tác:** Nút **Đặt lại** (có biểu tượng xoay) ở thanh tiêu đề phía trên.
2. **Hành động:** Nhấn nút "Đặt lại" và chọn **OK** trên hộp thoại xác nhận của trình duyệt.
3. **Kết quả mong đợi:** Toàn bộ các số liệu tổng trên thẻ KPI, biểu đồ Chart.js và bảng nhật ký xe sẽ được làm sạch về số 0, và hệ thống sẽ khởi tạo một phiên giám sát mới.

---

## 8. DỪNG HỆ THỐNG AN TOÀN

1. **Vị trí thao tác:** Cửa sổ dòng lệnh (PowerShell/CMD) đang chạy chương trình `run_dashboard.py`.
2. **Hành động:** Nhấn tổ hợp phím **Ctrl + C**.
3. **Kết quả mong đợi:** Máy chủ web FastAPI và chương trình OpenCV sẽ đóng toàn bộ kết nối, giải phóng camera/video và dừng tiến trình an toàn mà không làm hỏng dữ liệu.
