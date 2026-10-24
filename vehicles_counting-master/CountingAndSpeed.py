import cv2
from ultralytics import solutions
import time

# Mở video
cap = cv2.VideoCapture("NgaTuGa.mp4")
assert cap.isOpened(), "Error reading video file"

# Lấy thông tin video
w, h, fps = (int(cap.get(x)) for x in (
    cv2.CAP_PROP_FRAME_WIDTH, 
    cv2.CAP_PROP_FRAME_HEIGHT, 
    cv2.CAP_PROP_FPS
))

# Tạo video đầu ra
video_writer = cv2.VideoWriter(
    "Output.mp4", 
    cv2.VideoWriter_fourcc(*"mp4v"), 
    fps,
    (w, h)
)

# Khởi tạo ObjectCounter
counter = solutions.ObjectCounter(
    show=False,  
    region=[(0, int(h / 2)), (w, int(h / 2))],
    model="yolo11n.pt",
    classes=[2, 3, 5, 7]
)

# Khởi tạo SpeedEstimator
speedestimator = solutions.SpeedEstimator(
    region=[(0, int(h / 2)), (w, int(h / 2))],
    model="yolo11n.pt",
    show=False,
)

start_time = time.time()
frame_count = 0

# Xử lý từng khung hình
while cap.isOpened():
    success, im0 = cap.read()
    if not success:
        print("Video frame is empty or processing is complete.")
        break

    # Đếm đối tượng
    count_results = counter(im0)

    # Ước lượng tốc độ
    speed_results = speedestimator(count_results.plot_im)

    # Ghi video đầu ra
    video_writer.write(speed_results.plot_im)

    # Hiển thị video ra màn hình
    cv2.imshow('Processed Video', speed_results.plot_im)

    # Ấn phím 'q' để dừng
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_count += 1 
    
# Ghi lại thời gian kết thúc
end_time = time.time()

# Tính thời gian chạy
elapsed_time = end_time - start_time

# In thông tin thời gian và số khung hình
print(f"Total processing time: {elapsed_time:.2f} seconds")
print(f"Total frames processed: {frame_count}")
print(f"Average FPS: {frame_count / elapsed_time:.2f}")

# Giải phóng tài nguyên
cap.release()
video_writer.release()
cv2.destroyAllWindows()
