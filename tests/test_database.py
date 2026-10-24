import os
import pytest
from its_core.database import ITSDatabase

@pytest.fixture
def test_db(tmp_path):
    """Tạo cơ sở dữ liệu SQLite cô lập trong thư mục tạm phục vụ kiểm thử."""
    db_file = tmp_path / "test_traffic.db"
    db = ITSDatabase(str(db_file))
    return db

class TestDatabaseOperations:
    """Kiểm thử tính toàn vẹn, tính bất biến (Idempotency) và truy vấn CSDL."""

    def test_init_database_and_indices(self, test_db):
        """Xác minh bảng dữ liệu và các chỉ mục được tạo thành công."""
        with test_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row["name"] for row in cursor.fetchall()]
            assert "vehicle_logs" in tables
            assert "traffic_stats" in tables

            cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
            indices = [row["name"] for row in cursor.fetchall()]
            assert "uq_idx_session_track" in indices
            assert "idx_logs_is_speeding" in indices

    def test_log_vehicle_entry_idempotency(self, test_db):
        """Ghi nhận sự kiện Vạch 1: gọi nhiều lần cho cùng track_id không tạo bản ghi trùng lặp."""
        session_id = "test_sess_01"
        track_id = 101

        # Lần 1: Chèn mới thành công
        inserted = test_db.log_vehicle_entry(session_id, track_id, "motorcycle", "Xe máy")
        assert inserted is True

        # Lần 2: Cùng track_id và session_id -> Không tạo thêm dòng (rowcount = 0)
        inserted_again = test_db.log_vehicle_entry(session_id, track_id, "motorcycle", "Xe máy")
        assert inserted_again is False

        # Kiểm tra chỉ có duy nhất 1 dòng trong CSDL
        with test_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM vehicle_logs WHERE session_id = ? AND track_id = ?",
                           (session_id, track_id))
            assert cursor.fetchone()["cnt"] == 1

    def test_update_vehicle_speed(self, test_db):
        """Chốt tốc độ tại Vạch 2: cập nhật đúng dòng bản ghi đã có ở Vạch 1."""
        session_id = "test_sess_02"
        track_id = 202

        # Bước 1: Xe qua Vạch 1
        test_db.log_vehicle_entry(session_id, track_id, "car", "Ô tô")

        # Bước 2: Xe qua Vạch 2 với tốc độ 42.5 km/h (hợp lệ)
        success = test_db.update_vehicle_speed(session_id, track_id, 42.5, is_speeding=False)
        assert success is True

        records = test_db.get_all_records(session_id=session_id)
        assert len(records) == 1
        assert records[0]["track_id"] == 202
        assert records[0]["speed_kmh"] == 42.5
        assert records[0]["is_speeding"] == 0
        assert records[0]["status"] == "speed_locked"

    def test_summary_stats_calculation(self, test_db):
        """Kiểm tra độ chính xác của phép tính thống kê KPI (Tổng xe, phân loại, vận tốc TB, vi phạm)."""
        session_id = "test_sess_kpi"

        # Giả lập 3 xe:
        # Xe 1: Xe máy qua Vạch 1 & Vạch 2, 30.0 km/h (Hợp lệ)
        test_db.log_vehicle_entry(session_id, 1, "motorcycle", "Xe máy")
        test_db.update_vehicle_speed(session_id, 1, 30.0, is_speeding=False)

        # Xe 2: Xe máy chỉ qua Vạch 1 (rẽ hướng trước Vạch 2), chưa chốt tốc độ
        test_db.log_vehicle_entry(session_id, 2, "motorcycle", "Xe máy")

        # Xe 3: Ô tô qua Vạch 1 & Vạch 2, 60.0 km/h (Quá tốc độ vi phạm)
        test_db.log_vehicle_entry(session_id, 3, "car", "Ô tô")
        test_db.update_vehicle_speed(session_id, 3, 60.0, is_speeding=True, snapshot_path="snapshots/snap3.jpg")

        stats = test_db.get_summary_stats(session_id=session_id)

        # Tổng số xe đã qua Vạch 1 phải là 3
        assert stats["total"] == 3
        assert stats["motorcycles"] == 2
        assert stats["cars"] == 1
        assert stats["trucks"] == 0
        assert stats["buses"] == 0

        # Vận tốc trung bình chỉ tính cho xe đã chốt tốc độ (30.0 + 60.0) / 2 = 45.0 km/h
        assert stats["avg_speed"] == 45.0

        # Tổng số vụ vi phạm là 1
        assert stats["violations"] == 1

    def test_get_recent_violations(self, test_db):
        """Kiểm tra truy vấn danh sách vi phạm tốc độ."""
        session_id = "test_sess_violation"
        test_db.log_vehicle_entry(session_id, 10, "car", "Ô tô")
        test_db.update_vehicle_speed(session_id, 10, 58.0, is_speeding=True, snapshot_path="snapshots/v1.jpg")

        test_db.log_vehicle_entry(session_id, 11, "motorcycle", "Xe máy")
        test_db.update_vehicle_speed(session_id, 11, 35.0, is_speeding=False)

        violations = test_db.get_recent_violations(limit=5, session_id=session_id)
        assert len(violations) == 1
        assert violations[0]["track_id"] == 10
        assert violations[0]["speed_kmh"] == 58.0
        assert violations[0]["snapshot_path"] == "snapshots/v1.jpg"

    def test_clear_all_session_data(self, test_db):
        """Kiểm tra tính năng đặt lại số liệu (clear_all) theo session."""
        sess_a = "session_A"
        sess_b = "session_B"

        test_db.log_vehicle_entry(sess_a, 1, "car", "Ô tô")
        test_db.log_vehicle_entry(sess_b, 2, "motorcycle", "Xe máy")

        # Chỉ xóa session_A
        test_db.clear_all(session_id=sess_a)

        stats_a = test_db.get_summary_stats(session_id=sess_a)
        stats_b = test_db.get_summary_stats(session_id=sess_b)

        assert stats_a["total"] == 0
        assert stats_b["total"] == 1

