import argparse
import sys
import os

# Cấu hình in ký tự tiếng Việt chuẩn UTF-8 trên console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Đảm bảo đường dẫn gốc của dự án luôn nằm trong sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from its_core.pipeline import ITSPipeline
from its_core.config import DEFAULT_VIDEO_PATH, MODEL_PATH, OUTPUT_VIDEO_PATH, SPEED_LIMIT_KMH, validate_config

def main():
    """
    Điểm khởi chạy chương trình xử lý video ngoại tuyến (CLI Pipeline):
    - Đọc tham số dòng lệnh.
    - Kiểm tra cấu hình và tài nguyên.
    - Khởi tạo và thực thi ITSPipeline.
    """
    parser = argparse.ArgumentParser(
        description="Hệ thống ITS Nâng Cấp - Giám Sát, Đếm Xe và Đo Vận Tốc Phương Tiện Giao Thông"
    )
    parser.add_argument("--video", type=str, default=DEFAULT_VIDEO_PATH, help="Đường dẫn tệp video hoặc luồng camera RTSP")
    parser.add_argument("--model", type=str, default=MODEL_PATH, help="Đường dẫn tệp trọng số YOLO11")
    parser.add_argument("--output", type=str, default=OUTPUT_VIDEO_PATH, help="Đường dẫn tệp video kết quả (None để tắt ghi)")
    parser.add_argument("--speed-limit", type=float, default=SPEED_LIMIT_KMH, help="Ngưỡng tốc độ cảnh báo vi phạm (km/h)")
    parser.add_argument("--max-frames", type=int, default=None, help="Số khung hình tối đa cần xử lý (None = toàn bộ video)")
    parser.add_argument("--no-display", action="store_true", help="Chạy chế độ nền headless, không mở cửa sổ cv2.imshow")
    args = parser.parse_args()

    # Kiểm tra tính hợp lệ của cấu hình
    is_valid, msg = validate_config()
    if not is_valid:
        print(f"[CẢNH BÁO CẤU HÌNH] {msg}")

    print("=" * 65)
    print("   HỆ THỐNG ITS - SINGLE-PASS YOLO11 + BOT-SORT SPEED TRAP")
    print("=" * 65)
    print(f"Video nguồn: {args.video}")
    print(f"Mô hình YOLO: {args.model}")
    print(f"Giới hạn tốc độ: {args.speed_limit} km/h")
    print(f"Video đầu ra: {args.output if args.output else 'Không ghi'}")
    print(f"Chế độ hiển thị: {'Chạy nền (Headless)' if args.no_display else 'Mở cửa sổ màn hình'}")
    print("=" * 65)

    pipeline = ITSPipeline(
        video_source=args.video,
        model_path=args.model,
        speed_limit=args.speed_limit
    )

    out_file = None if args.output and args.output.lower() == "none" else args.output

    pipeline.run_offline(
        output_path=out_file,
        display=not args.no_display,
        max_frames=args.max_frames
    )

if __name__ == "__main__":
    main()
