"""
Database Abstraction Layer for CROX Python + MySQL Version.
Connects to MySQL with automatic fallback to SQLite if MySQL is unavailable.
Provides full CRUD operations for Projects, Floors, Rooms, and Furniture.
"""

import os
import uuid
import sqlite3
from .config import load_db_config

# Check for available MySQL driver modules
MYSQL_DRIVER = None
try:
    import mysql.connector
    MYSQL_DRIVER = 'mysql.connector'
except ImportError:
    try:
        import pymysql
        MYSQL_DRIVER = 'pymysql'
    except ImportError:
        MYSQL_DRIVER = None


class DatabaseManager:
    def __init__(self):
        self.config = load_db_config()
        self.backend = None  # 'mysql' or 'sqlite'
        self.conn = None
        self.status_message = "Initializing..."
        self.initialize_connection()

    def initialize_connection(self):
        """Attempts MySQL connection; falls back to SQLite if unavailable."""
        self.config = load_db_config()
        mysql_success = False

        if self.config.get('prefer_mysql', True) and MYSQL_DRIVER:
            try:
                if MYSQL_DRIVER == 'mysql.connector':
                    # First connect without database to ensure database exists
                    server_conn = mysql.connector.connect(
                        host=self.config.get('host', 'localhost'),
                        port=int(self.config.get('port', 3306)),
                        user=self.config.get('user', 'root'),
                        password=self.config.get('password', ''),
                        autocommit=True
                    )
                    cursor = server_conn.cursor()
                    db_name = self.config.get('database', 'crox_db')
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                    cursor.close()
                    server_conn.close()

                    # Now connect to the database
                    self.conn = mysql.connector.connect(
                        host=self.config.get('host', 'localhost'),
                        port=int(self.config.get('port', 3306)),
                        user=self.config.get('user', 'root'),
                        password=self.config.get('password', ''),
                        database=db_name,
                        autocommit=True
                    )
                elif MYSQL_DRIVER == 'pymysql':
                    server_conn = pymysql.connect(
                        host=self.config.get('host', 'localhost'),
                        port=int(self.config.get('port', 3306)),
                        user=self.config.get('user', 'root'),
                        password=self.config.get('password', ''),
                        autocommit=True
                    )
                    cursor = server_conn.cursor()
                    db_name = self.config.get('database', 'crox_db')
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                    cursor.close()
                    server_conn.close()

                    self.conn = pymysql.connect(
                        host=self.config.get('host', 'localhost'),
                        port=int(self.config.get('port', 3306)),
                        user=self.config.get('user', 'root'),
                        password=self.config.get('password', ''),
                        database=db_name,
                        autocommit=True
                    )

                self.backend = 'mysql'
                self.status_message = f"Connected to MySQL ({self.config['user']}@{self.config['host']}:{self.config['port']}/{self.config['database']})"
                mysql_success = True
            except Exception as e:
                self.status_message = f"MySQL unavailable ({e}). Using local SQLite database."
                mysql_success = False

        if not mysql_success:
            self.backend = 'sqlite'
            db_path = os.path.join(os.path.dirname(__file__), 'crox_offline.db')
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            if not self.status_message.startswith("MySQL unavailable"):
                self.status_message = f"Running in SQLite mode ({os.path.basename(db_path)})"

        self._create_tables()
        self._ensure_sample_data()

    def _create_tables(self):
        """Creates tables for projects, floors, rooms, and furniture."""
        cursor = self.conn.cursor()
        if self.backend == 'mysql':
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                budget DOUBLE NOT NULL DEFAULT 100000.0,
                unit VARCHAR(10) NOT NULL DEFAULT 'ft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS floors (
                floor_id VARCHAR(64) PRIMARY KEY,
                project_id VARCHAR(64) NOT NULL,
                name VARCHAR(100) NOT NULL,
                level INT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id VARCHAR(64) PRIMARY KEY,
                project_id VARCHAR(64) NOT NULL,
                floor_id VARCHAR(64) NOT NULL,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(50) NOT NULL,
                cost DOUBLE NOT NULL DEFAULT 0.0,
                width DOUBLE NOT NULL DEFAULT 220.0,
                height DOUBLE NOT NULL DEFAULT 180.0,
                area DOUBLE NOT NULL DEFAULT 99.0,
                flooring VARCHAR(50) DEFAULT 'Standard',
                wall_color VARCHAR(50) DEFAULT 'White',
                windows INT DEFAULT 0,
                x DOUBLE NOT NULL DEFAULT 20.0,
                y DOUBLE NOT NULL DEFAULT 20.0,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (floor_id) REFERENCES floors(floor_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS furniture (
                furniture_id VARCHAR(64) PRIMARY KEY,
                room_id VARCHAR(64) NOT NULL,
                name VARCHAR(100) NOT NULL,
                cost DOUBLE NOT NULL DEFAULT 0.0,
                position VARCHAR(50) DEFAULT 'Center',
                model VARCHAR(50) DEFAULT 'box',
                x DOUBLE NOT NULL DEFAULT 20.0,
                y DOUBLE NOT NULL DEFAULT 20.0,
                attached_to VARCHAR(50) DEFAULT 'floor',
                FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        else:
            # SQLite Table definitions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                budget REAL NOT NULL DEFAULT 100000.0,
                unit TEXT NOT NULL DEFAULT 'ft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS floors (
                floor_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                floor_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                cost REAL NOT NULL DEFAULT 0.0,
                width REAL NOT NULL DEFAULT 220.0,
                height REAL NOT NULL DEFAULT 180.0,
                area REAL NOT NULL DEFAULT 99.0,
                flooring TEXT DEFAULT 'Standard',
                wall_color TEXT DEFAULT 'White',
                windows INTEGER DEFAULT 0,
                x REAL NOT NULL DEFAULT 20.0,
                y REAL NOT NULL DEFAULT 20.0,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (floor_id) REFERENCES floors(floor_id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS furniture (
                furniture_id TEXT PRIMARY KEY,
                room_id TEXT NOT NULL,
                name TEXT NOT NULL,
                cost REAL NOT NULL DEFAULT 0.0,
                position TEXT DEFAULT 'Center',
                model TEXT DEFAULT 'box',
                x REAL NOT NULL DEFAULT 20.0,
                y REAL NOT NULL DEFAULT 20.0,
                attached_to TEXT DEFAULT 'floor',
                FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
            );
            """)
            self.conn.commit()
        cursor.close()

    def _query(self, sql, params=()):
        """Execute a query translating parameter placeholders (%s vs ?)."""
        cursor = self.conn.cursor()
        if self.backend == 'sqlite':
            # Translate %s placeholder to ? for SQLite
            sql = sql.replace('%s', '?')
        cursor.execute(sql, params)
        return cursor

    def _commit(self):
        if self.backend == 'sqlite':
            self.conn.commit()

    # -------------------------------------------------------------
    # Sample / Seed Data
    # -------------------------------------------------------------
    def _ensure_sample_data(self):
        """Ensures at least one sample project exists for immediate testing."""
        projects = self.get_all_projects()
        if not projects:
            p_id = self.create_project("Modern Villa Project", 120000.0, "ft")
            # Get default floors created
            floors = self.get_floors(p_id)
            ground_floor = next((f for f in floors if f['level'] == 0), floors[0])

            # Add starter rooms
            r1_id = self.add_room(
                project_id=p_id,
                floor_id=ground_floor['floor_id'],
                name="Living Room",
                room_type="Living Room",
                cost=12000.0,
                width=260.0,
                height=200.0,
                area=130.0,
                flooring="Hardwood Oak",
                wall_color="Warm Beige",
                windows=2,
                x=50.0,
                y=50.0
            )

            r2_id = self.add_room(
                project_id=p_id,
                floor_id=ground_floor['floor_id'],
                name="Kitchen & Dining",
                room_type="Kitchen",
                cost=9500.0,
                width=220.0,
                height=200.0,
                area=110.0,
                flooring="Ceramic Tile",
                wall_color="White",
                windows=1,
                x=310.0,
                y=50.0
            )

            # Add furniture
            self.add_furniture(r1_id, "Sectional Sofa", 1800.0, "Center", "sofa", 100.0, 80.0)
            self.add_furniture(r1_id, "Coffee Table", 450.0, "Center", "table", 120.0, 130.0)
            self.add_furniture(r2_id, "Dining Table Set", 1200.0, "Center", "table", 70.0, 80.0)

    # -------------------------------------------------------------
    # Projects CRUD
    # -------------------------------------------------------------
    def get_all_projects(self):
        cursor = self._query("SELECT project_id, name, budget, unit, created_at FROM projects ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        return [
            {
                'project_id': r[0],
                'name': r[1],
                'budget': float(r[2]),
                'unit': r[3],
                'created_at': str(r[4])
            }
            for r in rows
        ]

    def get_project(self, project_id):
        cursor = self._query("SELECT project_id, name, budget, unit, created_at FROM projects WHERE project_id = %s", (project_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return {
            'project_id': row[0],
            'name': row[1],
            'budget': float(row[2]),
            'unit': row[3],
            'created_at': str(row[4])
        }

    def create_project(self, name, budget=100000.0, unit="ft"):
        project_id = str(uuid.uuid4())
        self._query(
            "INSERT INTO projects (project_id, name, budget, unit) VALUES (%s, %s, %s, %s)",
            (project_id, name, float(budget), unit)
        )
        self._commit()
        self._create_default_floors(project_id)
        return project_id

    def update_project(self, project_id, name, budget, unit):
        self._query(
            "UPDATE projects SET name = %s, budget = %s, unit = %s WHERE project_id = %s",
            (name, float(budget), unit, project_id)
        )
        self._commit()

    def delete_project(self, project_id):
        self._query("DELETE FROM projects WHERE project_id = %s", (project_id,))
        self._commit()

    # -------------------------------------------------------------
    # Floors CRUD
    # -------------------------------------------------------------
    def _create_default_floors(self, project_id):
        defaults = [
            ("Basement", -1),
            ("Ground Floor", 0),
            ("First Floor", 1),
            ("Second Floor", 2),
            ("Attic", 3),
            ("Rooftop", 4)
        ]
        for name, level in defaults:
            self.add_floor(project_id, name, level)

    def get_floors(self, project_id):
        cursor = self._query("SELECT floor_id, project_id, name, level FROM floors WHERE project_id = %s ORDER BY level ASC", (project_id,))
        rows = cursor.fetchall()
        cursor.close()
        return [
            {
                'floor_id': r[0],
                'project_id': r[1],
                'name': r[2],
                'level': int(r[3])
            }
            for r in rows
        ]

    def add_floor(self, project_id, name, level):
        floor_id = str(uuid.uuid4())
        self._query(
            "INSERT INTO floors (floor_id, project_id, name, level) VALUES (%s, %s, %s, %s)",
            (floor_id, project_id, name, int(level))
        )
        self._commit()
        return floor_id

    def delete_floor(self, floor_id):
        self._query("DELETE FROM floors WHERE floor_id = %s", (floor_id,))
        self._commit()

    # -------------------------------------------------------------
    # Rooms CRUD
    # -------------------------------------------------------------
    def get_rooms(self, project_id, floor_id=None):
        if floor_id:
            cursor = self._query(
                """SELECT room_id, project_id, floor_id, name, type, cost, width, height, area,
                          flooring, wall_color, windows, x, y
                   FROM rooms WHERE project_id = %s AND floor_id = %s""",
                (project_id, floor_id)
            )
        else:
            cursor = self._query(
                """SELECT room_id, project_id, floor_id, name, type, cost, width, height, area,
                          flooring, wall_color, windows, x, y
                   FROM rooms WHERE project_id = %s""",
                (project_id,)
            )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {
                'room_id': r[0],
                'project_id': r[1],
                'floor_id': r[2],
                'name': r[3],
                'type': r[4],
                'cost': float(r[5]),
                'width': float(r[6]),
                'height': float(r[7]),
                'area': float(r[8]),
                'flooring': r[9],
                'wall_color': r[10],
                'windows': int(r[11]),
                'x': float(r[12]),
                'y': float(r[13])
            }
            for r in rows
        ]

    def get_room(self, room_id):
        cursor = self._query(
            """SELECT room_id, project_id, floor_id, name, type, cost, width, height, area,
                      flooring, wall_color, windows, x, y
               FROM rooms WHERE room_id = %s""",
            (room_id,)
        )
        r = cursor.fetchone()
        cursor.close()
        if not r:
            return None
        return {
            'room_id': r[0],
            'project_id': r[1],
            'floor_id': r[2],
            'name': r[3],
            'type': r[4],
            'cost': float(r[5]),
            'width': float(r[6]),
            'height': float(r[7]),
            'area': float(r[8]),
            'flooring': r[9],
            'wall_color': r[10],
            'windows': int(r[11]),
            'x': float(r[12]),
            'y': float(r[13])
        }

    def add_room(self, project_id, floor_id, name, room_type, cost=0.0, width=220.0, height=180.0,
                 area=99.0, flooring='Standard', wall_color='White', windows=0, x=20.0, y=20.0):
        room_id = str(uuid.uuid4())
        self._query(
            """INSERT INTO rooms
               (room_id, project_id, floor_id, name, type, cost, width, height, area, flooring, wall_color, windows, x, y)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (room_id, project_id, floor_id, name, room_type, float(cost), float(width), float(height),
             float(area), flooring, wall_color, int(windows), float(x), float(y))
        )
        self._commit()
        return room_id

    def update_room_position(self, room_id, x, y):
        self._query("UPDATE rooms SET x = %s, y = %s WHERE room_id = %s", (float(x), float(y), room_id))
        self._commit()

    def update_room_size(self, room_id, width, height, area):
        self._query("UPDATE rooms SET width = %s, height = %s, area = %s WHERE room_id = %s",
                    (float(width), float(height), float(area), room_id))
        self._commit()

    def update_room_floor(self, room_id, floor_id):
        self._query("UPDATE rooms SET floor_id = %s WHERE room_id = %s", (floor_id, room_id))
        self._commit()

    def update_room_details(self, room_id, name, room_type, cost, flooring, wall_color, windows):
        self._query(
            """UPDATE rooms
               SET name = %s, type = %s, cost = %s, flooring = %s, wall_color = %s, windows = %s
               WHERE room_id = %s""",
            (name, room_type, float(cost), flooring, wall_color, int(windows), room_id)
        )
        self._commit()

    def delete_room(self, room_id):
        self._query("DELETE FROM rooms WHERE room_id = %s", (room_id,))
        self._commit()

    def duplicate_room(self, room_id):
        orig = self.get_room(room_id)
        if not orig:
            return None
        new_id = self.add_room(
            project_id=orig['project_id'],
            floor_id=orig['floor_id'],
            name=f"{orig['name']} (Copy)",
            room_type=orig['type'],
            cost=orig['cost'],
            width=orig['width'],
            height=orig['height'],
            area=orig['area'],
            flooring=orig['flooring'],
            wall_color=orig['wall_color'],
            windows=orig['windows'],
            x=orig['x'] + 30.0,
            y=orig['y'] + 30.0
        )
        # Copy furniture as well
        furniture_list = self.get_furniture(room_id)
        for f in furniture_list:
            self.add_furniture(
                room_id=new_id,
                name=f['name'],
                cost=f['cost'],
                position=f['position'],
                model=f['model'],
                x=f['x'],
                y=f['y'],
                attached_to=f['attached_to']
            )
        return new_id

    # -------------------------------------------------------------
    # Furniture CRUD
    # -------------------------------------------------------------
    def get_furniture(self, room_id=None, project_id=None):
        if room_id:
            cursor = self._query(
                "SELECT furniture_id, room_id, name, cost, position, model, x, y, attached_to FROM furniture WHERE room_id = %s",
                (room_id,)
            )
        elif project_id:
            cursor = self._query(
                """SELECT f.furniture_id, f.room_id, f.name, f.cost, f.position, f.model, f.x, f.y, f.attached_to
                   FROM furniture f
                   JOIN rooms r ON f.room_id = r.room_id
                   WHERE r.project_id = %s""",
                (project_id,)
            )
        else:
            cursor = self._query(
                "SELECT furniture_id, room_id, name, cost, position, model, x, y, attached_to FROM furniture"
            )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {
                'furniture_id': r[0],
                'room_id': r[1],
                'name': r[2],
                'cost': float(r[3]),
                'position': r[4],
                'model': r[5],
                'x': float(r[6]),
                'y': float(r[7]),
                'attached_to': r[8]
            }
            for r in rows
        ]

    def add_furniture(self, room_id, name, cost=0.0, position='Center', model='box', x=20.0, y=20.0, attached_to='floor'):
        furniture_id = str(uuid.uuid4())
        self._query(
            """INSERT INTO furniture
               (furniture_id, room_id, name, cost, position, model, x, y, attached_to)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (furniture_id, room_id, name, float(cost), position, model, float(x), float(y), attached_to)
        )
        self._commit()
        return furniture_id

    def update_furniture_pos(self, furniture_id, x, y, attached_to=None, room_id=None):
        if room_id:
            self._query("UPDATE furniture SET room_id = %s, x = %s, y = %s WHERE furniture_id = %s",
                        (room_id, float(x), float(y), furniture_id))
        elif attached_to:
            self._query("UPDATE furniture SET x = %s, y = %s, attached_to = %s WHERE furniture_id = %s",
                        (float(x), float(y), attached_to, furniture_id))
        else:
            self._query("UPDATE furniture SET x = %s, y = %s WHERE furniture_id = %s",
                        (float(x), float(y), furniture_id))
        self._commit()

    def delete_furniture(self, furniture_id):
        self._query("DELETE FROM furniture WHERE furniture_id = %s", (furniture_id,))
        self._commit()

    # -------------------------------------------------------------
    # Project Financial Summary & Analytics
    # -------------------------------------------------------------
    def get_project_summary(self, project_id):
        project = self.get_project(project_id)
        if not project:
            return None
        rooms = self.get_rooms(project_id)
        furniture = self.get_furniture(project_id=project_id)

        total_room_cost = sum(r['cost'] for r in rooms)
        total_furn_cost = sum(f['cost'] for f in furniture)
        total_spending = total_room_cost + total_furn_cost
        remaining_budget = project['budget'] - total_spending
        total_area = sum(r['area'] for r in rooms)

        return {
            'project': project,
            'room_count': len(rooms),
            'furniture_count': len(furniture),
            'total_room_cost': total_room_cost,
            'total_furn_cost': total_furn_cost,
            'total_spending': total_spending,
            'remaining_budget': remaining_budget,
            'total_area': total_area,
            'rooms': rooms,
            'furniture': furniture
        }
