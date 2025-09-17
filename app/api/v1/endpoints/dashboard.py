"""
Router cho Dashboard và Báo cáo
Cung cấp dữ liệu dashboard cho các role khác nhau
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, UserRole
from app.routers.auth import get_current_user
from app.services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/admin")
def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dashboard cho Admin - tổng quan toàn hệ thống"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền xem dashboard này"
        )
    
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_admin_dashboard()
    except Exception as e:
        print(f"Error getting admin dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tải dashboard"
        )

@router.get("/accountant")
def get_accountant_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dashboard cho Kế toán - tập trung vào hóa đơn và doanh thu"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và kế toán mới có quyền xem dashboard này"
        )
    
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_accountant_dashboard()
    except Exception as e:
        print(f"Error getting accountant dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tải dashboard"
        )

@router.get("/teacher")
def get_teacher_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dashboard cho Giáo vụ - tập trung vào học sinh và khoản phí"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và giáo vụ mới có quyền xem dashboard này"
        )
    
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_teacher_dashboard()
    except Exception as e:
        print(f"Error getting teacher dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tải dashboard"
        )

@router.get("/parent")
def get_parent_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dashboard cho Phụ huynh - chỉ xem thông tin của con mình"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ phụ huynh mới có quyền xem dashboard này"
        )
    
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_parent_dashboard(current_user.id)
    except Exception as e:
        print(f"Error getting parent dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tải dashboard"
        )

@router.get("/reports/revenue")
def get_revenue_report(
    start_date: datetime = Query(..., description="Ngày bắt đầu"),
    end_date: datetime = Query(..., description="Ngày kết thúc"),
    group_by: str = Query("day", description="Nhóm theo: day, week, month"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Báo cáo doanh thu theo khoảng thời gian"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và kế toán mới có quyền xem báo cáo này"
        )
    
    if group_by not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="group_by phải là: day, week, hoặc month"
        )
    
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.generate_revenue_report(start_date, end_date, group_by)
    except Exception as e:
        print(f"Error generating revenue report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tạo báo cáo"
        )

@router.get("/reports/collection")
def get_collection_report(
    class_name: Optional[str] = Query(None, description="Lớp cụ thể (để trống để xem tất cả)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Báo cáo thu học phí theo lớp"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin, giáo vụ và kế toán mới có quyền xem báo cáo này"
        )
    
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_collection_report(class_name)
    except Exception as e:
        print(f"Error generating collection report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tạo báo cáo"
        )