from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models import User, Student, Order, UserRole, OrderStatus
from app.schemas import OrderCreate, OrderResponse
import uuid

router = APIRouter()

@router.get("/", response_model=List[OrderResponse])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách đơn hàng"""
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem đơn hàng của học sinh mình
        orders = db.query(Order).join(Student).filter(
            Student.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    else:
        # Admin, kế toán, giáo vụ xem được tất cả
        orders = db.query(Order).offset(skip).limit(limit).all()
    
    return orders

@router.post("/", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo đơn hàng mới"""
    # Chỉ admin và giáo vụ có thể tạo đơn hàng
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và giáo vụ mới có quyền tạo đơn hàng"
        )
    
    # Kiểm tra học sinh tồn tại
    student = db.query(Student).filter(Student.id == order_data.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy học sinh"
        )
    
    # Tạo mã đơn hàng duy nhất
    order_code = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    # Tạo đơn hàng mới
    db_order = Order(
        student_id=order_data.student_id,
        order_code=order_code,
        description=order_data.description,
        amount=order_data.amount,
        due_date=order_data.due_date,
        status=OrderStatus.PENDING
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy thông tin đơn hàng theo ID"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn hàng"
        )
    
    # Kiểm tra quyền truy cập
    if current_user.role == UserRole.PARENT:
        student = db.query(Student).filter(Student.id == order.student_id).first()
        if student and student.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền xem đơn hàng này"
            )
    
    return order