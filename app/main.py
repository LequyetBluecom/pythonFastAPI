"""
Main FastAPI application with improved structure
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import (
    AppException, 
    app_exception_handler, 
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.database import Base, engine
from app.api.v1.api import api_router
from app import init as app_init

# Tags metadata to describe groups in Swagger UI
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Đăng nhập, đăng ký, lấy thông tin người dùng hiện tại. Sử dụng Bearer token cho các API bảo vệ.",
    },
    {
        "name": "Users",
        "description": "Quản lý người dùng: danh sách, tạo mới (chỉ admin), xem chi tiết.",
    },
    {
        "name": "Students",
        "description": "Quản lý học sinh: gắn với phụ huynh (user role parent), xem/tra cứu.",
    },
    {
        "name": "Orders",
        "description": "Đơn hàng/phiếu thu học phí cho học sinh, trạng thái pending/paid/invoiced.",
    },
    {
        "name": "Payments",
        "description": "Tạo QR thanh toán, nhận webhook, truy vấn giao dịch.",
    },
    {
        "name": "Invoices",
        "description": "Phát hành hóa đơn điện tử, tải PDF/XML, tra cứu.",
    },
    {
        "name": "Dashboard & Reports",
        "description": "Báo cáo tổng hợp, đối soát, thống kê theo thời gian.",
    },
    {
        "name": "Print Management",
        "description": "Quản lý máy in và lệnh in hóa đơn/phiếu.",
    },
]

# Create database tables
Base.metadata.create_all(bind=engine)
app_init.ensure_default_admin()

# Initialize FastAPI app with settings
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
        # Enable request snippets (Swagger UI plugin) for quick copy-paste
        "requestSnippetsEnabled": True,
        "requestSnippets": [
            {"generator": "curl", "title": "cURL", "syntax": "bash"},
            {"generator": "javascript", "title": "JavaScript (fetch)", "syntax": "javascript"},
            {"generator": "javascript-axios", "title": "JavaScript (axios)", "syntax": "javascript"}
            # PHP can use the cURL snippet directly in php-curl
        ],
        "syntaxHighlight": {"activated": True, "theme": "monokai"}
    }
)

# Add exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS middleware (env-driven)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")

# Route chính
@app.get("/")
def read_root():
    return {
        "message": "Hệ thống Thanh toán QR Trường học 🏫",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "Thanh toán QR code",
            "Hóa đơn điện tử",
            "Quản lý học sinh",
            "Báo cáo đối soát"
        ]
    }

# Health check endpoint
@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "school-payment-system"}

# Production server entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
