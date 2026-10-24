# HUONG DAN SU DUNG HE THONG GIAM SAT GIAO THONG ITS

Tai lieu nay huong dan chi tiet tung buoc danh cho can bo dieu hanh, quan tri vien hoac nguoi dung khong chuyen ve lap trinh de khoi dong, van hanh, theo doi va khai thac du lieu tu He thong ITS.

---

## 1. CHUAN BI MOI TRUONG

Truoc khi khoi dong ung dung, hay dam bao may tinh da duoc cai dat:
- He dieu hanh: Windows 10/11 hoac Linux / macOS.
- Trinh duyet web hien dai: Google Chrome, Microsoft Edge hoac Mozilla Firefox.
- Python phien ban 3.10 tro len da duoc cai dat va them vao bien moi truong PATH.

Kiem tra bang cach mo PowerShell hoac Command Prompt:
```bash
python --version
```

---

## 2. KHOI DONG HE THONG

### 2.1. Khoi dong Web Dashboard (Giao dien chinh)

1. **Vi tri thao tac:** Cua so dong lenh (PowerShell hoac Terminal) tai thu muc goc cua du an: `D:\ITS-GiamSatXe`.
2. **Hanh dong:** Nhap dong lenh sau va nhan phím Enter:
   ```bash
   python run_dashboard.py
   ```
3. **Ket qua mong doi:** Man hinh console hien thi thong bao khoi dong:
   ```
   =================================================================
      KHOI DONG HE THONG ITS WEB DASHBOARD
      Dia chi truy cap: http://127.0.0.1:8000
      Bam Ctrl+C de dung may chu
   =================================================================
   ```
4. **Cach xu ly neu gap loi:** Neu thong bao loi "Address already in use", co nghia cong 8000 da bi ung dung khac chiem dung. Khoi dong lai voi cong 8080:
   ```bash
   python run_dashboard.py --port 8080
   ```

### 2.2. Mo giao dien Web

1. **Hanh dong:** Mo trinh duyet web va nhap dia chi:
   ```
   http://127.0.0.1:8000
   ```
2. **Ket qua mong doi:** Giao dien trung tam dieu hanh ITS mau toi (Dark Mode) xuat hien voi day du man hinh camera, cac the KPI thong ke va bieu do phan bo phuong tien.

---

## 3. QUAN SAT VIDEO VA DOC CAC CHI SO

### 3.1. Man hinh video thoi gian thuc
- **Vi tri:** O ben trai giao dien, khung "Video Giam Sat Real-Time".
- **Y nghia cac ky hieu tren man hinh:**
  - **Vach 1 mau vang:** Vach dem phuong tien va bat dau do toc do. Phuong tien di xuong cham vach nay se duoc he thong ghi nhan ngay lap tuc.
  - **Vach 2 mau xanh lo:** Vach chot toc do va phat hien vi pham. Phuong tien chay qua day se duoc he thong tinh toan van toc thuc te dua tren quang duong 8.0 met.
  - **Khung hop bao (Bounding Box):**
    - Khung xanh la cay: Phuong tien xe may hop le.
    - Khung cam / tim: Phuong tien o to / xe tai hop le.
    - Khung mau do: Phuong tien chay qua toc do quy dinh (> 50 km/h).
  - **The thong tin tren xe:** Hien thi ID phuong tien, loai xe va toc do (vi du: `#24 Xe may | 32.5 km/h [Chot]`).
  - **Bang HUD goc trai:** Hien thi tong so xe da qua vach va chi tiet tung loai xe.

### 3.2. Bang the chi so KPI
Nam o hang tren cung cua giao dien, gom 6 the chi so duoc dong bo tu co so du lieu:
1. **Tong Phuong Tien:** Tong so phuong tien doc lap da duoc ghi nhan qua Vach 1.
2. **Xe may:** So luong va ty le phan tram luu luong xe 2 banh.
3. **O to:** So luong va ty le phan tram xe o to con.
4. **Xe tai / Quyt:** Tong luu luong phuong tien van tai hang hoa va hanh khach.
5. **Toc do TB:** Van toc trung binh thuc te tinh bang km/h cua tat ca cac phuong tien da qua Vach 2.
6. **Qua toc do:** Tong so luong truong hop vi pham chay qua toc do cho phep.

---

## 4. DIEU CHINH VI TRI VACH DO VA NGUONG TOC DO

