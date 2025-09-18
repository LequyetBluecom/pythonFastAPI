-- =====================================================
-- MySQL Database Bootstrap Script
-- Hệ thống Thanh toán QR Trường học (FULL)
-- =====================================================

-- Tạo database
CREATE DATABASE IF NOT EXISTS school_payment_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE school_payment_db;

-- =====================================================
-- Bảng users
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role ENUM('admin', 'accountant', 'teacher', 'parent') NOT NULL,
    hashed_password VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng students
-- =====================================================
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    student_code VARCHAR(20) UNIQUE NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    grade VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_student_code (student_code),
    INDEX idx_class_name (class_name),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng fees (khoản phí chuẩn)
-- =====================================================
CREATE TABLE IF NOT EXISTS fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    default_amount DECIMAL(12,2) NOT NULL,
    fee_type ENUM('hoc_phi','dong_phuc','ngoai_khoa','khac') DEFAULT 'hoc_phi',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- Bảng orders
-- =====================================================
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    order_code VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status ENUM('pending', 'paid', 'invoiced') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP NULL,
    fee_id INT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (fee_id) REFERENCES fees(id) ON DELETE SET NULL,
    INDEX idx_order_code (order_code),
    INDEX idx_student_id (student_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng payments
-- =====================================================
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    payment_code VARCHAR(100) UNIQUE NOT NULL,
    gateway_txn_id VARCHAR(100),
    amount DECIMAL(12,2) NOT NULL,
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending',
    payment_method VARCHAR(50),
    qr_code_data TEXT,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_payment_code (payment_code),
    INDEX idx_order_id (order_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng invoices
-- =====================================================
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    invoice_code VARCHAR(100),
    e_invoice_code VARCHAR(100),
    customer_name VARCHAR(100) NOT NULL,
    customer_tax_code VARCHAR(20),
    customer_address VARCHAR(255),
    amount DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL,
    pdf_path VARCHAR(255),
    xml_path VARCHAR(255),
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP NULL,
    xml_checksum VARCHAR(128) NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_invoice_number (invoice_number),
    INDEX idx_order_id (order_id),
    INDEX idx_issued_at (issued_at)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng printer_agents
-- =====================================================
CREATE TABLE IF NOT EXISTS printer_agents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host_id VARCHAR(100) UNIQUE NOT NULL,
    host_name VARCHAR(100),
    jwt_token VARCHAR(500),
    last_seen TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_host_id (host_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng printers
-- =====================================================
CREATE TABLE IF NOT EXISTS printers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    ip_address VARCHAR(50),
    printer_type VARCHAR(50),
    agent_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES printer_agents(id) ON DELETE SET NULL,
    INDEX idx_name (name),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng print_jobs
-- =====================================================
CREATE TABLE IF NOT EXISTS print_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    printer_id INT NOT NULL,
    invoice_id INT NOT NULL,
    job_data TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    INDEX idx_printer_id (printer_id),
    INDEX idx_invoice_id (invoice_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- =====================================================
-- Bảng system_configs
-- =====================================================
CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- Bảng system_logs
-- =====================================================
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================
-- Bảng roles và user_roles
-- =====================================================
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================
-- Dữ liệu mẫu
-- =====================================================
INSERT INTO users (name, email, phone, role, hashed_password, is_active) VALUES
('Nguyễn Văn Admin', 'admin@school.edu.vn', '0901234567', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/5Kz8K2O', TRUE),
('Trần Thị Kế Toán', 'accountant@school.edu.vn', '0901234568', 'accountant', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/5Kz8K2O', TRUE),
('Lê Văn Giáo Vụ', 'teacher@school.edu.vn', '0901234569', 'teacher', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/5Kz8K2O', TRUE),
('Phạm Thị Phụ Huynh', 'parent1@email.com', '0901234570', 'parent', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/5Kz8K2O', TRUE),
('Hoàng Văn Phụ Huynh 2', 'parent2@email.com', '0901234571', 'parent', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/5Kz8K2O', TRUE);

INSERT INTO students (user_id, name, student_code, class_name, grade) VALUES
(4, 'Phạm Minh Anh', 'HS001', '1A', '1'),
(4, 'Phạm Thị Bình', 'HS002', '2B', '2'),
(5, 'Hoàng Văn Cường', 'HS003', '3A', '3'),
(5, 'Hoàng Thị Dung', 'HS004', '4B', '4');

INSERT INTO orders (student_id, order_code, description, amount, status, due_date) VALUES
(1, 'ORD-ABC12345', 'Học phí tháng 1/2024', 500000.00, 'pending', '2024-02-15 23:59:59'),
(1, 'ORD-ABC12346', 'Phí đồng phục học sinh', 200000.00, 'pending', '2024-02-20 23:59:59'),
(2, 'ORD-ABC12347', 'Học phí tháng 1/2024', 500000.00, 'paid', '2024-02-15 23:59:59'),
(3, 'ORD-ABC12348', 'Học phí tháng 1/2024', 500000.00, 'pending', '2024-02-15 23:59:59'),
(4, 'ORD-ABC12349', 'Học phí tháng 1/2024', 500000.00, 'paid', '2024-02-15 23:59:59');

INSERT INTO payments (order_id, payment_code, gateway_txn_id, amount, status, payment_method, qr_code_data, paid_at) VALUES
(3, 'TXN-PAY12345', 'GATEWAY-TXN-001', 500000.00, 'success', 'QR_CODE', 'VIETQR|demo-merchant|TXN-PAY12345|500000|VND|Học phí tháng 1/2024', '2024-01-15 10:30:00'),
(5, 'TXN-PAY12346', 'GATEWAY-TXN-002', 500000.00, 'success', 'QR_CODE', 'VIETQR|demo-merchant|TXN-PAY12346|500000|VND|Học phí tháng 1/2024', '2024-01-16 14:20:00');

INSERT INTO invoices (order_id, invoice_number, invoice_code, e_invoice_code, customer_name, customer_tax_code, customer_address, amount, tax_amount, total_amount, pdf_path, xml_path) VALUES
(3, 'HD20240115001', 'C25TTA240115ABC123', 'TCT12345678', 'Phạm Thị Phụ Huynh', '', '', 500000.00, 0.00, 500000.00, 'invoices/pdf/invoice_1.pdf', 'invoices/xml/invoice_1.xml'),
(5, 'HD20240116001', 'C25TTA240116DEF456', 'TCT87654321', 'Hoàng Văn Phụ Huynh 2', '', '', 500000.00, 0.00, 500000.00, 'invoices/pdf/invoice_2.pdf', 'invoices/xml/invoice_2.xml');

INSERT INTO printer_agents (host_id, host_name, jwt_token, last_seen, is_active) VALUES
('AGENT-001', 'Máy in phòng kế toán', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...', '2024-01-20 09:00:00', TRUE),
('AGENT-002', 'Máy in phòng hiệu trưởng', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...', '2024-01-20 08:30:00', TRUE);

INSERT INTO printers (name, location, ip_address, printer_type, agent_id, is_active) VALUES
('HP LaserJet Pro M404n', 'Phòng kế toán', '192.168.1.100', 'LASER', 1, TRUE),
('Canon PIXMA G3110', 'Phòng hiệu trưởng', '192.168.1.101', 'INKJET', 2, TRUE);

INSERT INTO print_jobs (printer_id, invoice_id, job_data, status, sent_at, completed_at) VALUES
(1, 1, '{"invoice_id": 1, "printer_id": 1, "copies": 1, "paper_size": "A4"}', 'completed', '2024-01-15 10:35:00', '2024-01-15 10:36:00'),
(2, 2, '{"invoice_id": 2, "printer_id": 2, "copies": 2, "paper_size": "A4"}', 'completed', '2024-01-16 14:25:00', '2024-01-16 14:26:00');

-- Roles
INSERT IGNORE INTO roles (name, description) VALUES
('admin', 'Quản trị hệ thống'),
('accountant', 'Kế toán'),
('teacher', 'Giáo vụ'),
('parent', 'Phụ huynh');

-- Gán role cho user đã có
INSERT IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u 
JOIN roles r ON u.role = r.name;

-- =====================================================
-- Views
-- =====================================================
CREATE OR REPLACE VIEW v_student_parent_info AS
SELECT 
    s.id as student_id,
    s.name as student_name,
    s.student_code,
    s.class_name,
    s.grade,
    u.id as parent_id,
    u.name as parent_name,
    u.email as parent_email,
    u.phone as parent_phone
FROM students s
JOIN users u ON s.user_id = u.id;

CREATE OR REPLACE VIEW v_order_payment_info AS
SELECT 
    o.id as order_id,
    o.order_code,
    o.description,
    o.amount as order_amount,
    o.status as order_status,
    o.created_at as order_created_at,
    o.due_date,
    s.name as student_name,
    s.student_code,
    s.class_name,
    u.name as parent_name,
    u.email as parent_email,
    p.id as payment_id,
    p.payment_code,
    p.amount as payment_amount,
    p.status as payment_status,
    p.paid_at,
    i.id as invoice_id,
    i.invoice_number,
    i.total_amount as invoice_amount
FROM orders o
LEFT JOIN students s ON o.student_id = s.id
LEFT JOIN users u ON s.user_id = u.id
LEFT JOIN payments p ON o.id = p.order_id
LEFT JOIN invoices i ON o.id = i.order_id;

-- =====================================================
-- Stored Procedures
-- =====================================================
DELIMITER //

CREATE PROCEDURE sp_revenue_report(
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    SELECT 
        DATE(p.paid_at) as payment_date,
        COUNT(*) as transaction_count,
        SUM(p.amount) as total_revenue,
        AVG(p.amount) as avg_transaction
    FROM payments p
    WHERE p.status = 'success' 
        AND p.paid_at >= start_date 
        AND p.paid_at <= end_date
    GROUP BY DATE(p.paid_at)
    ORDER BY payment_date;
END //

CREATE PROCEDURE sp_collection_by_class()
BEGIN
    SELECT 
        s.class_name,
        COUNT(DISTINCT s.id) as student_count,
        COUNT(o.id) as total_orders,
        SUM(CASE WHEN o.status IN ('paid', 'invoiced') THEN 1 ELSE 0 END) as paid_orders,
        SUM(o.amount) as total_amount,
        SUM(CASE WHEN o.status IN ('paid', 'invoiced') THEN o.amount ELSE 0 END) as paid_amount,
        ROUND(
            (SUM(CASE WHEN o.status IN ('paid', 'invoiced') THEN o.amount ELSE 0 END) / SUM(o.amount)) * 100, 2
        ) as collection_rate
    FROM students s
    LEFT JOIN orders o ON s.id = o.student_id
    GROUP BY s.class_name
    ORDER BY collection_rate DESC;
END //

DELIMITER ;

-- =====================================================
-- Indexes bổ sung
-- =====================================================
CREATE INDEX idx_payments_paid_at ON payments(paid_at);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_invoices_issued_at ON invoices(issued_at);

CREATE INDEX idx_orders_status_created ON orders(status, created_at);
CREATE INDEX idx_payments_status_created ON payments(status, created_at);

-- =====================================================
-- Triggers
-- =====================================================
DELIMITER //

CREATE TRIGGER tr_payment_success_update_order
AFTER UPDATE ON payments
FOR EACH ROW
BEGIN
    IF NEW.status = 'success' AND OLD.status != 'success' THEN
        UPDATE orders 
        SET status = 'paid' 
        WHERE id = NEW.order_id AND status = 'pending';
    END IF;
END //

CREATE TRIGGER tr_invoice_created_update_order
AFTER INSERT ON invoices
FOR EACH ROW
BEGIN
    UPDATE orders 
    SET status = 'invoiced' 
    WHERE id = NEW.order_id AND status = 'paid';
END //

DELIMITER ;

-- =====================================================
-- Kết thúc script
-- =====================================================
SELECT 'Database và dữ liệu mẫu FULL đã được tạo thành công!' as message;
