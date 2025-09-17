"""
API v1 router aggregation
"""
from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.students import router as students_router
from app.api.v1.endpoints.orders import router as orders_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.invoices import router as invoices_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.print_management import router as print_management_router

api_router = APIRouter()

# API v1 index route
@api_router.get("/", tags=["Meta"])
def api_v1_index():
    """API v1 index endpoint"""
    return {
        "status": "ok", 
        "version": "v1",
        "message": "Hệ thống Thanh toán QR Trường học API v1",
        "endpoints": {
            "auth": "/api/v1/auth/",
            "users": "/api/v1/users/",
            "students": "/api/v1/students/",
            "orders": "/api/v1/orders/",
            "payments": "/api/v1/payments/",
            "invoices": "/api/v1/invoices/",
            "dashboard": "/api/v1/dashboard/",
            "print": "/api/v1/print/"
        }
    }

# Include all endpoint routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(students_router, prefix="/students", tags=["Students"])
api_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_router.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard & Reports"])
api_router.include_router(print_management_router, prefix="/print", tags=["Print Management"])