Khi camera thay doi goc quan sat hoac can tinh chinh pham vi do toc do:

1. **Vi tri thao tac:** Khung dieu khien ngay ben duoi man hinh video.
2. **Cac tham so dieu chinh:**
   - **Vach 1 [Truoc] (Dem xe):** Keo thanh truot de dieu chinh do cao Vach 1 (khoang hop le: 18% - 45% chieu cao anh).
   - **Vach 2 [Sau] (Chot toc do):** Keo thanh truot de dieu chinh do cao Vach 2 (khoang hop le: 35% - 65% chieu cao anh).
   - **Gioi han toc do:** Nhap gia tri van toc toi da cho phep tai doan duong (vi du: 40 km/h, 50 km/h hoac 60 km/h).
3. **Hanh dong:** Bam vao nut **Cap Nhat Vung Do** (mau xanh cyan).
4. **Ket qua mong doi:** Hop thoai thong bao "Da cap nhat Vach Dem Xe & Vach Tinh Toc Do thanh cong!" xuat hien, va hai duong ke tren man hinh video se tu dong dich chuyen den vi tri moi.
5. **Luu y quan trong:** Vach 1 bat buoc phai nam o phia truoc (do cao nho hon) Vach 2 it nhat 5%. Neu keo Vach 1 thap hon hoac bang Vach 2, he thong se tu choi cap nhat de tranh sai lech phep tinh van toc.

---

## 5. TRA CUU VA XEM ANH BANG CHUNG VI PHAM

### 5.1. Xem danh sach vi pham
- **Vi tri:** Khung "Bang Chung Vi Pham Qua Toc Do" o cot ben phai giao dien.
- **Thong tin hien thi:** Anh thu nho phuong tien vi pham, ma dinh danh track ID, loai xe, thoi gian vi pham va toc do do duoc duoc dong khung do.

### 5.2. Phong to anh bang chung
1. **Hanh dong:** Nhan chuot trai truc tiep vao hinh anh thu nho cua phuong tien vi pham.
2. **Ket qua mong doi:** Cua so hop thoai phong to (Image Modal) se mo ra, hien thi ro rang bien canh bao vi pham va hop bao do quanh phuong tien.
3. **Dong cua so:** Nhan vao dau "x" o goc tren phai hoac nhan chuot vao vung toi ben ngoai anh de dong cua so.

---

## 6. XUAT BAO CAO GIAO THONG RA TEP CSV

1. **Vi tri thao tac:** Nut **Xuat CSV** (mau xanh duong) nam o thanh tieu de goc tren ben phai cua trang web.
2. **Hanh dong:** Nhan chuot vao nut "Xuat CSV".
3. **Ket qua mong doi:** Trinh duyet se tu dong tai xuong tep tin co ten `its_traffic_report.csv`.
4. **Kiem tra tep tin:** Mo tep bang Microsoft Excel, Notepad hoac Google Sheets. Tep tin duoc ma hoa voi chuan UTF-8 BOM, dam bao hien thi day du cac cot bang tieng Viet co dau:
   - STT
   - Track ID
   - Loai Phuong Tien
   - Van Toc (km/h)
   - Vi Pham Qua Toc Do
   - Huong Di Chuyen
   - Trang Thai
   - Thoi Gian Ghi Nhan

---

## 7. DAT LAI SO LIEU (RESET DATA)

Khi can bat dau mot ca truc giam sat moi hoac muon xoa so lieu cu:

1. **Vi tri thao tac:** Nut **Dat lai** (co bieu tuong xoay) o thanh tieu de phia tren.
2. **Hanh dong:** Nhan nut "Dat lai" va chon **OK** tren hop thoai xac nhan cua trinh duyet.
3. **Ket qua mong doi:** Toan bo cac so lieu tong tren the KPI, bieu do Chart.js va bang nhat ky xe se duoc lam sach ve so 0, va he thong se khoi tao mot phien giam sat moi.

---

## 8. DUNG HE THONG AN TOAN

1. **Vi tri thao tac:** Cua so dong lenh (PowerShell/CMD) dang chay chuong trinh `run_dashboard.py`.
2. **Hanh dong:** Nhan to hop phim **Ctrl + C**.
3. **Ket qua mong doi:** May chu web FastAPI va chuong trinh OpenCV se dong toan bo ket noi, giai phong camera/video va dung tien trinh an toan ma khong lam hong du lieu.

