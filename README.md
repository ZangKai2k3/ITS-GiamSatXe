# HE THONG GIAM SAT GIAO THONG THONG MINH (ITS)

He thong giam sat giao thong thong minh (Intelligent Transportation System - ITS) duoc xay dung tren nen tang thi giac may tinh (Computer Vision) va hoc sau (Deep Learning) nham thuc hien tu dong hoa quy trinh: nhan dien phuong tien, theo doi quy dao di chuyen, dem luu luong phan loai, do luong van toc thuc te va phat hien cac hanh vi vi pham qua toc do trong khu vuc do thi.

Du an duoc toi uu hoa va chuan hoa toan dien tu ma nguon goc chuyen de do an, dap ung cac tieu chuan ve Clean Code, kien truc mo rong, toan ven du lieu va san sang van hanh thuc te.

---

## 1. MUC TIEU VA PHAM VI HE THONG

- **Muc tieu:** Cung cap giai phap giam sat giao thong tu dong, giup co quan quan ly giao thong hoac cac don vi nghien cuu nam bat luu luong xe thoi gian thuc, phat hien phuong tien chay qua toc do quy dinh va xuat du lieu phuc vu phan tich.
- **Pham vi ung dung:** Giao lo do thi, nut giao thong trong diem, tuyen duong noi do co dat camera quan sat goc cao (high-angle / top-down perspective).
- **Doi tuong giam sat:** Bon nhom phuong tien chinh gom xe may, o to con, xe tai va xe buyt.

---

## 2. CAC CHUC NANG CHINH

1. **Nhan dien va theo doi phuong tien (Object Detection & Multi-Object Tracking):**
   - Su dung mo hinh YOLO11 ket hop thuat toan BoT-SORT (tracker="botsort.yaml").
   - Duy tri ID phuong tien lien tuc, han che toi da tinh trang nhay ID hoac bo sot xe may co kich thuoc nho.

2. **Dem luu luong theo phan loai (Vehicle Counting & Classification):**
   - Thiet lap Vach 1 (Counting Line) o phia truoc de ghi nhan phuong tien ngay khi tien vao vung quan sat.
   - Phan loai chinh xac thanh 4 nhom: Xe may, O to, Xe tai, Xe buyt.

3. **Do van toc vat ly thuc te (Two-Line Speed Trap Measurement):**
   - Su dung Vung do hai vach moc voi khoang cach hieu chuan vat ly chuan (mac dinh 8.0 met).
   - Tinh toan van toc vat ly dua tren thoi gian dich chuyen thuc te (delta_t) giua hai vach.
   - Ho tro module bien doi phoi canh Homography de quy doi toa do pixel sang toa do mat dat tinh bang met.

4. **Phat hien vi pham va tu dong luu bang chung (Violation Detection & Evidence Capture):**
   - So sanh van toc chot voi nguong quy dinh (mac dinh 50.0 km/h theo quy dinh do thi).
   - Tu dong chup anh phuong tien vi pham, dong khung bien bao loi va luu tru vao thu muc he thong.

5. **Luu tru du lieu SQLite va bao dam tinh nhat quan (Database & Idempotency):**
   - Luu nhat ky phuong tien vao co so du lieu `its_database.db` voi che do ghi WAL (Write-Ahead Logging).
   - Co che session_id va khoa duy nhat ngan chan trung lap du lieu khi phuong tien di qua nhieu vach hoac khi video phat lap lai.

6. **Web Dashboard dieu hanh truc quan (Web Monitoring Interface):**
   - Giao dien truc quan phat luong video MJPEG thoi gian thuc.
   - Hien thi cac the chi so KPI, bieu do phan bo phuong tien Chart.js va bang chung vi pham.
   - Cho phep dieu chinh vi tri hai vach moc va nguong toc do truc tiep tren web.
   - Xuat bao cao du lieu giao thong dinh dang CSV tieu chuan.

---

## 3. KIEN TRUC TONG QUAN

He thong duoc to chuc thanh ba tang chinh:

