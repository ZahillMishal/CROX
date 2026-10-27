# CROX — Architectural Blueprint & Budget Management System
## Pure Python + MySQL Desktop Edition

> **Version Note:** This is an independent, self-contained desktop edition of CROX developed strictly using **Python** and **MySQL**. It does not interfere with or modify the Flask web application in the root directory.

---

## 1. Overview
CROX (Python + MySQL Edition) is a computer science project designed for computer-aided architectural layout planning, floor-level space management, and real-time interior budget optimization.

Unlike web-based applications that rely on HTML, CSS, and JavaScript, this version is written **100% in Python** using the standard `tkinter` graphic system and persists all data to a relational **MySQL** database.

---

## 2. System Architecture & Features

### A. Python Desktop GUI (`tkinter` + `ttk`)
- **Interactive 2D Blueprint Canvas**:
  - Grid-based architectural coordinate system (scale: 20 pixels = 1 ft or 1 m).
  - Mouse-driven drag & drop with **magnetic edge snapping** (rooms snap flush together when moved within 15px).
  - Dynamic **doorway generation** between adjoining rooms on the same floor.
  - Multi-story **staircase generation** when rooms on adjacent floors vertically overlap.
  - Room header banners displaying dimensions, area, and color-coded tags.
  - Furniture rendering inside rooms with drag repositioning.
- **Project & Floor Management**:
  - Multi-project support with custom budgets and units (ft / m).
  - Architectural floor level switcher (Basement, Ground Floor, 1st Floor, 2nd Floor, etc.).
- **Live Financial & Property Inspector**:
  - Real-time budget tracking (Budget vs Spent vs Remaining).
  - Detailed room property inspector (dimensions, area, flooring, wall color, window count, itemized costs).
  - Comprehensive Project Analytics Dialog with room and furniture data tables.

---

## 3. Database Design (MySQL)

The database schema (`crox_db`) is normalized and enforces referential integrity through foreign keys with cascading deletes:

```
[projects] (1) --------< (M) [floors]
    |                          |
    | (1)                      | (1)
    |                          |
    v (M)                      v (M)
 [rooms] (1) ------------< (M) [furniture]
```

### Table Specifications:
1. **`projects`**:
   - `project_id` (VARCHAR 64, PK)
   - `name` (VARCHAR 100)
   - `budget` (DOUBLE)
   - `unit` (VARCHAR 10)
   - `created_at` (TIMESTAMP)

2. **`floors`**:
   - `floor_id` (VARCHAR 64, PK)
   - `project_id` (VARCHAR 64, FK -> projects.project_id ON DELETE CASCADE)
   - `name` (VARCHAR 100)
   - `level` (INT)

3. **`rooms`**:
   - `room_id` (VARCHAR 64, PK)
   - `project_id` (VARCHAR 64, FK -> projects.project_id ON DELETE CASCADE)
   - `floor_id` (VARCHAR 64, FK -> floors.floor_id ON DELETE CASCADE)
   - `name` (VARCHAR 100)
   - `type` (VARCHAR 50)
   - `cost` (DOUBLE)
   - `width`, `height`, `area` (DOUBLE)
   - `flooring`, `wall_color` (VARCHAR 50)
   - `windows` (INT)
   - `x`, `y` (DOUBLE)

4. **`furniture`**:
   - `furniture_id` (VARCHAR 64, PK)
   - `room_id` (VARCHAR 64, FK -> rooms.room_id ON DELETE CASCADE)
   - `name` (VARCHAR 100)
   - `cost` (DOUBLE)
   - `position`, `model` (VARCHAR 50)
   - `x`, `y` (DOUBLE)
   - `attached_to` (VARCHAR 50)

---

## 4. Automatic Offline Fallback (Zero Setup Hassle)
The application includes an intelligent database abstraction layer:
- If MySQL is installed and running, it automatically connects to MySQL, creates `crox_db`, and initializes all tables.
- If MySQL is not running or credentials have not been configured yet, the app **automatically falls back to a local SQLite database** (`crox_offline.db`). This ensures that teachers, examiners, or teammates can double-click and run the application instantly without configuration errors!

---

## 5. How to Run

### Method 1: Using the Batch Launcher (Windows)
Double-click:
```
run_desktop.bat
```
(Or `run_desktop_mysql.bat` in the root folder).

### Method 2: Manual Terminal Execution
1. Install MySQL drivers (optional if using MySQL server):
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python main.py
   ```

---

## 6. Configuring MySQL Connection
To connect to your specific MySQL server (e.g., XAMPP, WAMP, or MySQL Workbench):
1. Launch the application.
2. Click **⚙ Database Settings** in the top-right corner.
3. Enter your MySQL Host, Port (3306), Username (`root`), and Password.
4. Click **Test Connection**, then click **Save & Connect**.
