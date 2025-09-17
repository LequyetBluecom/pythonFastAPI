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

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app with settings
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Add exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS middleware  
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https://.*\.replit\.(app|dev)$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
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
