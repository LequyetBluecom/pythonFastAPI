from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Order, Payment, Invoice, UserRole, OrderStatus, PaymentStatus
from app.schemas import InvoiceResponse
from app.routers.auth import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/generate/{order_id}", response_model=InvoiceResponse)
def generate_invoice(
    order_id: int,
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
    
    # Kiểm tra đơn hàng tồn tại và đã thanh toán
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn hàng"
        )
    
    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đơn hàng chưa được thanh toán"
        )
    
    # Kiểm tra đã có hóa đơn chưa
    existing_invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đơn hàng đã có hóa đơn"
        )
    
    # Lấy thông tin học sinh và phụ huynh
    from app.models import Student
    student = db.query(Student).filter(Student.id == order.student_id).first()
    parent = db.query(User).filter(User.id == student.user_id).first()
    
    # Tạo số hóa đơn
    invoice_number = f"HD{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    
    # Tính thuế (giả sử VAT 0% cho học phí)
    tax_amount = 0
    total_amount = order.amount + tax_amount
    
    # Tạo hóa đơn
    db_invoice = Invoice(
        order_id=order_id,
        invoice_number=invoice_number,
        customer_name=parent.name,
        customer_address="",  # Có thể thêm trường địa chỉ vào User model
        amount=order.amount,
        tax_amount=tax_amount,
        total_amount=total_amount
    )
    
    db.add(db_invoice)
    
    # Cập nhật trạng thái đơn hàng
    order.status = OrderStatus.INVOICED
    
    db.commit()
    db.refresh(db_invoice)
    
    # TODO: Ở đây sẽ gọi API nhà cung cấp HĐĐT để phát hành thực tế
    # và lưu file PDF/XML
    
    return db_invoice

@router.get("/", response_model=List[InvoiceResponse])
def get_invoices(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách hóa đơn"""
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem hóa đơn của học sinh mình
        from app.models import Student
        invoices = db.query(Invoice).join(Order).join(Student).filter(
            Student.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    else:
        # Admin, kế toán, giáo vụ xem được tất cả
        invoices = db.query(Invoice).offset(skip).limit(limit).all()
    
    return invoices

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
    
    # TODO: Implement PDF generation using WeasyPrint
    # For now, return a simple response
    return {"message": "PDF generation will be implemented", "invoice_id": invoice_id}