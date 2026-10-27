-- ==========================================================
-- CROX - Computer Science Project Database Schema (MySQL)
-- Architecture Blueprint & Interior Budget Management System
-- ==========================================================

CREATE DATABASE IF NOT EXISTS crox_db;
USE crox_db;

-- ----------------------------------------------------------
-- 1. Table: projects
-- Stores project metadata, total budget, and measurement unit
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    budget DOUBLE NOT NULL DEFAULT 100000.0,
    unit VARCHAR(10) NOT NULL DEFAULT 'ft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- 2. Table: floors
-- Stores architectural levels (Basement, Ground Floor, etc.)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS floors (
    floor_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL,
    name VARCHAR(100) NOT NULL,
    level INT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- 3. Table: rooms
-- Stores room entities, dimensions, 2D coordinates, and styling
-- ----------------------------------------------------------
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

-- ----------------------------------------------------------
-- 4. Table: furniture
-- Stores furniture items attached to specific rooms
-- ----------------------------------------------------------
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
