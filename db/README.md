# Database Setup - Hệ thống Thanh toán QR Trường học

## Cài đặt MySQL Database

### 1. Yêu cầu hệ thống
- MySQL 8.0+ hoặc MariaDB 10.3+
- Quyền tạo database và user

### 2. Chạy script tạo database

```bash
# Kết nối MySQL
mysql -u root -p

# Chạy script tạo database và dữ liệu
source /path/to/db/mysql_bootstrap.sql
```

Hoặc chạy trực tiếp:
```bash
mysql -u root -p < db/mysql_bootstrap.sql
```

### 3. Cấu hình kết nối trong ứng dụng

Tạo file `.env` trong thư mục gốc:
```env
# Database
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/school_payment_db

# Hoặc nếu dùng user riêng
# DATABASE_URL=mysql+pymysql://school_payment_app:secure_password@localhost:3306/school_payment_db

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Environment
ENVIRONMENT=development
DEBUG=true
```

### 4. Cài đặt MySQL driver cho Python

```bash
pip install PyMySQL
```

### 5. Cấu trúc Database

#### Bảng chính:
- **users**: Người dùng (admin, accountant, teacher, parent)
- **students**: Học sinh (liên kết với phụ huynh)
- **orders**: Đơn hàng/phiếu thu học phí
- **payments**: Giao dịch thanh toán
- **invoices**: Hóa đơn điện tử
- **printers**: Máy in
- **printer_agents**: Agent quản lý máy in
- **print_jobs**: Lệnh in

#### Dữ liệu mẫu:
- 5 users (1 admin, 1 accountant, 1 teacher, 2 parents)
- 4 students (2 học sinh/phụ huynh)
- 5 orders (học phí, phí đồng phục)
- 2 payments (đã thanh toán)
- 2 invoices (hóa đơn điện tử)
- 2 printers + agents
- 2 print jobs

### 6. Tài khoản mẫu

| Role | Email | Password | Mô tả |
|------|-------|----------|-------|
| admin | admin@school.edu.vn | Admin@123 | Quản trị viên |
| accountant | accountant@school.edu.vn | Accountant@123 | Kế toán |
| teacher | teacher@school.edu.vn | Teacher@123 | Giáo vụ |
| parent | parent1@email.com | Parent@123 | Phụ huynh 1 |
| parent | parent2@email.com | Parent@123 | Phụ huynh 2 |

### 7. Views và Procedures

#### Views:
- `v_student_parent_info`: Thông tin học sinh và phụ huynh
- `v_order_payment_info`: Tổng hợp đơn hàng, thanh toán, hóa đơn

#### Stored Procedures:
- `sp_revenue_report(start_date, end_date)`: Báo cáo doanh thu theo thời gian
- `sp_collection_by_class()`: Báo cáo thu học phí theo lớp

### 8. Kiểm tra kết nối

```bash
# Chạy ứng dụng
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

# Kiểm tra API
curl http://localhost:5000/healthz
curl http://localhost:5000/docs
```

### 9. Troubleshooting

#### Lỗi kết nối MySQL:
- Kiểm tra MySQL service đang chạy
- Kiểm tra port 3306 có mở không
- Kiểm tra username/password
- Kiểm tra database đã được tạo chưa

#### Lỗi encoding:
- Đảm bảo MySQL sử dụng utf8mb4
- Kiểm tra collation của database

#### Lỗi foreign key:
- Chạy script theo đúng thứ tự
- Kiểm tra dữ liệu mẫu có đúng không
