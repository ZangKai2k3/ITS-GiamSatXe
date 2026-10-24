# KE HOACH VA KET QUA KIEM THU HE THONG ITS

Tai lieu nay ghi nhan toan bo ke hoach kiem thu, danh sach ca kiem thu tu dong (Automated Test Suite) va ket qua thuc nghiem thuc te tren He thong ITS tai `D:\ITS-GiamSatXe`.

---

## 1. MUC TIEU KIEM THU

Xac minh va bao dam he thong hoat dong chinh xac tren 4 tieu chi cot loi:
1. **Tinh dung dan cua phep tinh van toc:** Cac cong thuc vat ly va bien doi hinh hoc khong gay ra loi chia cho 0, khong chap nhan thoi gian am hoac gia tri vo cung, va xu ly dung cac nguong vi pham.
2. **Logic qua vach va chuyen doi trang thai:** Phuong tien qua Vach 1 duoc dem dung, khong bi dem lap khi rung lac quanh vach, va chot toc do chinh xac khi qua Vach 2.
3. **Tinh toan ven va bat bien cua co so du lieu (Database Idempotency):** Khong gay trung lap ban ghi khi phuong tien qua nhieu vach hoac khi video phat lai; thong ke KPI khop tuyet doi voi du lieu thuc te.
4. **Bao mat va do on dinh cua Dashboard API:** Cac endpoint tra ve dung ma trang thai HTTP, kiem soat chat che tham so dau vao va phong chong lo hong duyet thu muc.

---

## 2. MOI TRUONG KIEM THU

- **He dieu hanh:** Microsoft Windows 10/11 x64
- **Trinh thong dich Python:** Python 3.14.8
- **Cong cu kiem thu:** Pytest 9.1.1, HTTPX 0.28.1 (FastAPI TestClient)
- **Thu vien thi giac & Deep Learning:** OpenCV 4.13.0, Ultralytics 8.3.238, PyTorch 2.7.0, NumPy 2.2.3
- **Du lieu thu nghiem:** Video giao lo Nga Tu Ga (`NgaTuGa.mp4`), do phan giai $480 \times 854$, $29.95\text{ FPS}$, 630 khung hinh.

---

## 3. DANH SACH CAC CA KIEM THU TU DONG (AUTOMATED TEST SUITE)

Bo kiem thu gom 25 ca kiem thu tu dong duoc to chuc trong thu muc `tests/`:

### 3.1. Nhom 1: Kiem thu phep tinh van toc (`tests/test_speed_calculation.py`)

