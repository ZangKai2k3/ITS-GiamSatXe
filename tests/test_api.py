import pytest
from fastapi.testclient import TestClient
from its_dashboard.server import app, state

@pytest.fixture
def client():
    """Khởi tạo TestClient cho ứng dụng FastAPI."""
    with TestClient(app) as test_client:
        yield test_client

class TestDashboardAPI:
    """Kiểm thử tính đúng đắn và bảo mật của toàn bộ REST API."""

    def test_get_root_html(self, client):
        """Kiểm tra trang chủ Dashboard trả về mã trạng thái 200 và giao diện HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "ITS TRAFFIC MONITORING SYSTEM" in response.text

    def test_get_stats_endpoint(self, client):
        """Kiểm tra API /api/stats trả về đầy đủ các trường KPI theo định dạng JSON."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        
        expected_keys = [
            "total", "motorcycles", "cars", "buses", "trucks",
            "avg_speed", "violations", "current_fps", "speed_limit",
            "y_count_ratio", "y_speed_ratio", "session_id"
        ]
        for key in expected_keys:
            assert key in data, f"Thiếu trường dữ liệu {key} trong /api/stats"

    def test_get_violations_endpoint(self, client):
        """Kiểm tra API /api/violations trả về danh sách các trường hợp vi phạm."""
        response = client.get("/api/violations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_history_endpoint(self, client):
        """Kiểm tra API /api/history trả về danh sách nhật ký phương tiện."""
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_settings_valid_payload(self, client):
        """Kiểm tra cập nhật cấu hình với dữ liệu hợp lệ."""
        payload = {
            "speed_limit": 60.0,
            "y_count_ratio": 0.30,
            "y_speed_ratio": 0.45
        }
        response = client.post("/api/settings", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["speed_limit"] == 60.0
        assert data["y_count_ratio"] == 0.30
        assert data["y_speed_ratio"] == 0.45

    def test_update_settings_invalid_line_order(self, client):
        """Vạch 2 nằm trước hoặc quá sát Vạch 1 phải bị từ chối với mã 422."""
        payload = {
            "speed_limit": 50.0,
            "y_count_ratio": 0.50,
            "y_speed_ratio": 0.40  # Không hợp lệ: vạch 2 nhỏ hơn vạch 1
        }
        response = client.post("/api/settings", json=payload)
        assert response.status_code == 422

    def test_update_settings_invalid_speed(self, client):
        """Vận tốc giới hạn không hợp lý (ví dụ: < 10 km/h) phải bị từ chối với mã 422."""
        payload = {
            "speed_limit": 5.0,  # Nhỏ hơn ngưỡng tối thiểu 10 km/h
            "y_count_ratio": 0.30,
            "y_speed_ratio": 0.50
        }
        response = client.post("/api/settings", json=payload)
        assert response.status_code == 422

    def test_reset_data_endpoint(self, client):
        """Kiểm tra gọi /api/reset làm sạch dữ liệu thành công."""
        response = client.post("/api/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data

    def test_export_csv_endpoint(self, client):
        """Kiểm tra xuất báo cáo CSV có tiêu đề hợp lệ và định dạng text/csv."""
        response = client.get("/api/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "Content-Disposition" in response.headers
        assert "its_traffic_report.csv" in response.headers["Content-Disposition"]

