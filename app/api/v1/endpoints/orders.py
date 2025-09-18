from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.responses import paginated_response
from app.core.dependencies import get_db, get_current_user
from app.models import User, Student, Order, UserRole, OrderStatus
from app.schemas import OrderCreate, OrderResponse
import uuid

router = APIRouter()

@router.get("/")
def get_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    class_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách đơn hàng"""
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if class_name:
        query = query.join(Student).filter(Student.class_name == class_name)
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem đơn hàng của học sinh mình
        query = query.join(Student).filter(Student.user_id == current_user.id)
    total = query.count()
    data = query.offset(skip).limit(limit).all()
    return paginated_response(data=data, total=total, page=(skip // max(limit,1)) + 1, per_page=limit)

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

@router.post("/bulk")
def bulk_create_orders(
    orders: List[OrderCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    created = []
    for data in orders:
        student = db.query(Student).filter(Student.id == data.student_id).first()
        if not student:
            continue
        import uuid
        order_code = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        db_order = Order(
            student_id=data.student_id,
            order_code=order_code,
            description=data.description,
            amount=data.amount,
            due_date=data.due_date,
            status=OrderStatus.PENDING
        )
        db.add(db_order)
        created.append(db_order)
    db.commit()
    for o in created:
        db.refresh(o)
    return {"created": len(created), "orders": created}

@router.post("/reminders")
def send_overdue_reminders(
    class_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER, UserRole.ACCOUNTANT]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    from app.services.email_service import EmailService
    from sqlalchemy import and_
    from datetime import datetime
    q = db.query(Order, Student, User).join(Student, Order.student_id == Student.id).join(User, Student.user_id == User.id).filter(
        and_(Order.status == OrderStatus.PENDING, Order.due_date != None, Order.due_date < datetime.now())
    )
    if class_name:
        q = q.filter(Student.class_name == class_name)
    rows = q.all()
    by_parent = {}
    for order, student, parent in rows:
        by_parent.setdefault(parent.email, []).append({
            'parent_email': parent.email,
            'parent_name': parent.name,
            'student_name': student.name,
            'class_name': student.class_name,
            'description': order.description,
            'amount': float(order.amount),
            'due_date': order.due_date.strftime('%d/%m/%Y') if order.due_date else None
        })
    email = EmailService()
    sent = 0
    for parent_email, orders_list in by_parent.items():
        if email.send_payment_reminder([parent_email], orders_list):
            sent += 1
    return {"parents_notified": sent}

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