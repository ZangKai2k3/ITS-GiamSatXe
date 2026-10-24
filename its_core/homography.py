import numpy as np
from typing import List, Tuple, Optional

class HomographyTransformer:
    """
    Module xử lý biến đổi phối cảnh (Perspective Transformation / Homography).
    
    Nguyên lý toán học:
    Ánh xạ tọa độ điểm ảnh 2D từ mặt phẳng cảm biến camera [u, v, 1]^T sang tọa độ thực tế
    trên mặt phẳng đường (Bird's Eye View - BEV) [X, Y, 1]^T tính bằng mét thông qua ma trận H (3x3):
        [X']       [u]
        [Y'] = H * [v]   với X = X' / W',  Y = Y' / W'
        [W']       [1]
    
    Ứng dụng:
    Cho phép đo khoảng cách vật lý thực tế (mét) di chuyển trên mặt đường giữa các khung hình,
    từ đó tính toán vận tốc tức thời hoặc vận tốc trung bình độc lập với góc nghiêng camera.
    """

    def __init__(
        self,
        src_points: Optional[List[Tuple[float, float]]] = None,
        real_width_meters: float = 12.0,
        real_length_meters: float = 24.0
    ):
        """
        Khởi tạo bộ biến đổi phối cảnh:
        - src_points: Danh sách 4 điểm mốc trên ảnh theo thứ tự:
          [Top-Left, Top-Right, Bottom-Right, Bottom-Left].
        - real_width_meters: Chiều rộng thực tế của vùng đo mốc (mét).
        - real_length_meters: Chiều dài thực tế của vùng đo mốc (mét).
        """
        self.real_width = float(real_width_meters)
        self.real_length = float(real_length_meters)
        self.src_points = None
        self.H = None
        self.cv2 = None

        if src_points is not None:
            self.set_source_points(src_points)

    def _get_cv2(self):
        """Tải trễ thư viện OpenCV để tối ưu thời gian khởi động."""
        if self.cv2 is None:
            import cv2
            self.cv2 = cv2
        return self.cv2

    def set_source_points(self, src_points: List[Tuple[float, float]]) -> bool:
        """
        Thiết lập 4 điểm mốc chuẩn trên ảnh và tính toán ma trận phối cảnh H.
        Yêu cầu: chính xác 4 điểm không thẳng hàng.
        """
        if len(src_points) != 4:
            raise ValueError(f"Yêu cầu chính xác 4 điểm phối cảnh, nhận được {len(src_points)} điểm.")

        cv2 = self._get_cv2()
        self.src_points = np.array(src_points, dtype=np.float32)

        # Tọa độ mặt phẳng hình chữ nhật thực tế tính bằng mét
        dst_points = np.array([
            [0.0, 0.0],                          # Top-Left (Gốc tọa độ 0,0)
            [self.real_width, 0.0],              # Top-Right
            [self.real_width, self.real_length], # Bottom-Right
            [0.0, self.real_length]              # Bottom-Left
        ], dtype=np.float32)

        try:
            self.H = cv2.getPerspectiveTransform(self.src_points, dst_points)
            return True
        except Exception as e:
            print(f"[Homography Error] Không thể tính ma trận H: {e}")
            self.H = None
            return False

    def is_calibrated(self) -> bool:
        """Kiểm tra hệ thống đã được hiệu chuẩn ma trận H hay chưa."""
        return self.H is not None

    def transform_point(self, pt: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Chuyển đổi một điểm tọa độ pixel (u, v) sang tọa độ mặt đất thực tế (X, Y) tính bằng mét.
        Nếu hệ thống chưa hiệu chuẩn ma trận H, trả về None.
        """
        if self.H is None or pt is None:
            return None

        cv2 = self._get_cv2()
        point_array = np.array([[[float(pt[0]), float(pt[1])]]], dtype=np.float32)
        try:
            transformed = cv2.perspectiveTransform(point_array, self.H)
            x_real = float(transformed[0][0][0])
            y_real = float(transformed[0][0][1])
            return x_real, y_real
        except Exception as e:
            print(f"[Homography Error] Lỗi chuyển đổi tọa độ: {e}")
            return None

    def calculate_speed_kmh(
        self,
        point_prev: Optional[Tuple[float, float]],
        point_curr: Optional[Tuple[float, float]],
        time_delta_seconds: float
    ) -> float:
        """
        Tính toán vận tốc (km/h) giữa hai điểm tọa độ pixel thông qua ma trận Homography:
        1. Ánh xạ 2 điểm pixel sang 2 điểm mét trên mặt đất.
        2. Tính khoảng cách Euclidean thực tế: d = sqrt(dx^2 + dy^2).
        3. Vận tốc (km/h) = (d / time_delta) * 3.6.
        """
        # Kiểm tra điều kiện thời gian đo phải dương và có đủ tọa độ
        if time_delta_seconds <= 0 or point_prev is None or point_curr is None:
            return 0.0

        real_prev = self.transform_point(point_prev)
        real_curr = self.transform_point(point_curr)

        if real_prev is None or real_curr is None:
            return 0.0

        # Khoảng cách Euclidean thực tế trên mặt đất (mét)
        dx = real_curr[0] - real_prev[0]
        dy = real_curr[1] - real_prev[1]
        distance_meters = np.hypot(dx, dy)

        # Chuyển đổi từ m/s sang km/h
        speed_mps = distance_meters / time_delta_seconds
        speed_kmh = speed_mps * 3.6
        return float(round(speed_kmh, 1))