```
[ Tang Thu Thap & Thi Giac May Tinh ]
  Camera / Video File MP4 -> YOLO11 + BoT-SORT Tracking -> Vung do 2 vach moc (Speed Trap)
                                     |
                                     v
[ Tang Xu Ly Nghiep Vu & Luu Tru ]
  ITSTracker -> Kiem tra qua vach -> Tinh toc do -> Bat vi pham -> Chup anh bang chung
                                     |
                                     v
                        SQLite Database (its_database.db)
                                     |
                                     v
[ Tang Cung Cap Dich Vu & Giao Dien ]
  FastAPI Server (REST API + MJPEG Streaming) -> Web Dashboard (TailwindCSS + Chart.js)
```

---

## 4. CONG NGHE SU DUNG

- **Ngon ngu lap trinh:** Python 3.10 - 3.14
- **Thi giac may tinh & Deep Learning:** OpenCV (opencv-python), Ultralytics YOLO11, PyTorch
- **Thuat toan Tracking:** BoT-SORT (ket hop Kalman Filter, ReID va Camera Motion Compensation)
- **Co so du lieu:** SQLite3 (tich hop che do WAL va Foreign Key/Unique Constraints)
- **Web Backend:** FastAPI, Uvicorn, Pydantic v2
- **Web Frontend:** HTML5, TailwindCSS CDN, Font Awesome 6, Chart.js
- **Kiem thu tu dong:** Pytest, HTTPX

---

## 5. YEU CAU MOI TRUONG

- He dieu hanh: Windows 10/11, Linux Ubuntu 20.04+, macOS.
- Python: Phien ban 3.10 tro len.
- Bo nho RAM: Toi thieu 4 GB (khuyen nghi 8 GB tro len).
- CPU/GPU: Co the chay tot tren CPU da nhan; ho tro tang toc CUDA neu co card do hoa NVIDIA.

Cac thu vien can thiet duoc liet ke duoi day:
```bash
pip install ultralytics opencv-python torch torchvision fastapi uvicorn pydantic pytest httpx
```

---

## 6. CAU TRUC THU MUC DU AN

```
D:\ITS-GiamSatXe\
|-- its_core/                       # Goi xu ly nghiep vu loi
|   |-- __init__.py
|   |-- config.py                   # Cau hinh tham so, nguong van toc va danh muc xe
|   |-- tracker.py                  # Module nhan dien, theo doi BoT-SORT va tinh van toc
|   |-- pipeline.py                 # Dieu phoi luong doc video va xu ly khung hinh
|   |-- database.py                 # Quan ly co so du lieu SQLite va tinh toan KPI
|   |-- homography.py               # Bien doi phoi canh mat phang sang he toa do met
|-- its_dashboard/                  # Ung dung Web Dashboard giam sat
|   |-- server.py                   # Web server FastAPI, REST API va luong MJPEG
|   |-- templates/
|       |-- index.html              # Giao dien dieu hanh TailwindCSS + Chart.js
|-- tests/                          # Bo kiem thu tu dong (Automated Test Suite)
|   |-- __init__.py
|   |-- test_speed_calculation.py   # Kiem thu phep tinh van toc va dieu kien vat ly
|   |-- test_line_crossing.py       # Kiem thu logic qua vach va chuyen trang thai
|   |-- test_database.py            # Kiem thu tinh toan ven va truy van CSDL
|   |-- test_api.py                 # Kiem thu cac API endpoint cua Dashboard
|-- snapshots/                      # Thu muc luu tru anh bang chung vi pham
|-- vehicles_counting-master/       # Du lieu goc (video NgaTuGa.mp4, weights yolo11n.pt)
|-- its_database.db                 # Tep tin co so du lieu SQLite
|-- Output_upgraded.mp4             # Video ket qua sau khi xu ly xong
|-- run_dashboard.py                # Diem khoi chay giao dien Web Dashboard
|-- run_pipeline.py                 # Diem khoi chay chuong trinh CLI xu ly video
|-- README.md                       # Tai lieu huong dan tong quan va van hanh
|-- MO_TA_HE_THONG.md               # Tai lieu dac ta kien truc va luong nghiep vu
|-- HUONG_DAN_SU_DUNG.md            # Huong dan van hanh danh cho nguoi dung
|-- KIEM_THU.md                     # Ke hoach va ket qua kiem thu he thong
```

---

## 7. HUONG DAN CAI DAT VA VAN HANH

### 7.1. Chay giao dien Web Dashboard (Khuyen nghi)

Day la phuong thuc van hanh chinh, cung cap day du man hinh video truc tiep, bang chi so KPI va chuc nang dieu chinh:

```bash
python run_dashboard.py
```

