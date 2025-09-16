from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ACCOUNTANT = "accountant"  # Kế toán
    TEACHER = "teacher"        # Giáo vụ
    PARENT = "parent"          # Phụ huynh

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    INVOICED = "invoiced"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    role = Column(Enum(UserRole), nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Quan hệ với học sinh (nếu là phụ huynh)
    students = relationship("Student", back_populates="parent")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ID phụ huynh
    name = Column(String(100), nullable=False)
    student_code = Column(String(20), unique=True, nullable=False)
    class_name = Column(String(50), nullable=False)
    grade = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Quan hệ
    parent = relationship("User", back_populates="students")
    orders = relationship("Order", back_populates="student")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    order_code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=False)  # Mô tả khoản phí
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    
    # Quan hệ
    student = relationship("Student", back_populates="orders")
    payments = relationship("Payment", back_populates="order")
    invoice = relationship("Invoice", back_populates="order", uselist=False)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    payment_code = Column(String(100), unique=True, nullable=False)
    gateway_txn_id = Column(String(100))  # ID từ cổng thanh toán
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(50))  # QR_CODE, BANK_TRANSFER, etc.
    qr_code_data = Column(Text)  # Dữ liệu QR code
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Quan hệ
    order = relationship("Order", back_populates="payments")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_code = Column(String(100))  # Mã hóa đơn từ cơ quan thuế
    e_invoice_code = Column(String(100))  # Mã hóa đơn điện tử
    
    # Thông tin hóa đơn
    customer_name = Column(String(100), nullable=False)
    customer_tax_code = Column(String(20))
    customer_address = Column(String(255))
    
    amount = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    # File paths
    pdf_path = Column(String(255))  # Đường dẫn file PDF
    xml_path = Column(String(255))  # Đường dẫn file XML gốc
    
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Quan hệ
    order = relationship("Order", back_populates="invoice")

class Printer(Base):
    __tablename__ = "printers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))
    ip_address = Column(String(50))
    printer_type = Column(String(50))  # THERMAL, LASER, etc.
    agent_id = Column(Integer, ForeignKey("printer_agents.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Quan hệ
    agent = relationship("PrinterAgent", back_populates="printers")
    print_jobs = relationship("PrintJob", back_populates="printer")

class PrinterAgent(Base):
    __tablename__ = "printer_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(String(100), unique=True, nullable=False)
    host_name = Column(String(100))
    jwt_token = Column(String(500))
    last_seen = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Quan hệ
    printers = relationship("Printer", back_populates="agent")

class PrintJob(Base):
    __tablename__ = "print_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    printer_id = Column(Integer, ForeignKey("printers.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    job_data = Column(Text)  # Dữ liệu in (HTML, PDF base64, etc.)
    status = Column(String(20), default="pending")  # pending, sent, completed, failed
    sent_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Quan hệ
    printer = relationship("Printer", back_populates="print_jobs")
    invoice = relationship("Invoice")