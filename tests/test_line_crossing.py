import pytest

class SimulatedVehicleTrack:
    """Mô phỏng trạng thái và sự kiện đi qua hai vạch đo của một phương tiện."""

    def __init__(self, track_id: int, label_vi: str = "Xe máy", y_count: int = 280, y_speed: int = 400):
        self.track_id = track_id
        self.label_vi = label_vi
        self.y_count = y_count
        self.y_speed = y_speed
        
        self.prev_y = None
        self.curr_y = None
        self.counted = False
        self.speed_locked = False
        self.entry_frame = None
        self.exit_frame = None
        self.speed_kmh = 0.0

    def update_position(self, y: int, frame_idx: int, fps: float = 30.0, distance_m: float = 8.0):
        """Cập nhật tọa độ y mới và kiểm tra điều kiện kích hoạt các vạch đo."""
        if self.prev_y is None:
            self.prev_y = y
            self.curr_y = y
            return

        self.prev_y = self.curr_y
        self.curr_y = y

        # 1. Kiểm tra Vạch 1: Đếm xe & Kích hoạt bấm giờ
        if not self.counted and self.prev_y < self.y_count and self.curr_y >= self.y_count:
            self.counted = True
            self.entry_frame = frame_idx

        # 2. Kiểm tra Vạch 2: Chốt vận tốc
        if not self.speed_locked and self.prev_y < self.y_speed and self.curr_y >= self.y_speed:
            self.exit_frame = frame_idx
            self.speed_locked = True
            if self.entry_frame is not None:
                delta_f = self.exit_frame - self.entry_frame
                delta_t = delta_f / fps if fps > 0 else 0.0
                if delta_t > 0:
                    self.speed_kmh = round((distance_m / delta_t) * 3.6, 1)

class TestLineCrossingLogic:
    """Kiểm thử tính đúng đắn của logic vượt vạch và chuyển đổi trạng thái."""

    def test_normal_crossing_both_lines(self):
        """Xe di chuyển bình thường từ trên xuống qua Vạch 1 rồi Vạch 2."""
        car = SimulatedVehicleTrack(track_id=1, y_count=280, y_speed=400)
        
        # Frame 1: Chưa đến Vạch 1
        car.update_position(y=200, frame_idx=1)
        assert car.counted is False
        assert car.speed_locked is False

        # Frame 10: Chạm và vượt qua Vạch 1 (275 -> 285)
        car.update_position(y=275, frame_idx=9)
        car.update_position(y=285, frame_idx=10)
        assert car.counted is True
        assert car.entry_frame == 10
        assert car.speed_locked is False

        # Frame 30: Di chuyển giữa hai vạch (y = 350)
        car.update_position(y=350, frame_idx=30)
        assert car.counted is True
        assert car.speed_locked is False

        # Frame 40: Chạm và vượt qua Vạch 2 (395 -> 405)
        # Delta frames = 40 - 10 = 30 frames (1.0 giây tại 30 FPS)
        # Quãng đường 8.0 mét -> Vận tốc = 8.0 * 3.6 = 28.8 km/h
        car.update_position(y=395, frame_idx=39)
        car.update_position(y=405, frame_idx=40, fps=30.0, distance_m=8.0)
        assert car.speed_locked is True
        assert car.exit_frame == 40
        assert car.speed_kmh == 28.8

    def test_line_oscillation_does_not_double_count(self):
        """Xe dao động quanh vạch (nhấp nháy bounding box) không bị đếm trùng."""
        bike = SimulatedVehicleTrack(track_id=2, y_count=280, y_speed=400)
        
        bike.update_position(y=278, frame_idx=1)
        # Vượt qua Vạch 1 lần đầu -> Đã đếm
        bike.update_position(y=282, frame_idx=2)
        assert bike.counted is True
        assert bike.entry_frame == 2

        # Lùi lại chút do nhiễu tracking (y = 279 < 280)
        bike.update_position(y=279, frame_idx=3)
        # Vượt qua lại (y = 283 >= 280)
        bike.update_position(y=283, frame_idx=4)
        
        # Vẫn giữ nguyên trạng thái và entry_frame gốc, không bị ghi nhận 2 lần
        assert bike.counted is True
        assert bike.entry_frame == 2

    def test_reverse_direction_not_counted(self):
        """Xe đi ngược chiều (từ dưới lên trên: y lớn sang y nhỏ) không được đếm vào luồng xuôi."""
        rev_car = SimulatedVehicleTrack(track_id=3, y_count=280, y_speed=400)
        
        rev_car.update_position(y=300, frame_idx=1)
        rev_car.update_position(y=270, frame_idx=5) # Đi ngược từ 300 lên 270
        
        # prev_y (300) không nhỏ hơn y_count (280) -> Không thỏa điều kiện
        assert rev_car.counted is False
        assert rev_car.speed_locked is False

    def test_vehicle_turns_before_line_2(self):
        """Xe rẽ trước khi tới Vạch 2: được đếm nhưng không chốt vận tốc."""
        moto = SimulatedVehicleTrack(track_id=4, y_count=280, y_speed=400)
        moto.update_position(y=260, frame_idx=1)
        moto.update_position(y=285, frame_idx=5)
        assert moto.counted is True

        # Xe dừng hoặc rẽ nhánh, dừng ở y = 320
        moto.update_position(y=320, frame_idx=20)
        assert moto.speed_locked is False
        assert moto.speed_kmh == 0.0

