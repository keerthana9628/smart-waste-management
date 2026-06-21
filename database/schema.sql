-- ============================================================
-- Smart Waste Management System - Database Schema (MySQL)
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_waste_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smart_waste_db;

-- ------------------------------------------------------------
-- Table: users
-- Stores admin and collector accounts
-- ------------------------------------------------------------
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    role            ENUM('admin', 'collector') NOT NULL DEFAULT 'collector',
    email           VARCHAR(120),
    phone           VARCHAR(20),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: bins
-- Stores all smart dustbins and their current status
-- ------------------------------------------------------------
CREATE TABLE bins (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    bin_code            VARCHAR(20)  NOT NULL UNIQUE,
    location            VARCHAR(150) NOT NULL,
    latitude            DECIMAL(10,6),
    longitude           DECIMAL(10,6),
    capacity_l          INT NOT NULL DEFAULT 100,      -- capacity in liters
    fill_level          DECIMAL(5,2) NOT NULL DEFAULT 0, -- percentage 0-100
    status              ENUM('empty', 'half', 'full') NOT NULL DEFAULT 'empty',
    waste_type          VARCHAR(50) DEFAULT 'general',
    last_collected_at   DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: bin_fill_history
-- Time-series fill level readings, used for ML predictions
-- ------------------------------------------------------------
CREATE TABLE bin_fill_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    bin_id      INT NOT NULL,
    fill_level  DECIMAL(5,2) NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Table: alerts
-- Auto-generated when a bin crosses the fill threshold (80%)
-- ------------------------------------------------------------
CREATE TABLE alerts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    bin_id      INT NOT NULL,
    alert_type  ENUM('fill_warning', 'full', 'maintenance') NOT NULL DEFAULT 'fill_warning',
    message     VARCHAR(255) NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Table: collections
-- Collection schedules + history, assigned to collectors
-- ------------------------------------------------------------
CREATE TABLE collections (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    bin_id          INT NOT NULL,
    collector_id    INT,
    scheduled_date  DATE NOT NULL,
    scheduled_time  TIME,
    status          ENUM('pending', 'in_progress', 'completed', 'missed') NOT NULL DEFAULT 'pending',
    waste_collected_kg DECIMAL(6,2),
    collected_at    DATETIME,
    notes           VARCHAR(255),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE CASCADE,
    FOREIGN KEY (collector_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- Table: activity_logs
-- Audit trail of important actions across the system
-- ------------------------------------------------------------
CREATE TABLE activity_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    action      VARCHAR(100) NOT NULL,
    details     VARCHAR(255),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- Helpful indexes
-- ------------------------------------------------------------
CREATE INDEX idx_bins_status ON bins(status);
CREATE INDEX idx_history_bin ON bin_fill_history(bin_id, recorded_at);
CREATE INDEX idx_alerts_resolved ON alerts(is_resolved);
CREATE INDEX idx_collections_status ON collections(status);
CREATE INDEX idx_collections_date ON collections(scheduled_date);
