"""
Standardized API response formats
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Paginated response format"""
    success: bool = True
    message: str = "Success"
    data: List[Any] = []
    meta: Dict[str, Any] = {
        "total": 0,
        "page": 1,
        "per_page": 10,
        "total_pages": 0,
        "has_next": False,
        "has_prev": False
    }


class ErrorResponse(BaseModel):
    """Error response format"""
    success: bool = False
    message: str
    details: Optional[Dict[str, Any]] = None
    error_type: Optional[str] = None


def success_response(
    data: Any = None,
    message: str = "Thành công",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create success response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": meta
    }


def error_response(
    message: str,
    details: Optional[Dict[str, Any]] = None,
    error_type: Optional[str] = None
) -> Dict[str, Any]:
    """Create error response"""
    return {
        "success": False,
        "message": message,
        "details": details,
        "error_type": error_type
    }


def paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    per_page: int = 10,
    message: str = "Thành công"
) -> Dict[str, Any]:
    """Create paginated response"""
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


def created_response(
    data: Any = None,
    message: str = "Tạo mới thành công"
) -> Dict[str, Any]:
    """Create 201 Created response"""
    return success_response(data=data, message=message)


def updated_response(
    data: Any = None,
    message: str = "Cập nhật thành công"
) -> Dict[str, Any]:
    """Create update success response"""
    return success_response(data=data, message=message)


def deleted_response(
    message: str = "Xóa thành công"
) -> Dict[str, Any]:
    """Create delete success response"""
    return success_response(message=message)