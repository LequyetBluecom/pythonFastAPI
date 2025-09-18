from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from app.core.responses import paginated_response
from fastapi import Request
from app.core.dependencies import get_db, get_current_user, rate_limiter
from app.models import User, Order, Payment, UserRole, PaymentStatus, OrderStatus
from app.schemas import PaymentCreate, PaymentResponse, QRCodeResponse
from app.services.payment_service import PaymentService
from app.services.email_service import EmailService
import uuid
from decimal import Decimal

router = APIRouter()

@router.post(
    "/create-qr",
    response_model=QRCodeResponse,
    summary="Tạo QR thanh toán",
    description="Sinh mã QR để phụ huynh quét và thanh toán học phí cho đơn hàng.",
    openapi_extra={
        "x-codeSamples": [
            {
                "lang": "cURL",
                "source": "curl -X POST 'http://localhost:5000/api/v1/payments/create-qr' -H 'Authorization: Bearer <ACCESS_TOKEN>' -H 'Content-Type: application/json' -d '{\\n  \\\"order_id\\\": 1,\\n  \\\"amount\\\": 100000\\n}'"
            },
            {
                "lang": "JavaScript (fetch)",
                "source": "fetch('http://localhost:5000/api/v1/payments/create-qr', { method: 'POST', headers: { 'Authorization': 'Bearer <ACCESS_TOKEN>', 'Content-Type': 'application/json' }, body: JSON.stringify({ order_id: 1, amount: 100000 }) }).then(r => r.json()).then(console.log);"
            },
            {
                "lang": "PHP (cURL)",
                "source": "$ch = curl_init('http://localhost:5000/api/v1/payments/create-qr');\\n$payload = json_encode(['order_id'=>1,'amount'=>100000]);\\ncurl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_HTTPHEADER=>['Authorization: Bearer <ACCESS_TOKEN>','Content-Type: application/json'], CURLOPT_POSTFIELDS=>$payload, CURLOPT_RETURNTRANSFER=>true]);\\n$resp = curl_exec($ch); curl_close($ch); echo $resp;"
            }
        ]
    }
)
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

@router.post(
    "/webhook",
    summary="Webhook thanh toán",
    description="Cổng thanh toán gọi vào endpoint này để báo kết quả giao dịch (server-to-server).",
    openapi_extra={
        "x-codeSamples": [
            {
                "lang": "cURL",
                "source": "curl -X POST 'http://localhost:5000/api/v1/payments/webhook' -H 'Content-Type: application/json' -d '{\\n  \\\"transaction_id\\\": \\\"TXN-XXXX\\\",\\n  \\\"status\\\": \\\"success\\\"\\n}'"
            }
        ]
    }
)
def payment_webhook(webhook_data: dict, request: Request, db: Session = Depends(get_db), _: bool = Depends(rate_limiter(limit=60, window_seconds=60))):
    """Webhook nhận thông báo thanh toán từ cổng thanh toán"""
    try:
        # Verify signature header
        signature = request.headers.get("X-Signature", "")
        if not PaymentService(db).gateway.verify_webhook(webhook_data, signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
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

@router.get(
    "/",
    summary="Danh sách thanh toán",
    description="Trả về danh sách giao dịch thanh toán. Phụ huynh chỉ xem được giao dịch của con mình."
)
def get_payments(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách thanh toán"""
    query = db.query(Payment)
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    if q:
        query = query.filter(Payment.payment_code.ilike(f"%{q}%"))
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem thanh toán của học sinh mình
        from app.models import Student
        query = query.join(Order).join(Student).filter(Student.user_id == current_user.id)
    total = query.count()
    data = query.offset(skip).limit(limit).all()
    return paginated_response(data=data, total=total, page=(skip // max(limit,1)) + 1, per_page=limit)

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Chi tiết thanh toán",
    description="Trả thông tin chi tiết của một giao dịch thanh toán."
)
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


@router.post("/{payment_id}/confirm", summary="Xác nhận thanh toán thủ công")
def manual_confirm_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy giao dịch")
    if payment.status == PaymentStatus.SUCCESS:
        return {"message": "Giao dịch đã ở trạng thái thành công"}
    payment.status = PaymentStatus.SUCCESS
    payment.paid_at = func.now()
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if order and order.status == OrderStatus.PENDING:
        order.status = OrderStatus.PAID
    db.commit()
    return {"message": "Đã xác nhận thanh toán thành công"}


@router.post("/{payment_id}/refund", summary="Hoàn tiền (mock)")
def refund_payment_mock(
    payment_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy giao dịch")
    payment.status = PaymentStatus.FAILED
    note = f"REFUND:{reason or 'manual'}"
    payment.gateway_txn_id = (payment.gateway_txn_id or '') + (f"|{note}" if payment.gateway_txn_id else note)
    db.commit()
    return {"message": "Đã đánh dấu hoàn tiền (mock)"}