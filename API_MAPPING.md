# Tài liệu API Mapping - Hệ thống Thanh toán QR Trường học

## Tổng quan cấu trúc API

API đã được tái cấu trúc theo chuẩn FastAPI best practices với:
- **API Version**: v1 (prefix: `/api/v1`)
- **Response Format**: Chuẩn hóa với `success`, `message`, `data`, `meta`
- **Error Handling**: Centralized exception handling
- **Authentication**: JWT Bearer token
- **Documentation**: Swagger UI tại `/docs`

## Endpoints API v1

### 📋 Meta & System

| Endpoint | Method | Chức năng | Auth Required |
|----------|--------|-----------|---------------|
| `/api/v1/` | GET | Thông tin API v1 và danh sách endpoints | ❌ |
| `/` | GET | Thông tin hệ thống | ❌ |
| `/healthz` | GET | Health check | ❌ |
| `/docs` | GET | API Documentation (Swagger UI) | ❌ |

---

### 🔐 Authentication (`/api/v1/auth`)

| Endpoint | Method | Chức năng | Body Schema | Response |
|----------|--------|-----------|-------------|----------|
| `/login` | POST | Đăng nhập và lấy JWT token | `LoginRequest` | Access token + thông tin user |
| `/register` | POST | Đăng ký tài khoản phụ huynh | `UserCreate` | Thông tin user đã tạo |
| `/me` | GET | Lấy thông tin user hiện tại | - | User profile |

**Auth Flow:**
1. POST `/api/v1/auth/login` → Nhận access_token
2. Sử dụng header: `Authorization: Bearer <token>`
3. Token có thời hạn 30 phút

---

### 👥 Users Management (`/api/v1/users`)
*Chỉ Admin*

| Endpoint | Method | Chức năng | Auth Required | Role Required |
|----------|--------|-----------|---------------|---------------|
| `/` | GET | Danh sách tất cả users | ✅ | Admin |
| `/` | POST | Tạo user mới (Admin/Staff) | ✅ | Admin |
| `/{user_id}` | GET | Chi tiết user | ✅ | Admin |
| `/{user_id}` | PUT | Cập nhật user | ✅ | Admin |
| `/{user_id}/deactivate` | POST | Vô hiệu hóa user | ✅ | Admin |

---

### 👦 Students Management (`/api/v1/students`)

| Endpoint | Method | Chức năng | Auth Required | Role Required |
|----------|--------|-----------|---------------|---------------|
| `/` | GET | Danh sách học sinh | ✅ | All roles |
| `/` | POST | Thêm học sinh mới | ✅ | Admin/Teacher/Parent |
| `/{student_id}` | GET | Chi tiết học sinh | ✅ | All roles |
| `/{student_id}` | PUT | Cập nhật thông tin học sinh | ✅ | Admin/Teacher/Parent |
| `/my-students` | GET | Học sinh của phụ huynh | ✅ | Parent |

**Business Rules:**
- Parent chỉ quản lý học sinh của mình
- Admin/Teacher có thể quản lý tất cả học sinh

---

### 📋 Orders Management (`/api/v1/orders`)

| Endpoint | Method | Chức năng | Auth Required | Role Required |
|----------|--------|-----------|---------------|---------------|
| `/` | GET | Danh sách đơn hàng | ✅ | All roles |
| `/` | POST | Tạo đơn hàng (khoản phí) | ✅ | Admin/Accountant/Teacher |
| `/{order_id}` | GET | Chi tiết đơn hàng | ✅ | All roles |
| `/{order_id}` | PUT | Cập nhật đơn hàng | ✅ | Admin/Accountant |
| `/student/{student_id}` | GET | Đơn hàng của học sinh | ✅ | All roles |
| `/bulk-create` | POST | Tạo hàng loạt đơn hàng | ✅ | Admin/Accountant |

**Order Status Flow:**
`PENDING` → `PAID` → `INVOICED`

---

### 💳 Payments (`/api/v1/payments`)

| Endpoint | Method | Chức năng | Auth Required | Role Required |
|----------|--------|-----------|---------------|---------------|
| `/` | GET | Danh sách thanh toán | ✅ | Admin/Accountant |
| `/create-qr` | POST | Tạo QR code thanh toán | ✅ | All roles |
| `/{payment_id}` | GET | Chi tiết thanh toán | ✅ | All roles |
| `/webhook` | POST | Webhook từ cổng thanh toán | ❌ | Public |
| `/verify/{payment_id}` | POST | Xác minh thanh toán | ✅ | Admin/Accountant |

**Payment Flow:**
1. Tạo Order → Tạo QR code → Thanh toán → Webhook → Cập nhật status

---

### 📄 Invoices (`/api/v1/invoices`)

| Endpoint | Method | Chức năng | Auth Required | Role Required |
|----------|--------|-----------|---------------|---------------|
| `/` | GET | Danh sách hóa đơn | ✅ | All roles |
| `/create` | POST | Tạo hóa đơn từ order | ✅ | Admin/Accountant |
| `/{invoice_id}` | GET | Chi tiết hóa đơn | ✅ | All roles |
| `/{invoice_id}/pdf` | GET | Download PDF hóa đơn | ✅ | All roles |
| `/{invoice_id}/send-email` | POST | Gửi hóa đơn qua email | ✅ | Admin/Accountant |
| `/bulk-create` | POST | Tạo hàng loạt hóa đơn | ✅ | Admin/Accountant |

