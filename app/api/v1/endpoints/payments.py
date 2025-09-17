from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models import User, Order, Payment, UserRole, PaymentStatus, OrderStatus
from app.schemas import PaymentCreate, PaymentResponse, QRCodeResponse
from app.services.payment_service import PaymentService
from app.services.email_service import EmailService
import uuid
from decimal import Decimal

router = APIRouter()

@router.post("/create-qr", response_model=QRCodeResponse)
def create_qr_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo QR code cho thanh toán sử dụng PaymentService"""
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
    
    try:
        # Sử dụng PaymentService để tạo thanh toán
        payment_service = PaymentService(db)
        payment_response = payment_service.create_payment_request(
            order_id=payment_data.order_id,
            amount=payment_data.amount
        )
        
        return QRCodeResponse(
            payment_id=payment_response["payment_id"],
            qr_code_data=payment_response["qr_code_image"],
            amount=payment_data.amount,
            order_code=payment_response["order_code"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tạo thanh toán"
        )

@router.post("/webhook")
def payment_webhook(webhook_data: dict, db: Session = Depends(get_db)):
    """Webhook nhận thông báo thanh toán từ cổng thanh toán"""
    try:
        # Sử dụng PaymentService để xử lý webhook
        payment_service = PaymentService(db)
        success = payment_service.process_webhook(webhook_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xử lý webhook"
            )
        
        # Nếu thanh toán thành công, gửi email thông báo
        if webhook_data.get("status") == "success":
            try:
                payment = db.query(Payment).filter(
                    Payment.payment_code == webhook_data.get("payment_code")
                ).first()
                
                if payment:
                    order = db.query(Order).filter(Order.id == payment.order_id).first()
                    if order:
                        from app.models import Student
                        student = db.query(Student).filter(Student.id == order.student_id).first()
                        parent = db.query(User).filter(User.id == student.user_id).first()
                        
                        # Gửi email xác nhận thanh toán
                        email_service = EmailService()
                        email_service.send_payment_confirmation(
                            recipient_email=parent.email,
                            recipient_name=parent.name,
                            payment_data={
                                'payment_code': payment.payment_code,
                                'amount': payment.amount,
                                'student_name': student.name,
                                'description': order.description,
                                'paid_at': payment.paid_at.strftime('%d/%m/%Y %H:%M') if payment.paid_at else None
                            }
                        )
            except Exception as email_error:
                # Log error nhưng không fail webhook
                print(f"Error sending payment confirmation email: {email_error}")
        
        return {"message": "Webhook xử lý thành công"}
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi xử lý webhook"
        )

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