-- ============================================================
-- Smart Waste Management System - Sample Seed Data
-- Run AFTER schema.sql
-- Default password for all users below is: "password123"
-- (hash generated using Werkzeug's generate_password_hash - pbkdf2:sha256)
-- ============================================================

USE smart_waste_db;

-- ------------------------------------------------------------
-- Users (1 admin + 3 collectors)
-- Password for all = password123
-- ------------------------------------------------------------
INSERT INTO users (username, password_hash, full_name, role, email, phone) VALUES
('admin',     'pbkdf2:sha256:600000$YwL0sB1F$d3a4b1e8c1b16f7d3a7e6e7f6f9a5d4c3b2a1e8f7d6c5b4a3e2f1c0b9a8d7e6f', 'System Administrator', 'admin', 'admin@ewit.edu', '9000000001'),
('collector1','pbkdf2:sha256:600000$YwL0sB1F$d3a4b1e8c1b16f7d3a7e6e7f6f9a5d4c3b2a1e8f7d6c5b4a3e2f1c0b9a8d7e6f', 'Ravi Kumar',          'collector', 'ravi@ewit.edu', '9000000002'),
('collector2','pbkdf2:sha256:600000$YwL0sB1F$d3a4b1e8c1b16f7d3a7e6e7f6f9a5d4c3b2a1e8f7d6c5b4a3e2f1c0b9a8d7e6f', 'Suresh Babu',         'collector', 'suresh@ewit.edu', '9000000003'),
('collector3','pbkdf2:sha256:600000$YwL0sB1F$d3a4b1e8c1b16f7d3a7e6e7f6f9a5d4c3b2a1e8f7d6c5b4a3e2f1c0b9a8d7e6f', 'Lakshmi Narayan',     'collector', 'lakshmi@ewit.edu', '9000000004');

-- NOTE: The hashes above are placeholders. Run `python seed_db.py` instead,
-- which creates users with correctly generated hashes via Werkzeug at
-- runtime (recommended). This SQL file is provided for reference / direct
-- MySQL import if you prefer not to use the seed script.

-- ------------------------------------------------------------
-- Bins (12 sample bins across a campus)
-- ------------------------------------------------------------
INSERT INTO bins (bin_code, location, latitude, longitude, capacity_l, fill_level, status, waste_type, last_collected_at) VALUES
('BIN-001', 'Main Gate',                 12.9352, 77.5347, 120, 92.0, 'full', 'general', NOW() - INTERVAL 2 DAY),
('BIN-002', 'Library Block',             12.9355, 77.5350, 100, 45.0, 'half', 'general', NOW() - INTERVAL 1 DAY),
('BIN-003', 'Canteen Area',              12.9358, 77.5353, 150, 88.0, 'full', 'organic', NOW() - INTERVAL 3 DAY),
('BIN-004', 'AIML Department',           12.9360, 77.5355, 100, 22.0, 'empty', 'general', NOW() - INTERVAL 1 DAY),
('BIN-005', 'Hostel Block A',            12.9363, 77.5358, 200, 67.0, 'half', 'general', NOW() - INTERVAL 2 DAY),
('BIN-006', 'Hostel Block B',            12.9365, 77.5360, 200, 81.0, 'full', 'general', NOW() - INTERVAL 4 DAY),
('BIN-007', 'Sports Ground',             12.9368, 77.5363, 100, 15.0, 'empty', 'general', NOW() - INTERVAL 1 DAY),
('BIN-008', 'Admin Block',               12.9370, 77.5365, 100, 53.0, 'half', 'general', NOW() - INTERVAL 2 DAY),
('BIN-009', 'Mechanical Workshop',       12.9372, 77.5368, 150, 30.0, 'empty', 'recyclable', NOW() - INTERVAL 1 DAY),
('BIN-010', 'Parking Area',              12.9375, 77.5370, 100, 76.0, 'half', 'general', NOW() - INTERVAL 3 DAY),
('BIN-011', 'Auditorium',                12.9378, 77.5372, 150, 95.0, 'full', 'general', NOW() - INTERVAL 5 DAY),
('BIN-012', 'Faculty Quarters',          12.9380, 77.5375, 100, 10.0, 'empty', 'general', NOW() - INTERVAL 1 DAY);

-- ------------------------------------------------------------
-- Alerts (auto-generated for bins above 80%)
-- ------------------------------------------------------------
INSERT INTO alerts (bin_id, alert_type, message, is_resolved, created_at) VALUES
(1, 'full',         'BIN-001 (Main Gate) has reached 92% capacity. Immediate collection required.', FALSE, NOW() - INTERVAL 5 HOUR),
(3, 'full',         'BIN-003 (Canteen Area) has reached 88% capacity. Immediate collection required.', FALSE, NOW() - INTERVAL 8 HOUR),
(6, 'fill_warning', 'BIN-006 (Hostel Block B) has reached 81% capacity. Schedule collection soon.', FALSE, NOW() - INTERVAL 12 HOUR),
(11,'full',         'BIN-011 (Auditorium) has reached 95% capacity. Immediate collection required.', FALSE, NOW() - INTERVAL 2 HOUR),
(10,'fill_warning', 'BIN-010 (Parking Area) reached 76% capacity yesterday.', TRUE, NOW() - INTERVAL 1 DAY);

-- ------------------------------------------------------------
-- Collections (scheduled + completed history)
-- ------------------------------------------------------------
INSERT INTO collections (bin_id, collector_id, scheduled_date, scheduled_time, status, waste_collected_kg, collected_at, notes) VALUES
(1, 2, CURDATE(), '09:00:00', 'pending', NULL, NULL, 'Urgent - bin nearly full'),
(3, 3, CURDATE(), '10:00:00', 'pending', NULL, NULL, 'Urgent - organic waste'),
(11,2, CURDATE(), '09:30:00', 'pending', NULL, NULL, 'Urgent - auditorium event tomorrow'),
(6, 4, CURDATE(), '11:00:00', 'pending', NULL, NULL, NULL),
(2, 2, CURDATE() - INTERVAL 1 DAY, '09:00:00', 'completed', 18.5, NOW() - INTERVAL 1 DAY, 'Routine collection'),
(5, 3, CURDATE() - INTERVAL 1 DAY, '10:30:00', 'completed', 32.0, NOW() - INTERVAL 1 DAY, 'Routine collection'),
(7, 4, CURDATE() - INTERVAL 2 DAY, '09:00:00', 'completed', 8.2,  NOW() - INTERVAL 2 DAY, NULL),
(9, 2, CURDATE() - INTERVAL 2 DAY, '14:00:00', 'completed', 12.0, NOW() - INTERVAL 2 DAY, NULL),
(4, 3, CURDATE() - INTERVAL 3 DAY, '09:00:00', 'missed',   NULL, NULL, 'Collector unavailable');

-- ------------------------------------------------------------
-- Activity logs
-- ------------------------------------------------------------
INSERT INTO activity_logs (user_id, action, details) VALUES
(1, 'LOGIN', 'Admin logged in'),
(1, 'ADD_BIN', 'Added new bin BIN-012 at Faculty Quarters'),
(1, 'CREATE_SCHEDULE', 'Created collection schedule for BIN-001'),
(2, 'UPDATE_COLLECTION', 'Marked BIN-002 collection as completed'),
(1, 'RESOLVE_ALERT', 'Resolved alert for BIN-010');
