import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, get_db
from app.models import Base
from app.routers import auth, users, students, orders, payments, invoices, dashboard, print_management
from fastapi.middleware.cors import CORSMiddleware

# Tạo các bảng trong database
Base.metadata.create_all(bind=engine)

# Khởi tạo app
app = FastAPI(
    title="Hệ thống Thanh toán QR Trường học",
    description="API cho hệ thống thanh toán học phí và phát hành hóa đơn điện tử",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production, chỉ định cụ thể domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard & Reports"])
app.include_router(print_management.router, prefix="/api/print", tags=["Print Management"])

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
