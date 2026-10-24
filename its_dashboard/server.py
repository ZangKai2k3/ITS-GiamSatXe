import os
import cv2
import time
import io
import csv
import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, Request, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from its_core.config import (
    DEFAULT_VIDEO_PATH, MODEL_PATH, DATABASE_PATH, SNAPSHOT_DIR,
    SPEED_LIMIT_KMH, SPEED_ZONE_CONFIG
)
from its_core.database import ITSDatabase
from its_core.tracker import ITSTracker

class GlobalState:
    """
    Quản lý trạng thái toàn cục của phiên ứng dụng web:
    - Nguồn video đầu vào (tệp MP4 hoặc camera RTSP).
    - Cấu hình vùng đo và ngưỡng tốc độ.
    - Thể hiện ITSTracker và ITSDatabase.
    - Biến đo FPS và mã phiên làm việc (session_id).
    """
    def __init__(self):
        self.video_source = DEFAULT_VIDEO_PATH
        self.model_path = MODEL_PATH
        self.speed_limit = float(SPEED_LIMIT_KMH)
        self.y_count_ratio = float(SPEED_ZONE_CONFIG.get("y_count_ratio", 0.33))
        self.y_speed_ratio = float(SPEED_ZONE_CONFIG.get("y_speed_ratio", 0.47))
        self.db = ITSDatabase(DATABASE_PATH)
        self.tracker: Optional[ITSTracker] = None
        self.is_running = True
        self.current_fps = 0.0
        self.session_id = f"web_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def init_engine(self):
        """Khởi tạo engine nhận diện và theo dõi YOLO11 + BoT-SORT."""
        self.tracker = ITSTracker(
            model_path=self.model_path,
            db=self.db,
            speed_limit=self.speed_limit,
            session_id=self.session_id
        )