| Ma ca kiem thu | Muc tieu kiem thu | Du lieu dau vao | Ket qua mong doi | Ket qua thuc te | Trang thai |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-SPD-01` | Tinh van toc hop le voi khoang cach va thoi gian chuan | $D = 8.0\text{ m}, \Delta t = 0.8\text{ s}$ | $v = 36.0\text{ km/h}$ | $v = 36.0\text{ km/h}$ | PASSED |
| `TC-SPD-02` | Thoi gian bang 0 | $D = 8.0\text{ m}, \Delta t = 0.0\text{ s}$ | Phat sinh `ValueError` ("lon hon 0") | Phat sinh `ValueError` hop le | PASSED |
| `TC-SPD-03` | Thoi gian am (loi nguoc thu tu frame) | $D = 8.0\text{ m}, \Delta t = -0.5\text{ s}$ | Phat sinh `ValueError` ("lon hon 0") | Phat sinh `ValueError` hop le | PASSED |
| `TC-SPD-04` | Gia tri vo cung hoac NaN | $D = \infty$ hoac $\Delta t = \text{NaN}$ | Phat sinh `ValueError` ("so huu han") | Phat sinh `ValueError` hop le | PASSED |
| `TC-SPD-05` | So sanh nguong vi pham toc do | $v = 50.1$ (Vi pham), $v = 50.0$ (Hop le), $v = 49.9$ (Hop le) | True cho $50.1$, False cho $50.0$ va $49.9$ | Khop tuyet doi | PASSED |
| `TC-SPD-06` | Phep bien doi Homography | 4 diem moc $(10\text{m} \times 20\text{m})$, di chuyen $10\text{m}$ trong $1.0\text{s}$ | $v \approx 36.0\text{ km/h}$ | $v = 36.0\text{ km/h}$ | PASSED |

### 3.2. Nhom 2: Kiem thu logic qua vach (`tests/test_line_crossing.py`)

| Ma ca kiem thu | Muc tieu kiem thu | Du lieu dau vao | Ket qua mong doi | Ket qua thuc te | Trang thai |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-LNE-01` | Xe di chuyen binh thuong qua Vach 1 roi Vach 2 | $y: 200 \rightarrow 285 \rightarrow 350 \rightarrow 405$ | Dem tai frame qua Vach 1, chot toc do tai Vach 2 | Dung thu tu va dung toc do | PASSED |
| `TC-LNE-02` | Xe dao dong quanh vach (nhap nhay toa do) | $y: 278 \rightarrow 282 \rightarrow 279 \rightarrow 283$ | Chi dem dung 1 lan duy nhat | Khong bi dem lap | PASSED |
| `TC-LNE-03` | Xe di nguoc chieu (tu duoi len tren) | $y: 300 \rightarrow 270$ | Khong duoc dem vao luong xuoi | Khong tang bo dem | PASSED |
| `TC-LNE-04` | Xe re huong truoc khi cham Vach 2 | $y: 260 \rightarrow 285 \rightarrow 320$ (dung lai) | Duoc dem nhung van toc $= 0.0$ | Dem dung, khong chot toc do ao | PASSED |

### 3.3. Nhom 3: Kiem thu co so du lieu SQLite (`tests/test_database.py`)

| Ma ca kiem thu | Muc tieu kiem thu | Du lieu dau vao | Ket qua mong doi | Ket qua thuc te | Trang thai |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-DB-01` | Khoi tao bang du lieu va cac chi muc | Database tam thoi tren dia | Tao du `vehicle_logs`, `traffic_stats`, va index | Cac bang va index deu ton tai | PASSED |
| `TC-DB-02` | Tinh bat bien (Idempotency) khi ghi Vach 1 | Goi `log_vehicle_entry` 2 lan cung ID va session | Chi co duy nhat 1 ban ghi trong CSDL | So luong dong $= 1$ | PASSED |
| `TC-DB-03` | Cap nhat van toc Vach 2 | Goi `update_vehicle_speed` cho xe da qua Vach 1 | Cap nhat dung dong hien co, status: speed_locked | Cap nhat thanh cong, khong tao dong moi | PASSED |
| `TC-DB-04` | Tinh toan KPI tong hop | 3 xe (1 xe hop le, 1 xe re truoc vach 2, 1 xe qua toc do) | Tong: 3, Xe may: 2, O to: 1, Vtoc TB: 45.0, Vi pham: 1 | Khop tuyet doi so lieu | PASSED |
| `TC-DB-05` | Truy van danh sach vi pham | 1 xe vi pham (58 km/h), 1 xe binh thuong (35 km/h) | Chi tra ve dung 1 ban ghi vi pham kem snapshot | Danh sach chi chua xe vi pham | PASSED |
| `TC-DB-06` | Dat lai so lieu theo session | session_A va session_B, chi xoa session_A | session_A tong $= 0$, session_B giu nguyen | Cach ly phien hoan hao | PASSED |

### 3.4. Nhom 4: Kiem thu Dashboard REST API (`tests/test_api.py`)

| Ma ca kiem thu | Muc tieu kiem thu | Du lieu dau vao | Ket qua mong doi | Ket qua thuc te | Trang thai |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-API-01` | Cung cap trang giao dien chu | `GET /` | HTTP 200, noi dung chua tieu de he thong | HTTP 200, day du HTML | PASSED |
| `TC-API-02` | Tra ve so lieu KPI | `GET /api/stats` | HTTP 200, JSON day du cac truong thong ke | HTTP 200, day du cac truong | PASSED |
| `TC-API-03` | Tra ve danh sach vi pham | `GET /api/violations` | HTTP 200, mang JSON chua cac vu vi pham | HTTP 200, mang hop le | PASSED |
| `TC-API-04` | Tra ve nhat ky phuong tien | `GET /api/history` | HTTP 200, mang JSON 50 ban ghi moi nhat | HTTP 200, mang hop le | PASSED |
| `TC-API-05` | Cap nhat cau hinh hop le | `POST /api/settings` voi vach 1 < vach 2, toc do 60 | HTTP 200, `{"status": "success"}` | HTTP 200, cap nhat thanh cong | PASSED |
| `TC-API-06` | Tu choi khi thu tu vach bi dao nguoc | `POST /api/settings` voi vach 1 = 0.5, vach 2 = 0.4 | HTTP 422 Unprocessable Entity | HTTP 422, tu choi hop le | PASSED |
| `TC-API-07` | Tu choi van toc gioi han khong hop le | `POST /api/settings` voi speed_limit = 5.0 km/h | HTTP 422 Unprocessable Entity | HTTP 422, tu choi hop le | PASSED |
| `TC-API-08` | Dat lai so lieu qua API | `POST /api/reset` | HTTP 200, tra ve ma session_id moi | HTTP 200, lam sach du lieu | PASSED |
| `TC-API-09` | Xuat bao cao dinh dang CSV | `GET /api/export` | HTTP 200, content-type text/csv, tieu de dung | HTTP 200, file CSV hop le | PASSED |

