import uvicorn
import os
import sys
import argparse

# Cấu hình in ký tự tiếng Việt chuẩn UTF-8 trên console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from its_core.config import validate_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Khởi động Giao diện Web Giám sát ITS")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Địa chỉ IP host (mặc định: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Cổng dịch vụ (mặc định: 8000)")
    args = parser.parse_args()

    # Kiểm tra cấu hình trước khi chạy
    is_valid, msg = validate_config()
    if not is_valid:
        print(f"[CẢNH BÁO CẤU HÌNH] {msg}")

    print("=" * 65)
    print("   KHỞI ĐỘNG HỆ THỐNG ITS WEB DASHBOARD")
    print(f"   Địa chỉ truy cập: http://{args.host}:{args.port}")
    print("   Bấm Ctrl+C để dừng máy chủ")
    print("=" * 65)

    uvicorn.run("its_dashboard.server:app", host=args.host, port=args.port, reload=False)

    # Kiểm tra cấu hình trước khi chạy
    is_valid, msg = validate_config()
    if not is_valid:
        print(f"[CẢNH BÁO CẤU HÌNH] {msg}")

    print("=" * 65)
    print("   KHỞI ĐỘNG HỆ THỐNG ITS WEB DASHBOARD")
    print(f"   Địa chỉ truy cập: http://{args.host}:{args.port}")
    print("   Bấm Ctrl+C để dừng máy chủ")
    print("=" * 65)

    uvicorn.run("its_dashboard.server:app", host=args.host, port=args.port, reload=False)