state = GlobalState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng FastAPI: Khởi tạo engine khi startup."""
    state.init_engine()
    yield

app = FastAPI(
    title="Hệ Thống ITS Giám Sát Giao Thông",
    description="Giao diện Web Giám Sát, Đo Tốc Độ và Phát Hiện Vi Phạm Giao Thông Thời Gian Thực",
    version="2.0.0",
    lifespan=lifespan
)

# Đảm bảo thư mục snapshots tồn tại và mount phục vụ xem ảnh bằng chứng tĩnh
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=SNAPSHOT_DIR), name="snapshots")

class SettingsPayload(BaseModel):
    """Mô hình dữ liệu xác thực cấu hình truyền từ Dashboard."""
    speed_limit: float = Field(..., ge=10.0, le=150.0, description="Giới hạn tốc độ cho phép (10 - 150 km/h)")
    y_count_ratio: float = Field(..., ge=0.10, le=0.80, description="Tỷ lệ vị trí Vạch 1 trên chiều cao ảnh")
    y_speed_ratio: float = Field(..., ge=0.20, le=0.95, description="Tỷ lệ vị trí Vạch 2 trên chiều cao ảnh")

    @model_validator(mode='after')
    def validate_lines(self):
        if self.y_speed_ratio <= self.y_count_ratio + 0.05:
            raise ValueError("Vạch 2 (y_speed_ratio) phải nằm ở phía sau Vạch 1 ít nhất 5% chiều cao khung hình.")
        return self

def generate_video_stream():
    """
    Tạo luồng video MJPEG truyền trực tiếp đến trình duyệt:
    - Đọc từng khung hình từ nguồn video.
    - Truyền qua ITSTracker để nhận diện, theo dõi, đếm xe và đo vận tốc.
    - Encode khung hình sang định dạng JPEG chất lượng cao.
    - Lặp lại video liên tục khi xem hết luồng.
    """
    cap = cv2.VideoCapture(state.video_source)
    frame_idx = 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    try:
        while state.is_running:
            ret, frame = cap.read()
            if not ret or frame is None:
                # Tua lại đầu video để duy trì luồng giả lập camera trực tiếp
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                continue

            frame_idx += 1
            h, w = frame.shape[:2]
            
            # Cập nhật vị trí vùng đo theo tỷ lệ động do người dùng cấu hình
            y_count = int(h * state.y_count_ratio)
            y_speed = int(h * state.y_speed_ratio)
            if state.tracker:
                state.tracker.set_zone_positions(y_count, y_speed)
                state.tracker.speed_limit = state.speed_limit
                state.tracker.session_id = state.session_id

            t_start = time.time()
            if state.tracker:
                annotated = state.tracker.process_frame(frame, frame_idx=frame_idx, fps=fps)
            else:
                annotated = frame

            t_cost = time.time() - t_start
            state.current_fps = round(1.0 / max(0.001, t_cost), 1)

            # Nén ảnh sang JPEG với chất lượng 75% để truyền tải mượt mà qua mạng
            ret_encode, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if not ret_encode:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Điều tiết tốc độ phát khung hình
            sleep_time = max(0.005, (1.0 / fps) - t_cost)
            time.sleep(sleep_time)

    finally:
        cap.release()

@app.get("/video_feed")
def video_feed():
    """Endpoint cung cấp luồng phát video MJPEG cho thẻ <img> trên giao diện."""
    return StreamingResponse(
        generate_video_stream(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/stats")
def get_stats():
    """
    Endpoint trả về các chỉ số KPI thống kê lưu lượng và trạng thái:
    - Tổng số xe, phân loại chi tiết (xe máy, ô tô, tải, buýt).
    - Vận tốc trung bình thực tế và số vi phạm quá tốc độ.
    - FPS xử lý hiện tại và cấu hình vạch đo.
    """
    stats = state.db.get_summary_stats(session_id=state.session_id)
    stats["current_fps"] = state.current_fps
    stats["speed_limit"] = state.speed_limit
    stats["y_count_ratio"] = state.y_count_ratio
    stats["y_speed_ratio"] = state.y_speed_ratio
    stats["session_id"] = state.session_id
    return JSONResponse(stats)

@app.get("/api/violations")
def get_violations():
    """
    Endpoint trả về danh sách 12 trường hợp vi phạm quá tốc độ gần nhất kèm đường dẫn ảnh.
    Đường dẫn ảnh được chuẩn hóa chỉ lấy tên tệp (basename) để ngăn ngừa lỗ hổng Path Traversal.
    """
    violations = state.db.get_recent_violations(limit=12, session_id=state.session_id)
    for v in violations:
        if v.get("snapshot_path"):
            safe_basename = os.path.basename(v["snapshot_path"])
            v["snapshot_url"] = f"/snapshots/{safe_basename}"
        else:
            v["snapshot_url"] = None
    return JSONResponse(violations)

@app.get("/api/history")
def get_history():
    """Endpoint trả về danh sách 50 phương tiện qua trạm gần nhất."""
    records = state.db.get_all_records(limit=50, session_id=state.session_id)
    return JSONResponse(records)

@app.post("/api/settings")
def update_settings(payload: SettingsPayload):
    """
    Endpoint cập nhật cấu hình hệ thống thời gian thực từ Dashboard:
    - Giới hạn tốc độ (km/h)
    - Tỷ lệ vị trí Vạch 1 và Vạch 2
    """
    state.speed_limit = float(payload.speed_limit)
    state.y_count_ratio = float(payload.y_count_ratio)
    state.y_speed_ratio = float(payload.y_speed_ratio)
    if state.tracker:
        state.tracker.speed_limit = state.speed_limit
    return JSONResponse({
        "status": "success", 
        "speed_limit": state.speed_limit, 
        "y_count_ratio": state.y_count_ratio,
        "y_speed_ratio": state.y_speed_ratio
    })

@app.post("/api/reset")
def reset_data():
    """
    Endpoint đặt lại số liệu thống kê:
    - Làm sạch số liệu trong CSDL của phiên hiện tại.
    - Đặt lại bộ đếm trong ITSTracker.
    - Tạo mã phiên mới để bắt đầu chu kỳ giám sát mới.
    """
    state.db.clear_all(session_id=state.session_id)
    if state.tracker:
        state.tracker.reset_stats()
    # Tạo mã phiên mới
    state.session_id = f"web_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if state.tracker:
        state.tracker.set_session_id(state.session_id)
    return JSONResponse({"status": "success", "session_id": state.session_id})

@app.get("/api/export")
def export_csv():
    """
    Endpoint xuất báo cáo lưu lượng phương tiện ra tệp tin CSV:
    Bao gồm ID, loại phương tiện, vận tốc, trạng thái vi phạm và thời gian ghi nhận.
    """
    records = state.db.get_all_records(limit=10000, session_id=state.session_id)
    output = io.StringIO()
    # Thêm BOM UTF-8 để Microsoft Excel hiển thị đúng tiếng Việt có dấu
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "STT", "Track ID", "Loại Phương Tiện", "Vận Tốc (km/h)",
        "Vi Phạm Quá Tốc Độ", "Hướng Di Chuyển", "Trạng Thái", "Thời Gian Ghi Nhận"
    ])
    for idx, r in enumerate(records, 1):
        writer.writerow([
            idx,
            r.get("track_id", ""),
            r.get("label_vi", ""),
            r.get("speed_kmh", 0.0),
            "CÓ VI PHẠM" if r.get("is_speeding") else "BÌNH THƯỜNG",
            r.get("direction", "Xuôi dòng"),
            r.get("status", "speed_locked"),
            r.get("timestamp", "")
        ])
    output.seek(0)
    return Response(
        content=output.getvalue().encode('utf-8-sig'),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=its_traffic_report.csv"}
    )

@app.get("/", response_class=HTMLResponse)
@app.head("/", response_class=HTMLResponse)
def index():
    """Cung cấp trang giao diện giám sát web chính."""
    html_file = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>ITS Dashboard loading...</h1>"
