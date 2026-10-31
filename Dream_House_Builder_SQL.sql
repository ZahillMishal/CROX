-- =====================================================================
--  DREAM HOUSE BUILDER  -  MySQL database
--  Run this once in MySQL Workbench / command line:  source Dream_House_Builder_SQL.sql
--  (The Python program also creates/upgrades these tables automatically.)
-- =====================================================================
CREATE DATABASE IF NOT EXISTS dream_house_builder;
USE dream_house_builder;

-- One row per saved house design
CREATE TABLE IF NOT EXISTS projects (
    project_id     INT AUTO_INCREMENT PRIMARY KEY,
    project_name   VARCHAR(100) NOT NULL,
    budget         BIGINT NOT NULL DEFAULT 1000000,
    layout_version INT NOT NULL DEFAULT 2,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rooms of a project. pos_x / pos_y = room position on the floor plan (feet)
CREATE TABLE IF NOT EXISTS rooms (
    room_id     INT AUTO_INCREMENT PRIMARY KEY,
    project_id  INT NOT NULL,
    room_name   VARCHAR(80) NOT NULL,
    room_type   VARCHAR(30) NOT NULL DEFAULT 'Living Room',
    width_ft    INT NOT NULL,
    length_ft   INT NOT NULL,
    floor_type  VARCHAR(40) DEFAULT 'Wooden',
    wall_color  VARCHAR(20) DEFAULT '#DCC69F',
    base_cost   BIGINT NOT NULL DEFAULT 0,
    pos_x       INT NOT NULL DEFAULT 0,
    pos_y       INT NOT NULL DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- Furniture inside rooms. pos_x / pos_y = centre of the item in TENTHS of a foot from the
-- room's top-left corner. rotation = 0, 90, 180 or 270 degrees.
CREATE TABLE IF NOT EXISTS furniture (
    furniture_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id      INT NOT NULL,
    item_name    VARCHAR(80) NOT NULL,
    item_type    VARCHAR(40) NOT NULL DEFAULT '',
    price        BIGINT NOT NULL,
    pos_x        INT DEFAULT 0,
    pos_y        INT DEFAULT 0,
    rotation     INT DEFAULT 0,
    color        VARCHAR(10) DEFAULT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);

-- Handy summary for the viva: cost of every project
CREATE OR REPLACE VIEW project_summary AS
SELECT p.project_id, p.project_name, p.budget,
       COUNT(DISTINCT r.room_id)                         AS rooms,
       COALESCE(SUM(DISTINCT r.base_cost), 0)            AS room_cost
FROM projects p LEFT JOIN rooms r ON r.project_id = p.project_id
GROUP BY p.project_id, p.project_name, p.budget;

SHOW TABLES;

-- ---- Useful sample queries ----
-- SELECT * FROM projects;
-- SELECT r.room_name, f.item_name, f.price FROM rooms r JOIN furniture f ON f.room_id = r.room_id WHERE r.project_id = 1;
-- SELECT r.room_name, SUM(f.price) AS furniture_cost FROM rooms r JOIN furniture f ON f.room_id = r.room_id GROUP BY r.room_name;
-- ---- Upgrading an OLD database made with the first version? Just run the Python program once;
-- ---- it adds the missing columns automatically.
