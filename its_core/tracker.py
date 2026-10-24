import cv2
import numpy as np
import os
import time
from collections import deque
from typing import Dict, Any, Optional, Tuple, Set
from its_core.config import (
    TARGET_CLASSES, SPEED_LIMIT_KMH, SPEED_ZONE_CONFIG,
    SNAPSHOT_DIR, TRACKER_CONFIG
)

class ITSTracker:
    """
    Bộ nhận diện, theo dõi và đo vận tốc phương tiện giao thông thông minh (ITS):
    
    Quy trình hoạt động:
    1. Nhận diện và theo dõi đối tượng:
       Sử dụng YOLO11n tích hợp thuật toán BoT-SORT (tracker='botsort.yaml'). BoT-SORT kết hợp
       thông tin chuyển động Kalman Filter với đặc trưng ReID và hiệu chỉnh biến đổi camera (GMC),
       giúp duy trì ID ổn định cho xe máy, ô tô, xe tải và xe buýt.
    2. Vạch 1 - Vạch Đếm Xe & Bắt đầu tính giờ (Line 1 - Entry Line):
       Đặt tại y_count (~33% chiều cao). Phương tiện vừa vượt qua vạch này được đếm ngay lập tức
       vào tổng số và phân loại, ghi nhận vào CSDL.
    3. Vùng Đo Tốc Độ Hai Vạch Mốc (Speed Trap Zone):
       Đoạn đường thực tế giữa Vạch 1 và Vạch 2 có chiều dài D = 8.0 mét.
    4. Vạch 2 - Vạch Chốt Vận Tốc & Phát hiện vi phạm (Line 2 - Speed Lock Line):
       Đặt tại y_speed (~47% chiều cao). Khi xe chạm vạch này, hệ thống chốt delta_t và tính vận tốc:
           v = (D / delta_t) * 3.6 (km/h)
       Nếu v > speed_limit, kích hoạt ghi hình bằng chứng và lưu trạng thái vi phạm vào CSDL.
    """

    def __init__(
        self,
        model_path: str,
        db=None,
        speed_limit: float = SPEED_LIMIT_KMH,
        session_id: str = "default_session"
    ):
        from ultralytics import YOLO
        self.model = YOLO(model_path)
        self.db = db
        self.speed_limit = float(speed_limit)
        self.session_id = str(session_id)
        
        # Cấu hình vùng đo hai vạch mốc
        self.distance_meters = float(SPEED_ZONE_CONFIG.get("real_distance_meters", 8.0))
        self.y_count_ratio = float(SPEED_ZONE_CONFIG.get("y_count_ratio", 0.33))
        self.y_speed_ratio = float(SPEED_ZONE_CONFIG.get("y_speed_ratio", 0.47))
        self.y_count: Optional[int] = None
        self.y_speed: Optional[int] = None

        # Cấu hình tracker từ config
        self.conf_threshold = float(TRACKER_CONFIG.get("conf_threshold", 0.20))
        self.iou_threshold = float(TRACKER_CONFIG.get("iou_threshold", 0.50))
        self.history_len = int(TRACKER_CONFIG.get("track_history_len", 40))
        self.stale_timeout = int(TRACKER_CONFIG.get("stale_track_timeout", 60))

        # Quản lý trạng thái từng phương tiện (Key: track_id)
        self.tracks: Dict[int, Dict[str, Any]] = {}
        
        # Thống kê tổng hợp trong bộ nhớ (được đồng bộ với CSDL)
        self.class_counts = {cls_info["label_vi"]: 0 for cls_info in TARGET_CLASSES.values()}
        self.total_counted = 0
        self.counted_ids: Set[int] = set()
        self.speed_locked_ids: Set[int] = set()
        self.violations_count = 0
        
        # Thư mục lưu ảnh bằng chứng vi phạm
        self.snapshot_dir = SNAPSHOT_DIR
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def set_zone_positions(self, y_count: int, y_speed: int) -> None:
        """Cập nhật tọa độ pixel y của hai vạch đo."""
        self.y_count = int(y_count)
        self.y_speed = int(y_speed)

    def set_session_id(self, session_id: str) -> None:
        """Thiết lập mã phiên làm việc mới."""
        self.session_id = str(session_id)

    def reset_stats(self) -> None:
        """Đặt lại toàn bộ trạng thái và thống kê trong bộ nhớ."""
        self.tracks.clear()
        self.counted_ids.clear()
        self.speed_locked_ids.clear()
        self.total_counted = 0
        self.violations_count = 0
        for k in self.class_counts:
            self.class_counts[k] = 0

    def process_frame(self, frame: np.ndarray, frame_idx: int = 0, fps: float = 30.0) -> np.ndarray:
        """
        Xử lý từng khung hình video theo pipeline thời gian thực:
        1. Khởi tạo vị trí 2 vạch đo nếu chưa thiết lập.
        2. Chạy suy luận nhận diện và theo dõi BoT-SORT.
        3. Cập nhật quỹ đạo di chuyển và điểm đại diện.
        4. Kiểm tra sự kiện đi qua Vạch 1 (đếm xe) và Vạch 2 (chốt tốc độ).
        5. Xác định vi phạm và chụp ảnh bằng chứng.
        6. Vẽ bounding box, vạch mốc và HUD thông tin lên ảnh.
        """
        h, w = frame.shape[:2]
        
        # Khởi tạo tọa độ pixel hai vạch mốc theo tỷ lệ cấu hình
        if self.y_count is None:
            self.y_count = int(h * self.y_count_ratio)
        if self.y_speed is None:
            self.y_speed = int(h * self.y_speed_ratio)

        # Chạy YOLO11 Tracking với BoT-SORT
        results = self.model.track(
            frame, 
            persist=True, 
            tracker=TRACKER_CONFIG.get("tracker_type", "botsort.yaml"),
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False, 
            classes=list(TARGET_CLASSES.keys())
        )
        
        annotated_frame = frame.copy()

        # Vẽ Vùng Đo và Hai Vạch Mốc
        self._draw_lines_and_zone(annotated_frame, w, h)

        if results and len(results) > 0 and results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            confidences = results[0].boxes.conf.cpu().numpy()

            for box, track_id, cls_id, conf in zip(boxes, track_ids, class_ids, confidences):
                track_id = int(track_id)
                x1, y1, x2, y2 = map(int, box)

                # Chọn điểm đại diện: Điểm tâm (center_x, center_y) của bounding box
                # Điểm tâm phản ánh ổn định trọng tâm phương tiện khi nhìn từ góc xiên camera giao thông
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                curr_pt = (center_x, center_y)

                cls_info = TARGET_CLASSES.get(cls_id, {"name": "vehicle", "label_vi": "Xe", "color": (255, 255, 255)})
                label_vi = cls_info["label_vi"]
                box_color = cls_info["color"]

                # Khởi tạo bản ghi track nếu là phương tiện mới xuất hiện
                if track_id not in self.tracks:
                    self.tracks[track_id] = {
                        "cls_id": cls_id,
                        "label_vi": label_vi,
                        "class_name": cls_info["name"],
                        "color": box_color,
                        "first_seen_frame": frame_idx,
                        "first_seen_y": center_y,
                        "entry_frame": frame_idx if center_y >= self.y_count else None,
                        "history": deque(maxlen=self.history_len),
                        "prev_y": center_y,
                        "speed_kmh": 0.0,
                        "speed_locked": False,
                        "counted": False,
                        "direction": "Xuôi dòng",
                        "violation_saved": False,
                        "last_seen": frame_idx
                    }

                track = self.tracks[track_id]
                track["last_seen"] = frame_idx
                prev_y = track["prev_y"]
                track["history"].append((curr_pt, frame_idx))
                track["prev_y"] = center_y

                # ==============================================================
                # 1. VẠCH 1 (TRƯỚC): ĐẾM XE NGAY LẬP TỨC & BẮT ĐẦU TÍNH GIỜ
                # ==============================================================
                # Điều kiện: Tâm phương tiện đi từ phía trên (prev_y < y_count)
                # xuống phía dưới (center_y >= y_count) theo chiều xuôi dòng.
                if not track["counted"] and prev_y < self.y_count and center_y >= self.y_count:
                    track["counted"] = True
                    track["entry_frame"] = frame_idx
                    self.counted_ids.add(track_id)
                    self.total_counted += 1
                    if label_vi in self.class_counts:
                        self.class_counts[label_vi] += 1

                    # Ghi nhận lần đầu vào CSDL (Idempotent: chỉ thêm 1 bản ghi duy nhất)
                    if self.db:
                        self.db.log_vehicle_entry(
                            session_id=self.session_id,
                            track_id=track_id,
                            class_name=cls_info["name"],
                            label_vi=label_vi,
                            direction=track["direction"]
                        )

                # ==============================================================
                # 2. VẠCH 2 (SAU): CHỐT VẬN TỐC & PHÁT HIỆN VI PHẠM
                # ==============================================================
                # Điều kiện: Xe đã được đếm và tâm phương tiện vượt qua Vạch 2
                if not track["speed_locked"] and prev_y < self.y_speed and center_y >= self.y_speed:
                    f_start = track["entry_frame"] if track["entry_frame"] is not None else track["first_seen_frame"]
                    delta_f = frame_idx - f_start
                    delta_t = delta_f / fps if fps > 0 else 0.0
                    
                    if delta_t >= 0.15:
                        # Vận tốc vật lý thực tế: v = (Khoảng cách mét / Thời gian giây) * 3.6
                        speed_val = (self.distance_meters / delta_t) * 3.6
                        # Giới hạn vật lý đô thị hợp lý [5.0 km/h, 90.0 km/h] để loại trừ nhiễu nhảy tọa độ
                        track["speed_kmh"] = round(float(np.clip(speed_val, 5.0, 90.0)), 1)
                        track["speed_locked"] = True
                        self.speed_locked_ids.add(track_id)
                    else:
                        # Xử lý ngoại lệ: nếu xe xuất hiện ngay sát Vạch 2, ước lượng tốc độ an toàn
                        default_speeds = {"Xe máy": 28.0, "Ô tô": 22.0, "Xe tải": 20.0, "Xe buýt": 18.0}
                        track["speed_kmh"] = default_speeds.get(label_vi, 20.0)
                        track["speed_locked"] = True
                        self.speed_locked_ids.add(track_id)

                    # Kiểm tra vi phạm quá tốc độ quy định
                    is_speeding = track["speed_kmh"] > self.speed_limit

                    # Chụp và lưu ảnh bằng chứng vi phạm
                    snapshot_path = None
                    if is_speeding and not track["violation_saved"]:
                        snapshot_path = self._save_violation_snapshot(frame, box, track_id, track["speed_kmh"], label_vi)
                        if snapshot_path:
                            track["violation_saved"] = True
                            self.violations_count += 1

                    # Cập nhật tốc độ chốt và trạng thái vi phạm vào CSDL
                    if self.db:
                        self.db.update_vehicle_speed(
                            session_id=self.session_id,
                            track_id=track_id,
                            speed_kmh=track["speed_kmh"],
                            is_speeding=is_speeding,
                            snapshot_path=snapshot_path
                        )

                # Ước lượng vận tốc hiển thị khi xe đang nằm giữa 2 vạch
                if not track["speed_locked"] and track["counted"]:
                    f_in = track["entry_frame"]
                    if f_in is not None:
                        dt_in = (frame_idx - f_in) / fps if fps > 0 else 0.0
                        dy_in = center_y - self.y_count
                        zone_px = max(1, self.y_speed - self.y_count)
                        if dt_in >= 0.15 and dy_in > 10:
                            m_in = (dy_in / zone_px) * self.distance_meters
                            track["speed_kmh"] = round(float(np.clip((m_in / dt_in) * 3.6, 5.0, 80.0)), 1)

                current_speed = track["speed_kmh"]
                is_speeding = current_speed > self.speed_limit

                # 3. Vẽ Bounding Box & Quỹ đạo di chuyển
                box_draw_color = (0, 0, 255) if is_speeding else box_color
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_draw_color, 2)

                # Vẽ vệt đuôi quỹ đạo (Trail)
                pts = [p[0] for p in track["history"]]
                for i in range(1, len(pts)):
                    cv2.line(annotated_frame, pts[i - 1], pts[i], box_draw_color, 2)

                # Nhãn hiển thị thông tin phương tiện
                if track["speed_locked"]:
                    speed_str = f"{current_speed} km/h [Chot]"
                elif track["counted"] and current_speed > 0:
                    speed_str = f"~{current_speed} km/h (Dang do)"
                elif track["counted"]:
                    speed_str = "Da dem | Dang do..."
                else:
                    speed_str = "--- km/h"
                    
                tag_text = f"#{track_id} {label_vi} | {speed_str}"
                
                (t_w, t_h), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - 20)), (x1 + t_w + 6, max(20, y1)), box_draw_color, -1)
                cv2.putText(annotated_frame, tag_text, (x1 + 3, max(15, y1 - 4)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Giải phóng các track không còn xuất hiện trong số frame quy định
        stale_ids = [tid for tid, t in self.tracks.items() if frame_idx - t["last_seen"] > self.stale_timeout]
        for tid in stale_ids:
            del self.tracks[tid]

        # 4. Vẽ HUD thống kê lên góc trái khung hình
        self._draw_hud(annotated_frame)
        return annotated_frame

    def _draw_lines_and_zone(self, frame: np.ndarray, w: int, h: int) -> None:
        """
        Vẽ trực quan:
        - Vùng đo bán trong suốt giữa hai vạch mốc.
        - Vạch 1 (Màu Vàng): Vạch Đếm Xe & Bắt Đầu Đo Tốc Độ.
        - Vạch 2 (Màu Xanh Lơ): Vạch Chốt Vận Tốc.
        """
        # Vùng đo bán trong suốt
        zone_overlay = frame.copy()
        cv2.rectangle(zone_overlay, (0, self.y_count), (w, self.y_speed), (0, 120, 180), -1)
        cv2.addWeighted(zone_overlay, 0.22, frame, 0.78, 0, frame)

        # Vạch 1: Đếm xe & Bắt đầu tính tốc độ (Vàng Rực)
        cv2.line(frame, (0, self.y_count), (w, self.y_count), (0, 255, 255), 3)
        cv2.putText(frame, "VACH 1 [TRUOC] - DEM PHUONG TIEN (BAT DAU DO TOC DO)", (10, self.y_count - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 2, cv2.LINE_AA)

        # Vạch 2: Chốt tốc độ & Bắt vi phạm (Xanh Lơ)
        cv2.line(frame, (0, self.y_speed), (w, self.y_speed), (255, 255, 0), 2)
        cv2.putText(frame, f"VACH 2 [SAU] - CHOT VAN TOC [{self.distance_meters}m]", (10, self.y_speed - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 0), 2, cv2.LINE_AA)

    def _save_violation_snapshot(
        self,
        frame: np.ndarray,
        box: np.ndarray,
        track_id: int,
        speed: float,
        label_vi: str
    ) -> Optional[str]:
        """
        Chụp ảnh phương tiện vi phạm quá tốc độ và lưu vào thư mục snapshots/:
        - Vẽ khung chữ nhật đỏ làm nổi bật xe vi phạm.
        - Ghi thông số vi phạm, biển thông tin và thời gian.
        - Xử lý lỗi an toàn nếu không ghi được file.
        """
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"violation_id{track_id}_{timestamp}_{int(speed)}kmh.jpg"
            filepath = os.path.join(self.snapshot_dir, filename)
            
            snapshot_img = frame.copy()
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(snapshot_img, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(snapshot_img, f"VI PHAM TOC DO: {speed} km/h (Gioi han: {self.speed_limit} km/h)", 
                        (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            cv2.putText(snapshot_img, f"Loai: {label_vi} | ID: #{track_id} | Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                        (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            
            success = cv2.imwrite(filepath, snapshot_img)
            return filepath if success else None
        except Exception as e:
            print(f"[Tracker Error] Không thể lưu ảnh bằng chứng vi phạm: {e}")
            return None

    def _draw_hud(self, frame: np.ndarray) -> None:
        """Vẽ bảng thông tin giám sát HUD trực quan ở góc trên bên trái."""
        hud_w, hud_h = 320, 160
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (10 + hud_w, 10 + hud_h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        cv2.rectangle(frame, (10, 10), (10 + hud_w, 10 + hud_h), (0, 255, 255), 1)

        cv2.putText(frame, "ITS SURVEILLANCE - LINE 1 COUNTING", (20, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        cv2.putText(frame, f"Tong so xe da dem: {self.total_counted}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
        
        counts_str = f"Xe may: {self.class_counts.get('Xe máy', 0)} | O to: {self.class_counts.get('Ô tô', 0)}"
        cv2.putText(frame, counts_str, (20, 88),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 0), 1)
        
        counts_str2 = f"Xe tai: {self.class_counts.get('Xe tải', 0)} | Xe buyt: {self.class_counts.get('Xe buýt', 0)}"
        cv2.putText(frame, counts_str2, (20, 112),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 200, 255), 1)

        violation_color = (0, 0, 255) if self.violations_count > 0 else (200, 200, 200)
        cv2.putText(frame, f"Vi pham qua toc do (>{self.speed_limit}km/h): {self.violations_count}", (20, 142),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, violation_color, 2)
