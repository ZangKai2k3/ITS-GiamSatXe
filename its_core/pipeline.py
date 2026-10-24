import cv2
import time
import os
import sys
import datetime
from typing import Optional, Dict, Any

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from its_core.config import (
    MODEL_PATH, DEFAULT_VIDEO_PATH, OUTPUT_VIDEO_PATH, DATABASE_PATH,
    SPEED_LIMIT_KMH, SPEED_ZONE_CONFIG
)
from its_core.database import ITSDatabase
from its_core.tracker import ITSTracker

class ITSPipeline:
    """
    Module điều phối xử lý video (Video Processing Pipeline):
    
    Trách nhiệm:
    - Mở và quản lý luồng video đầu vào (tập tin MP4 hoặc luồng camera IP / RTSP).
    - Tạo phiên làm việc (session_id) riêng biệt để dữ liệu không bị trùng lặp giữa các lần chạy.
    - Đọc từng khung hình và chuyển tiếp cho ITSTracker xử lý.
    - Đo đạc tốc độ xử lý (FPS thời gian thực và FPS trung bình).
    - Ghi video kết quả có chú thích ra tệp tin MP4 (H.264 / MP4V).
    - Hiển thị màn hình OpenCV và bắt phím 'q' để dừng an toàn.
    - Đảm bảo giải phóng tài nguyên (bộ nhớ, file video) trong khối finally.
    - Báo cáo số liệu tổng kết lưu lượng và vi phạm sau khi xử lý.
    """

    def __init__(
        self,
        video_source: str = DEFAULT_VIDEO_PATH,
        model_path: str = MODEL_PATH,
        speed_limit: float = SPEED_LIMIT_KMH,
        session_id: Optional[str] = None
    ):
        self.video_source = video_source
        self.model_path = model_path
        self.speed_limit = float(speed_limit)
        
        # Khởi tạo mã phiên làm việc duy nhất cho lần chạy này
        if session_id is None:
            now_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_id = f"cli_{now_tag}"
        else:
            self.session_id = str(session_id)

        # Kết nối cơ sở dữ liệu
        self.db = ITSDatabase(DATABASE_PATH)
        
        # Khởi tạo bộ theo dõi
        self.tracker: Optional[ITSTracker] = None
        self._init_tracker()

    def _init_tracker(self) -> None:
        """Khởi tạo ITSTracker với model và CSDL."""
        self.tracker = ITSTracker(
            model_path=self.model_path,
            db=self.db,
            speed_limit=self.speed_limit,
            session_id=self.session_id
        )

    def set_zone(self, y_count: int, y_speed: int) -> None:
        """Cập nhật tọa độ vùng đo."""
        if self.tracker:
            self.tracker.set_zone_positions(y_count, y_speed)

    def run_offline(
        self,
        output_path: Optional[str] = OUTPUT_VIDEO_PATH,
        display: bool = True,
        max_frames: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Thực thi xử lý toàn bộ video theo chế độ ngoại tuyến (Batch / Offline processing):
        - output_path: Đường dẫn lưu video kết quả đã vẽ bounding box và HUD (None = không ghi file).
        - display: Mở cửa sổ giao diện OpenCV cv2.imshow (True) hoặc chạy nền headless (False).
        - max_frames: Giới hạn số khung hình xử lý để thử nghiệm nhanh (None = xử lý hết video).
        """
        if not os.path.exists(self.video_source):
            raise FileNotFoundError(f"Không tìm thấy video nguồn tại: {self.video_source}")

        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            raise RuntimeError(f"Không thể mở nguồn video: {self.video_source}")

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        video_writer = None
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            video_writer = cv2.VideoWriter(
                output_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (w, h)
            )

        print(f"[*] Bắt đầu xử lý video: {self.video_source}")
        print(f"[*] Phiên làm việc (Session ID): {self.session_id}")
        print(f"[*] Độ phân giải: {w}x{h} | FPS nguồn: {fps:.2f} | Tổng số frames: {total_frames}")

        frame_idx = 0
        start_time = time.time()

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                frame_idx += 1
                if max_frames and frame_idx > max_frames:
                    break

                t_frame_start = time.time()
                
                # Xử lý khung hình qua ITSTracker (BoT-SORT Two-Line Speed Trap)
                annotated = self.tracker.process_frame(frame, frame_idx=frame_idx, fps=fps)
                
                t_frame_end = time.time()
                current_fps = 1.0 / max(0.001, (t_frame_end - t_frame_start))
                cv2.putText(annotated, f"FPS: {current_fps:.1f}", (w - 140, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Ghi video ra tệp nếu được cấu hình
                if video_writer:
                    video_writer.write(annotated)

                # Hiển thị trực tiếp lên màn hình nếu bật chế độ display
                if display:
                    cv2.imshow("ITS Vehicle Surveillance [Two-Line Speed Trap]", annotated)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("[!] Người dùng bấm 'q' để dừng sớm pipeline.")
                        break

                # In thông báo tiến độ xử lý mỗi 30 khung hình
                if frame_idx % 30 == 0 or frame_idx == total_frames:
                    elapsed = time.time() - start_time
                    avg_fps = frame_idx / max(0.001, elapsed)
                    pct = (frame_idx / total_frames * 100) if total_frames > 0 else 0
                    print(f"[-] Đã xử lý {frame_idx}/{total_frames} frames ({pct:.1f}%) | FPS TB: {avg_fps:.1f}")

        finally:
            # Giải phóng toàn bộ tài nguyên hệ thống một cách an toàn
            cap.release()
            if video_writer:
                video_writer.release()
            if display:
                cv2.destroyAllWindows()

        total_elapsed = time.time() - start_time
        avg_fps_final = frame_idx / max(0.001, total_elapsed)
        summary = self.db.get_summary_stats(session_id=self.session_id)

        print("\n" + "=" * 60)
        print("   KẾT QUẢ XỬ LÝ HỆ THỐNG ITS [TWO-LINE SPEED TRAP]")
        print("=" * 60)
        print(f"Mã phiên (Session ID): {self.session_id}")
        print(f"Tổng thời gian: {total_elapsed:.2f}s | Số khung hình: {frame_idx}")
        print(f"Tốc độ xử lý trung bình: {avg_fps_final:.2f} FPS")
        print(f"Tổng số xe đã qua Vạch 1: {summary['total']}")
        print(f"  - Xe máy: {summary['motorcycles']}")
        print(f"  - Ô tô: {summary['cars']}")
        print(f"  - Xe tải: {summary['trucks']}")
        print(f"  - Xe buýt: {summary['buses']}")
        print(f"Vận tốc trung bình thực tế: {summary['avg_speed']} km/h")
        print(f"Số vi phạm quá tốc độ (> {self.speed_limit} km/h): {summary['violations']}")
        if output_path:
            print(f"Video đầu ra đã lưu tại: {output_path}")
        print("=" * 60 + "\n")

        return summary