---

## 4. KET QUA CHAY TEST THUC TE

Lenh thuc thi:
```bash
python -m pytest tests/ -v
```

Ket qua ghi nhan tren moi truong:
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

======================== 25 passed in 4.51s ========================
```

Ty le dat: **25 / 25 ca kiem thu (100% PASSED)**.

---

## 5. KET QUA KIEM THU TICH HOP TREN VIDEO NGA TU GA

Chay thuc te toan bo chuong trinh `run_pipeline.py` tren tep `NgaTuGa.mp4`:
- Tong so khung hinh xu ly: 630 frames (toan bo thoi luong video).
- Tong so phuong tien da qua Vach 1: 42 phuong tien.
  - Xe may: 14 phuong tien (tang tu 0 xe o ban cu len 14 xe nho BoT-SORT).
  - O to: 16 phuong tien.
  - Xe tai: 8 phuong tien.
  - Xe buyt: 4 phuong tien.
- Van toc trung binh thuc te: 35.7 km/h (phu hop hoan toan voi toc do luu thong thuc te tai giao lo do thi).
- So vu vi pham qua toc do (> 50.0 km/h): 3 truong hop (duoc chup anh luu vao thu muc `snapshots/`).
- Video ket qua dau ra: `Output_upgraded.mp4` co dung luong khoang 25 MB, hien thi muot ma toan bo hop bao, quy dao, vung do va bang HUD.

---

## 6. CAC GIOI HAN KIEM THU CON LAI

1. **Tap du lieu video thuc nghiem:** Hien tai he thong chi duoc kiem thu tich hop tren mot video mau duy nhat la `NgaTuGa.mp4`. De danh gia toan dien tren thuc te, can thu nghiem them tren cac video co dieu kien thoi tiet khac nhau (mua, dem, gio chieu nguoc nang).
2. **Kiem thu hieu nang voi luong RTSP thuc:** Luong RTSP tu camera giao thong IP thuc te co the bi mat goi hoac tre mang (network jitter). Can kiem thu them co che bo qua frame (frame skipping / drop frame) khi mang bi nghen.

