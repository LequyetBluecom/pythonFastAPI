from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
from app.database import get_db, SessionLocal
from app.models import User, Order, Payment, UserRole, PaymentStatus, OrderStatus
from app.schemas import PaymentCreate, PaymentResponse, QRCodeResponse
from app.routers.auth import get_current_user
import qrcode
import io
import base64
import uuid
from decimal import Decimal

router = APIRouter()

@router.post("/create-qr", response_model=QRCodeResponse)
def create_qr_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo QR code cho thanh toán"""
    # Kiểm tra đơn hàng tồn tại
    order = db.query(Order).filter(Order.id == payment_data.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn hàng"
        )
    
    # Kiểm tra quyền thanh toán (phụ huynh chỉ thanh toán cho con mình)
    if current_user.role == UserRole.PARENT:
        from app.models import Student
        student = db.query(Student).filter(Student.id == order.student_id).first()
        if student and student.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền thanh toán đơn hàng này"
            )
    
    # Kiểm tra đơn hàng chưa được thanh toán
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đơn hàng đã được thanh toán hoặc đã có hóa đơn"
        )
    
    # Tạo mã thanh toán duy nhất
    payment_code = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    
    # Tạo dữ liệu QR code (format đơn giản cho demo)
    qr_data = f"PAYMENT:{payment_code}|AMOUNT:{payment_data.amount}|ORDER:{order.order_code}"
    
    # Tạo QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Convert to base64 string
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Lưu payment record
    db_payment = Payment(
        order_id=payment_data.order_id,
        payment_code=payment_code,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        qr_code_data=qr_data,
        status=PaymentStatus.PENDING
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    return QRCodeResponse(
        payment_id=db_payment.id,
        qr_code_data=f"data:image/png;base64,{qr_code_base64}",
        amount=payment_data.amount,
        order_code=order.order_code
    )

@router.post("/webhook")
def payment_webhook(webhook_data: dict, db: Session = Depends(get_db)):
    """Webhook nhận thông báo thanh toán từ cổng thanh toán"""
    # TODO: Verify webhook signature trong production
    # if not verify_webhook_signature(webhook_data, headers):
    #     raise HTTPException(status_code=401, detail="Invalid signature")
    
    payment_code = webhook_data.get("payment_code")
    webhook_status = webhook_data.get("status")
    
    if not payment_code or not webhook_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dữ liệu webhook không hợp lệ"
        )
    
    # Tìm payment record
    payment = db.query(Payment).filter(Payment.payment_code == payment_code).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy giao dịch thanh toán"
        )
    
    # Kiểm tra idempotency (tránh xử lý trùng lặp)
    if payment.status != PaymentStatus.PENDING:
        return {"message": "Payment already processed", "current_status": payment.status}
    
    # Cập nhật trạng thái thanh toán
    if webhook_status == "success":
        payment.status = PaymentStatus.SUCCESS
        payment.paid_at = func.now()
        
        # Cập nhật trạng thái đơn hàng atomically
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = OrderStatus.PAID
    else:
        payment.status = PaymentStatus.FAILED
    
    db.commit()
    
    return {"message": "Webhook processed successfully"}

@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách thanh toán"""
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem thanh toán của học sinh mình
        from app.models import Student
        payments = db.query(Payment).join(Order).join(Student).filter(
            Student.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    else:
        # Admin, kế toán, giáo vụ xem được tất cả
        payments = db.query(Payment).offset(skip).limit(limit).all()
    
    return payments

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy thông tin thanh toán theo ID"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy giao dịch thanh toán"
        )
    
    # Kiểm tra quyền truy cập
    if current_user.role == UserRole.PARENT:
        from app.models import Student
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            student = db.query(Student).filter(Student.id == order.student_id).first()
            if student and student.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Không có quyền xem giao dịch này"
                )
    
    return payment