Sau khi may chu khoi dong, mo trinh duyet web (Chrome, Edge, Firefox) va truy cap dia chi:
```
http://127.0.0.1:8000
```

Tham so tuy chon:
```bash
python run_dashboard.py --host 0.0.0.0 --port 8000
```

### 7.2. Chay xu ly video qua dong lenh (CLI Pipeline)

Phuong thuc nay phu hop cho viec xu ly hang loat tep video hoac chay tren may chu khong co giao dien do hoa:

- Chay xem truc tiep man hinh OpenCV:
  ```bash
  python run_pipeline.py
  ```

- Chay che do an (Headless), khong mo cua so man hinh:
  ```bash
  python run_pipeline.py --no-display
  ```

- Xu ly so luong khung hinh gioi han (vi du 150 khung hinh):
  ```bash
  python run_pipeline.py --max-frames 150
  ```

- Chi dinh video nguon va tep ket qua khac:
  ```bash
  python run_pipeline.py --video duong_dan_video.mp4 --output video_dau_ra.mp4 --speed-limit 50
  ```

---

## 8. DU LIEU DAU RA VA LUU TRU

| Thanh phan | Vi tri luu tru | Mo ta |
| :--- | :--- | :--- |
| Video ket qua | `Output_upgraded.mp4` | Video da duoc chu thich bounding box, quy dao di chuyen, vung do va bang HUD |
| Co so du lieu | `its_database.db` | CSDL SQLite luu tru nhat ky phuong tien va bang thong ke |
| Anh bang chung | `snapshots/` | Tep anh JPG chup phuong tien vi pham toc do kem theo thong tin loi |
| Bao cao xuat ban | `its_traffic_report.csv` | File bao cao CSV duoc xuat qua nut bam tren Dashboard |

---

## 9. XU LY CAC VAN DE THUONG GAP

1. **Loi khong tim thay mo hinh (`FileNotFoundError: yolo11n.pt`):**
   - Kiem tra tep `vehicles_counting-master/yolo11n.pt` co ton tai hay khong. Neu chua co, he thong se tu dong tai tu Ultralytics hoac ban can dat file vao dung thu muc.

2. **Loi font tieng Viet tren Windows Console:**
   - He thong da tich hop co che tu dong thiet lap UTF-8 qua `sys.stdout.reconfigure(encoding='utf-8')`. Neu van bi loi, hay chay lenh `chcp 65001` tren PowerShell/CMD truoc khi khoi chay.

3. **Cong 8000 da bi su dung boi ung dung khac:**
   - Khoi dong voi cong khac: `python run_dashboard.py --port 8080`.

4. **Co so du lieu bi khoa (`sqlite3.OperationalError: database is locked`):**
   - He thong da bat che do WAL (Write-Ahead Logging) va thoi gian timeout 15 giay de ngan chan khoa du lieu. Neu van xay ra, kiem tra xem co chuong trinh DB Browser nao dang mo file database ma chua commit khong.

---

## 10. GIOI HAN HIEN TAI CUA HE THONG

- **Goc quay camera:** Phep do van toc hien tai phu hop nhat voi camera co goc quay co dinh nhin xuoi hoac cheo tu tren cao xuong. Camera di dong hoac lia goc quay lien tuc se lam bien doi khoang cach tham chieu.
- **Che khuat cuc bo:** Khi cac phuong tien co kich thuoc lon nhu xe tai hoac xe buyt che hoan toan xe may trong suot doan giua hai vach, he thong co the bi ngat quang quang duong theo doi.
- **Dieu kien anh sang:** Video ban dem hoac thoi tiet mua lon co the lam giam do tin cay cua mo hinh nhan dien COCO mac dinh.

---

## 11. LIEN KET TAI LIEU CHI TIET

- [MO_TA_HE_THONG.md](file:///d:/ITS-GiamSatXe/MO_TA_HE_THONG.md): Tai lieu dac ta kien truc, luong nghiep vu va dac ta API.
- [HUONG_DAN_SU_DUNG.md](file:///d:/ITS-GiamSatXe/HUONG_DAN_SU_DUNG.md): Huong dan van hanh chi tiet tung buoc cho nguoi dung.
- [KIEM_THU.md](file:///d:/ITS-GiamSatXe/KIEM_THU.md): Ke hoach kiem thu va ket qua xac minh cac ca kiem thu tu dong.

