import pytest
import math
from its_core.homography import HomographyTransformer

def compute_speed_trap(distance_m: float, delta_t: float) -> float:
    """
    Hàm tính vận tốc vùng đo hai vạch mốc (Speed Trap Formula):
        v = (distance_m / delta_t) * 3.6 (km/h)
    """
    if delta_t <= 0:
        raise ValueError("Thời gian đo delta_t phải lớn hơn 0")
    if not math.isfinite(distance_m) or not math.isfinite(delta_t):
        raise ValueError("Khoảng cách và thời gian phải là số hữu hạn")
    if distance_m <= 0:
        raise ValueError("Khoảng cách đo distance_m phải lớn hơn 0")
    
    speed_kmh = (distance_m / delta_t) * 3.6
    return round(float(speed_kmh), 1)

def is_speed_violation(speed_kmh: float, speed_limit: float = 50.0) -> bool:
    """
    Kiểm tra vi phạm: vận tốc vượt quá ngưỡng quy định (v > speed_limit).
    """
    return speed_kmh > speed_limit

class TestSpeedCalculation:
    """Kiểm thử toán học và logic vật lý của phép đo vận tốc."""

    def test_valid_speed_calculation(self):
        """Kiểm thử tính vận tốc với khoảng cách và thời gian chuẩn."""
        # 8.0 mét trong 0.8 giây: v = (8.0 / 0.8) * 3.6 = 36.0 km/h
        speed = compute_speed_trap(8.0, 0.8)
        assert speed == 36.0

        # 8.0 mét trong 1.0 giây: v = 8.0 * 3.6 = 28.8 km/h
        speed = compute_speed_trap(8.0, 1.0)
        assert speed == 28.8

    def test_zero_time_delta_raises_error(self):
        """Thời gian bằng 0 phải phát sinh ngoại lệ ValueError, không để chia cho 0."""
        with pytest.raises(ValueError, match="lớn hơn 0"):
            compute_speed_trap(8.0, 0.0)

    def test_negative_time_delta_raises_error(self):
        """Thời gian âm (lỗi thứ tự frame) phải phát sinh ngoại lệ."""
        with pytest.raises(ValueError, match="lớn hơn 0"):
            compute_speed_trap(8.0, -0.5)

    def test_infinite_or_nan_values_raise_error(self):
        """Giá trị vô cùng hoặc NaN không được chấp nhận."""
        with pytest.raises(ValueError, match="số hữu hạn"):
            compute_speed_trap(float('inf'), 1.0)
        with pytest.raises(ValueError, match="số hữu hạn"):
            compute_speed_trap(8.0, float('nan'))

    def test_speed_limit_threshold_comparison(self):
        """Kiểm tra điều kiện ranh giới so sánh ngưỡng vi phạm (50 km/h)."""
        limit = 50.0
        # Vận tốc vượt ngưỡng -> Vi phạm
        assert is_speed_violation(50.1, limit) is True
        assert is_speed_violation(65.0, limit) is True

        # Vận tốc bằng đúng ngưỡng -> Không vi phạm (<= 50 km/h là hợp lệ)
        assert is_speed_violation(50.0, limit) is False

        # Vận tốc dưới ngưỡng -> Không vi phạm
        assert is_speed_violation(49.9, limit) is False
        assert is_speed_violation(30.0, limit) is False

    def test_homography_speed_calculation(self):
        """Kiểm thử tính vận tốc qua Homography Transformer."""
        transformer = HomographyTransformer(
            src_points=[(0, 0), (100, 0), (100, 200), (0, 200)],
            real_width_meters=10.0,
            real_length_meters=20.0
        )
        assert transformer.is_calibrated() is True

        # Điểm bắt đầu (50, 0) -> tương đương (5m, 0m)
        # Điểm kết thúc (50, 100) -> tương đương (5m, 10m)
        # Quãng đường di chuyển = 10m trong 1.0s -> 36.0 km/h
        speed = transformer.calculate_speed_kmh((50, 0), (50, 100), 1.0)
        assert pytest.approx(speed, 0.1) == 36.0

        # Kiểm thử thời gian <= 0 trong Homography trả về 0.0 an toàn
        assert transformer.calculate_speed_kmh((50, 0), (50, 100), 0.0) == 0.0
        assert transformer.calculate_speed_kmh((50, 0), (50, 100), -1.0) == 0.0

