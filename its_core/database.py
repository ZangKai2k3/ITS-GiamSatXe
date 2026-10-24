import sqlite3
import datetime
import os
import uuid
from typing import Optional, List, Dict, Any

class ITSDatabase:
    """
    Module quản lý cơ sở dữ liệu SQLite cho hệ thống giám sát giao thông ITS.
    
    Trách nhiệm:
    - Khởi tạo bảng dữ liệu và thiết lập chỉ mục (Index) phục vụ truy vấn thời gian thực.
    - Lưu nhật ký phương tiện qua trạm (Line 1: đếm xe; Line 2: chốt tốc độ và phát hiện vi phạm).
    - Bảo đảm tính toàn vẹn (Idempotency): mỗi track_id trong một phiên chạy (session_id)
      chỉ có duy nhất một bản ghi tổng hợp, không bị trùng lặp khi phương tiện qua nhiều vạch.
    - Cung cấp số liệu thống kê KPI lưu lượng, phân loại xe, vận tốc trung bình và vi phạm.
    - Hỗ trợ xuất dữ liệu ra file báo cáo CSV/Excel.
    """

    def __init__(self, db_path: str = "its_database.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Khởi tạo kết nối SQLite với cấu hình:
        - timeout=15.0: Chờ tối đa 15 giây nếu database bị khóa bởi tiến trình khác.
        - row_factory: Cho phép truy xuất cột theo tên dict-like.
        - WAL (Write-Ahead Logging): Tối ưu hóa đọc/ghi đồng thời giữa pipeline và web dashboard.
        """
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        # Bật chế độ WAL để pipeline ghi liên tục không làm nghẽn dashboard đọc
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """
        Khởi tạo lược đồ cơ sở dữ liệu và chỉ mục tra cứu tốc độ cao.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Bảng nhật ký phương tiện qua trạm
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicle_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default_session',
                    track_id INTEGER NOT NULL,
                    class_name TEXT NOT NULL,
                    label_vi TEXT NOT NULL,
                    entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    exit_time DATETIME,
                    speed_kmh REAL,
                    is_speeding INTEGER DEFAULT 0,
                    direction TEXT DEFAULT 'Xuoi dong',
                    status TEXT DEFAULT 'counted',
                    crossed_line INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    snapshot_path TEXT,
                    CONSTRAINT uq_session_track UNIQUE (session_id, track_id)
                )
            ''')

            # 2. Bảng tổng hợp lưu lượng theo chuỗi thời gian (time-series)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default_session',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_count INTEGER DEFAULT 0,
                    motorcycles INTEGER DEFAULT 0,
                    cars INTEGER DEFAULT 0,
                    buses INTEGER DEFAULT 0,
                    trucks INTEGER DEFAULT 0,
                    avg_speed REAL DEFAULT 0.0,
                    violations INTEGER DEFAULT 0
                )
            ''')

            # Tự động di chuyển lược đồ (Automatic Schema Migration) cho các CSDL đã tồn tại
            cursor.execute("PRAGMA table_info(vehicle_logs);")
            columns = [col["name"] for col in cursor.fetchall()]
            if "session_id" not in columns:
                cursor.execute("ALTER TABLE vehicle_logs ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default_session';")
            if "entry_time" not in columns:
                cursor.execute("ALTER TABLE vehicle_logs ADD COLUMN entry_time DATETIME;")
            if "exit_time" not in columns:
                cursor.execute("ALTER TABLE vehicle_logs ADD COLUMN exit_time DATETIME;")
            if "status" not in columns:
                cursor.execute("ALTER TABLE vehicle_logs ADD COLUMN status TEXT DEFAULT 'counted';")

            cursor.execute("PRAGMA table_info(traffic_stats);")
            ts_columns = [col["name"] for col in cursor.fetchall()]
            if "session_id" not in ts_columns:
                cursor.execute("ALTER TABLE traffic_stats ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default_session';")

            # 3. Tạo chỉ mục tối ưu hóa tốc độ truy vấn và bảo đảm tính duy nhất
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_idx_session_track ON vehicle_logs(session_id, track_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_is_speeding ON vehicle_logs(is_speeding);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON vehicle_logs(timestamp);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_crossed ON vehicle_logs(crossed_line);')

            conn.commit()

    def log_vehicle_entry(
        self,
        session_id: str,
        track_id: int,
        class_name: str,
        label_vi: str,
        direction: str = "Xuôi dòng"
    ) -> bool:
        """
        Ghi nhận sự kiện phương tiện chạm Vạch 1 (Bắt đầu theo dõi và đếm xe).
        Nếu bản ghi đã tồn tại trong session này, thao tác sẽ được bỏ qua an toàn (Idempotent).
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO vehicle_logs (
                        session_id, track_id, class_name, label_vi, direction,
                        status, crossed_line, entry_time, timestamp
                    ) VALUES (?, ?, ?, ?, ?, 'counted', 1, ?, ?)
                ''', (
                    str(session_id), int(track_id), str(class_name), str(label_vi),
                    str(direction), now_str, now_str
                ))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            # Ghi log lỗi nhẹ để không làm gián đoạn pipeline xử lý video thời gian thực
            print(f"[DB Error] log_vehicle_entry thất bại cho track #{track_id}: {e}")
            return False

    def update_vehicle_speed(
        self,
        session_id: str,
        track_id: int,
        speed_kmh: float,
        is_speeding: bool = False,
        snapshot_path: Optional[str] = None
    ) -> bool:
        """
        Cập nhật vận tốc chốt tại Vạch 2 và trạng thái vi phạm quá tốc độ.
        Nếu phương tiện chưa có bản ghi ban đầu, hệ thống sẽ tự động chèn bản ghi mới với đầy đủ thông tin.
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Cập nhật bản ghi đã ghi nhận ở Vạch 1
                cursor.execute('''
                    UPDATE vehicle_logs
                    SET speed_kmh = ?,
                        is_speeding = ?,
                        exit_time = ?,
                        timestamp = ?,
                        snapshot_path = COALESCE(?, snapshot_path),
                        status = 'speed_locked'
                    WHERE session_id = ? AND track_id = ?
                ''', (
                    round(float(speed_kmh), 1),
                    1 if is_speeding else 0,
                    now_str,
                    now_str,
                    snapshot_path,
                    str(session_id),
                    int(track_id)
                ))

                # Nếu chưa có bản ghi (ví dụ xe xuất hiện ngay giữa 2 vạch), chèn bản ghi mới
                if cursor.rowcount == 0:
                    cursor.execute('''
                        INSERT OR REPLACE INTO vehicle_logs (
                            session_id, track_id, class_name, label_vi,
                            speed_kmh, is_speeding, direction, status, crossed_line,
                            entry_time, exit_time, timestamp, snapshot_path
                        ) VALUES (?, ?, 'vehicle', 'Xe', ?, ?, 'Xuôi dòng', 'speed_locked', 1, ?, ?, ?, ?)
                    ''', (
                        str(session_id), int(track_id), round(float(speed_kmh), 1),
                        1 if is_speeding else 0, now_str, now_str, now_str, snapshot_path
                    ))

                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"[DB Error] update_vehicle_speed thất bại cho track #{track_id}: {e}")
            return False

    def log_vehicle_event(
        self,
        track_id: int,
        class_name: str,
        label_vi: str,
        speed_kmh: float,
        is_speeding: bool = False,
        direction: str = "Xuôi dòng",
        crossed_line: bool = True,
        snapshot_path: Optional[str] = None,
        session_id: str = "default_session"
    ) -> None:
        """
        Phương thức tương thích ngược cho các lệnh gọi một bước cũ.
        Thực hiện lưu hoặc cập nhật bản ghi duy nhất cho cặp (session_id, track_id).
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_val = "speed_locked" if speed_kmh > 0 else "counted"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO vehicle_logs (
                        session_id, track_id, class_name, label_vi, speed_kmh,
                        is_speeding, direction, status, crossed_line, entry_time, timestamp, snapshot_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, track_id) DO UPDATE SET
                        speed_kmh = CASE WHEN excluded.speed_kmh > 0 THEN excluded.speed_kmh ELSE vehicle_logs.speed_kmh END,
                        is_speeding = CASE WHEN excluded.is_speeding = 1 THEN 1 ELSE vehicle_logs.is_speeding END,
                        snapshot_path = COALESCE(excluded.snapshot_path, vehicle_logs.snapshot_path),
                        status = CASE WHEN excluded.speed_kmh > 0 THEN 'speed_locked' ELSE vehicle_logs.status END,
                        timestamp = excluded.timestamp
                ''', (
                    str(session_id), int(track_id), str(class_name), str(label_vi),
                    round(float(speed_kmh), 1), 1 if is_speeding else 0,
                    str(direction), status_val, 1 if crossed_line else 0,
                    now_str, now_str, snapshot_path
                ))
                conn.commit()
        except sqlite3.Error as e:
            print(f"[DB Error] log_vehicle_event thất bại: {e}")

    def get_summary_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Tính toán các chỉ số KPI hiệu năng hệ thống:
        - Tổng số phương tiện độc lập đã đếm.
        - Số lượng từng loại phương tiện: Xe máy, Ô tô, Xe buýt, Xe tải.
        - Vận tốc trung bình thực tế của các xe đã hoàn thành chốt tốc độ (> 0 km/h).
        - Tổng số vụ vi phạm quá tốc độ quy định.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = "WHERE crossed_line = 1"
                params = []
                if session_id:
                    where_clause += " AND session_id = ?"
                    params.append(session_id)

                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total_logged,
                        SUM(CASE WHEN label_vi = 'Xe máy' THEN 1 ELSE 0 END) as motorcycles,
                        SUM(CASE WHEN label_vi = 'Ô tô' THEN 1 ELSE 0 END) as cars,
                        SUM(CASE WHEN label_vi = 'Xe buýt' THEN 1 ELSE 0 END) as buses,
                        SUM(CASE WHEN label_vi = 'Xe tải' THEN 1 ELSE 0 END) as trucks,
                        AVG(CASE WHEN speed_kmh > 0 THEN speed_kmh ELSE NULL END) as avg_speed,
                        SUM(CASE WHEN is_speeding = 1 THEN 1 ELSE 0 END) as violations
                    FROM vehicle_logs
                    {where_clause}
                ''', params)
                row = cursor.fetchone()
                if not row or row["total_logged"] is None:
                    return {
                        "total": 0, "motorcycles": 0, "cars": 0, "buses": 0,
                        "trucks": 0, "avg_speed": 0.0, "violations": 0
                    }
                return {
                    "total": int(row["total_logged"] or 0),
                    "motorcycles": int(row["motorcycles"] or 0),
                    "cars": int(row["cars"] or 0),
                    "buses": int(row["buses"] or 0),
                    "trucks": int(row["trucks"] or 0),
                    "avg_speed": round(float(row["avg_speed"] or 0.0), 1),
                    "violations": int(row["violations"] or 0)
                }
        except sqlite3.Error as e:
            print(f"[DB Error] get_summary_stats thất bại: {e}")
            return {
                "total": 0, "motorcycles": 0, "cars": 0, "buses": 0,
                "trucks": 0, "avg_speed": 0.0, "violations": 0
            }

    def get_recent_violations(self, limit: int = 10, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các bản ghi vi phạm tốc độ mới nhất để hiển thị bằng chứng trên Dashboard.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = "WHERE is_speeding = 1"
                params = []
                if session_id:
                    where_clause += " AND session_id = ?"
                    params.append(session_id)
                params.append(limit)

                cursor.execute(f'''
                    SELECT track_id, label_vi, speed_kmh, direction, timestamp, snapshot_path
                    FROM vehicle_logs
                    {where_clause}
                    ORDER BY id DESC
                    LIMIT ?
                ''', params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"[DB Error] get_recent_violations thất bại: {e}")
            return []

    def get_all_records(self, limit: int = 100, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lấy danh sách nhật ký phương tiện gần nhất phục vụ bảng theo dõi thời gian thực.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = ""
                params = []
                if session_id:
                    where_clause = "WHERE session_id = ?"
                    params.append(session_id)
                params.append(limit)

                cursor.execute(f'''
                    SELECT id, track_id, label_vi, speed_kmh, is_speeding, direction, status, timestamp
                    FROM vehicle_logs
                    {where_clause}
                    ORDER BY id DESC
                    LIMIT ?
                ''', params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"[DB Error] get_all_records thất bại: {e}")
            return []

    def clear_all(self, session_id: Optional[str] = None) -> None:
        """
        Xóa nhật ký (được gọi khi người dùng bấm Đặt lại trên Dashboard).
        Nếu session_id được truyền vào, chỉ xóa dữ liệu của session đó.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if session_id:
                    cursor.execute("DELETE FROM vehicle_logs WHERE session_id = ?", (session_id,))
                    cursor.execute("DELETE FROM traffic_stats WHERE session_id = ?", (session_id,))
                else:
                    cursor.execute("DELETE FROM vehicle_logs")
                    cursor.execute("DELETE FROM traffic_stats")
                conn.commit()
        except sqlite3.Error as e:
            print(f"[DB Error] clear_all thất bại: {e}")
