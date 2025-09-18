from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.responses import paginated_response
from app.core.dependencies import get_db, get_current_user
from app.models import User, Order, Payment, Invoice, UserRole, OrderStatus, PaymentStatus
from app.schemas import InvoiceResponse
from app.services.invoice_service import InvoiceService
from app.services.email_service import EmailService
import os
from datetime import datetime

router = APIRouter()

@router.post("/generate/{order_id}", response_model=InvoiceResponse)
def generate_invoice(
    order_id: int,
    send_email: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Phát hành hóa đơn điện tử cho đơn hàng đã thanh toán"""
    # Chỉ admin và kế toán có thể phát hành hóa đơn
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và kế toán mới có quyền phát hành hóa đơn"
        )
    
    try:
        # Sử dụng InvoiceService để tạo hóa đơn
        invoice_service = InvoiceService(db)
        invoice_result = invoice_service.generate_invoice(order_id)
        
        # Lấy thông tin hóa đơn vừa tạo
        invoice = db.query(Invoice).filter(Invoice.id == invoice_result["invoice_id"]).first()
        
        # Gửi email nếu yêu cầu
        if send_email:
            try:
                from app.models import Student, Order
                order = db.query(Order).filter(Order.id == order_id).first()
                student = db.query(Student).filter(Student.id == order.student_id).first()
                parent = db.query(User).filter(User.id == student.user_id).first()
                
                email_service = EmailService()
                email_service.send_invoice_email(
                    recipient_email=parent.email,
                    recipient_name=parent.name,
                    invoice_data={
                        'invoice_number': invoice.invoice_number,
                        'invoice_code': invoice.invoice_code,
                        'lookup_code': invoice.e_invoice_code,
                        'student_name': student.name,
                        'class_name': student.class_name,
                        'description': order.description,
                        'total_amount': invoice.total_amount
                    },
                    pdf_path=invoice.pdf_path,
                    xml_path=invoice.xml_path
                )
            except Exception as email_error:
                # Log error nhưng không fail việc tạo hóa đơn
                print(f"Error sending invoice email: {email_error}")
        
        return invoice
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error generating invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tạo hóa đơn"
        )

@router.get("/")
def get_invoices(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách hóa đơn"""
    query = db.query(Invoice)
    if q:
        like = f"%{q}%"
        query = query.filter((Invoice.invoice_number.ilike(like)) | (Invoice.e_invoice_code.ilike(like)))
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem hóa đơn của học sinh mình
        from app.models import Student
        query = query.join(Order).join(Student).filter(Student.user_id == current_user.id)
    total = query.count()
    data = query.offset(skip).limit(limit).all()
    return paginated_response(data=data, total=total, page=(skip // max(limit,1)) + 1, per_page=limit)

@router.get("/lookup/{code}")
def lookup_invoice_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter((Invoice.invoice_number == code) | (Invoice.e_invoice_code == code)).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hóa đơn")
    return invoice

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy thông tin hóa đơn theo ID"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hóa đơn"
        )
    
    # Kiểm tra quyền truy cập
    if current_user.role == UserRole.PARENT:
        from app.models import Student
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        if order:
            student = db.query(Student).filter(Student.id == order.student_id).first()
            if student and student.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Không có quyền xem hóa đơn này"
                )
    
    return invoice

@router.post("/{invoice_id}/resend")
def resend_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    try:
        service = InvoiceService(db)
        ok = service.resend_invoice_email(invoice_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể gửi email hóa đơn")
        return {"message": "Đã gửi lại email hóa đơn"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{invoice_id}/rerender")
def rerender_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    try:
        service = InvoiceService(db)
        pdf_path = service.rerender_pdf(invoice_id)
        return {"message": "Đã render lại PDF", "pdf_path": pdf_path}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tải file PDF hóa đơn"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hóa đơn"
        )
    
    # Kiểm tra quyền truy cập tương tự như get_invoice
    if current_user.role == UserRole.PARENT:
        from app.models import Student
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        if order:
            student = db.query(Student).filter(Student.id == order.student_id).first()
            if student and student.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Không có quyền tải hóa đơn này"
                )
    
    # Kiểm tra file PDF có tồn tại không
    if not invoice.pdf_path or not os.path.exists(invoice.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File PDF hóa đơn không tồn tại"
        )
    
    # Trả về file PDF
    return FileResponse(
        path=invoice.pdf_path,
        filename=f"hoadon_{invoice.invoice_number}.pdf",
        media_type="application/pdf"
    )