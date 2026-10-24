import os
from typing import Dict, Any, Tuple

# Đường dẫn thư mục gốc của dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Đường dẫn tài nguyên mặc định
MODEL_PATH = os.path.join(BASE_DIR, "vehicles_counting-master", "yolo11n.pt")
DEFAULT_VIDEO_PATH = os.path.join(BASE_DIR, "vehicles_counting-master", "NgaTuGa.mp4")
OUTPUT_VIDEO_PATH = os.path.join(BASE_DIR, "Output_upgraded.mp4")
DATABASE_PATH = os.path.join(BASE_DIR, "its_database.db")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")

# Danh mục các lớp phương tiện giao thông theo tập nhãn chuẩn COCO
# class_id: { "name": tên tiếng Anh, "label_vi": tên hiển thị tiếng Việt, "color": mã màu BGR }
TARGET_CLASSES: Dict[int, Dict[str, Any]] = {
    2: {"name": "car", "label_vi": "Ô tô", "color": (255, 140, 0)},         # Xanh lơ cam (BGR)
    3: {"name": "motorcycle", "label_vi": "Xe máy", "color": (0, 230, 0)},     # Xanh lá cây sáng
    5: {"name": "bus", "label_vi": "Xe buýt", "color": (0, 165, 255)},       # Cam đậm
    7: {"name": "truck", "label_vi": "Xe tải", "color": (255, 0, 255)}       # Tím hồng
}

# Ngưỡng vận tốc quy định trong khu vực đô thị (km/h) theo Thông tư 31/2019/TT-BGTVT
SPEED_LIMIT_KMH: float = 50.0

# Cấu hình Vùng Đo Hai Vạch Mốc (Two-Line Speed Trap Zone):
# - Vạch 1 (Vạch Đếm Xe & Bắt đầu tính giờ): Đặt ở vị trí trước (33% chiều cao khung hình ~ 280px).
#   Mục đích: Đếm phương tiện ngay khi tiến vào phạm vi giám sát, tránh bị che khuất hoặc rẽ hướng.
# - Vạch 2 (Vạch Chốt Vận Tốc & Phát hiện vi phạm): Đặt ở vị trí sau (47% chiều cao khung hình ~ 400px).
#   Mục đích: Chốt thời gian di chuyển delta_t khi xe đi hết quãng đường thực tế 8.0 mét.
SPEED_ZONE_CONFIG: Dict[str, float] = {
    "y_count_ratio": 0.33,         # Vạch 1: 33% chiều cao khung hình
    "y_speed_ratio": 0.47,         # Vạch 2: 47% chiều cao khung hình
    "real_distance_meters": 8.0,   # Khoảng cách thực tế giữa hai vạch mốc trên mặt đường (mét)
}

# Cấu hình suy luận YOLO và Bộ theo dõi BoT-SORT
TRACKER_CONFIG = {
    "tracker_type": "botsort.yaml",
    "conf_threshold": 0.20,        # Ngưỡng tin cậy cân bằng giữa phát hiện xe máy nhỏ và loại bỏ nhiễu
    "iou_threshold": 0.50,         # Ngưỡng IoU phục vụ gán ID liên tục giữa các khung hình
    "track_history_len": 40,       # Độ dài lưu vết quỹ đạo di chuyển (trail)
    "stale_track_timeout": 60      # Số frame tối đa giữ track không còn xuất hiện trước khi giải phóng
}

def validate_config() -> Tuple[bool, str]:
    """
    Kiểm tra tính hợp lệ của cấu hình hệ thống trước khi khởi động.
    Trả về: (is_valid: bool, message: str)
    """
    if not os.path.exists(MODEL_PATH):
        return False, f"Không tìm thấy file mô hình YOLO tại: {MODEL_PATH}"
    
    if SPEED_ZONE_CONFIG["y_count_ratio"] >= SPEED_ZONE_CONFIG["y_speed_ratio"]:
        return False, "Cấu hình không hợp lệ: Vạch 1 (y_count_ratio) phải nằm ở phía trên Vạch 2 (y_speed_ratio)."

    if SPEED_ZONE_CONFIG["real_distance_meters"] <= 0:
        return False, "Cấu hình không hợp lệ: Khoảng cách giữa hai vạch (real_distance_meters) phải lớn hơn 0."

    if SPEED_LIMIT_KMH <= 0 or SPEED_LIMIT_KMH > 200:
        return False, f"Giới hạn tốc độ không hợp lý: {SPEED_LIMIT_KMH} km/h"

    return True, "Cấu hình hợp lệ"