**Invoice Integration:**
- Tích hợp với nhà cung cấp HĐĐT
- Tạo XML theo chuẩn Nghị định 123/2020
- Tự động gửi email sau khi tạo

---

### 📊 Dashboard & Reports (`/api/v1/dashboard`)

| Endpoint | Method | Chức năng | Auth Required | Role Required |
|----------|--------|-----------|---------------|---------------|
| `/admin` | GET | Dashboard Admin | ✅ | Admin |
| `/accountant` | GET | Dashboard Kế toán | ✅ | Accountant |
| `/teacher` | GET | Dashboard Giáo vụ | ✅ | Teacher |
| `/parent` | GET | Dashboard Phụ huynh | ✅ | Parent |
| `/revenue-report` | GET | Báo cáo doanh thu | ✅ | Admin/Accountant |
| `/collection-report` | GET | Báo cáo thu học phí | ✅ | Admin/Accountant/Teacher |
| `/outstanding-report` | GET | Báo cáo công nợ | ✅ | Admin/Accountant |

**Dashboard Features:**
- **Admin**: Tổng quan toàn hệ thống, thống kê doanh thu, user activity
- **Accountant**: Báo cáo tài chính, hóa đơn, thanh toán
- **Teacher**: Thống kê học phí theo lớp, danh sách nợ
- **Parent**: Thông tin học phí con em, lịch sử thanh toán

---

### 🖨️ Print Management (`/api/v1/print`)

| Endpoint | Method | Chức năng | Auth Required | Role Required |
|----------|--------|-----------|---------------|---------------|
| `/printers` | GET | Danh sách máy in | ✅ | Admin/Accountant |
| `/printers` | POST | Đăng ký máy in mới | ✅ | Admin |
| `/printers/discover` | GET | Tự động phát hiện máy in | ✅ | Admin |
| `/jobs` | GET | Danh sách job in | ✅ | Admin/Accountant |
| `/jobs` | POST | Tạo job in hóa đơn | ✅ | Admin/Accountant |
| `/agents` | GET | Danh sách Print Agent | ✅ | Admin |
| `/agents` | POST | Đăng ký Print Agent | ✅ | Admin |

**Print System:**
- **Local Printing**: In trực tiếp qua CUPS (Linux) 
- **Remote Printing**: Qua Print Agent trên máy tính từ xa
- **Queue Management**: Theo dõi trạng thái job in

---

## 🔒 Authentication & Authorization

### JWT Token Structure
```json
{
  "sub": "user@email.com",
  "user_id": 123,
  "role": "admin|accountant|teacher|parent",
  "exp": 1640995200
}
```

### Role Permissions

| Role | Users | Students | Orders | Payments | Invoices | Dashboard | Print |
|------|-------|----------|--------|----------|----------|-----------|-------|
| **Admin** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Accountant** | ❌ | ✅ Read | ✅ Manage | ✅ Verify | ✅ Create | ✅ Finance | ✅ Print |
| **Teacher** | ❌ | ✅ Manage | ✅ Create | ❌ | ❌ | ✅ Class | ❌ |
| **Parent** | ❌ | ✅ Own Only | ✅ Read Own | ✅ Pay | ✅ Read Own | ✅ Own | ❌ |

---

## 📝 Standard Response Format

### Success Response
```json
{
  "success": true,
  "message": "Thành công",
  "data": { /* response data */ },
  "meta": { /* pagination, etc */ }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Lỗi mô tả",
  "details": { /* error details */ },
  "error_type": "ValidationError"
}
```

### Paginated Response
```json
{
  "success": true,
  "message": "Thành công",
  "data": [ /* array of items */ ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 10,
    "total_pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 🔧 Cấu hình kỹ thuật

### Base URLs
- **Development**: `http://localhost:5000`
- **Production**: `https://your-domain.replit.app`

### Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`

### Rate Limiting
- **General**: 100 requests/minute
- **Auth**: 10 requests/minute
- **File Upload**: 5 requests/minute

### File Upload Limits
- **Max File Size**: 10MB
- **Allowed Types**: PDF, PNG, JPG, XLSX

---

## 🚀 Cải tiến so với phiên bản cũ

### ✅ Cấu trúc mới
- **API Versioning**: `/api/v1/` prefix
- **Modular Architecture**: Core modules (config, dependencies, security, responses)
- **Centralized Exception Handling**: Consistent error responses
- **Improved Dependencies**: Reusable auth, db dependencies

### ✅ Security Enhancements
- **CORS**: Restricted to Replit domains
- **JWT**: Secure token management with expiration
- **Role-based Access**: Fine-grained permissions
- **Input Validation**: Pydantic schemas

### ✅ Developer Experience
- **Auto Documentation**: Swagger UI with full schemas
- **Type Safety**: Full TypeScript-like type hints
- **Error Details**: Detailed error responses with context
- **Response Standardization**: Consistent API format

### ✅ Production Ready
- **Config Management**: Environment-based settings
- **Logging**: Structured logging system
- **Health Checks**: Monitoring endpoints
- **Database**: Optimized connection handling

---

*Tài liệu này được tạo tự động từ cấu trúc API đã được tối ưu hóa theo chuẩn FastAPI best practices.*