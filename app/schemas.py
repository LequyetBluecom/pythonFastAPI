from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models import UserRole, OrderStatus, PaymentStatus

# Base schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Student schemas
class StudentBase(BaseModel):
    name: str
    student_code: str
    class_name: str
    grade: Optional[str] = None

class StudentCreate(StudentBase):
    user_id: int

class StudentResponse(StudentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Order schemas
class OrderBase(BaseModel):
    description: str
    amount: Decimal
    due_date: Optional[datetime] = None

class OrderCreate(OrderBase):
    student_id: int

class OrderResponse(OrderBase):
    id: int
    student_id: int
    order_code: str
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True

# Payment schemas
class PaymentCreate(BaseModel):
    order_id: int
    amount: Decimal
    payment_method: str = "QR_CODE"

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    payment_code: str
    amount: Decimal
    status: PaymentStatus
    qr_code_data: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Invoice schemas
class InvoiceResponse(BaseModel):
    id: int
    order_id: int
    invoice_number: str
    invoice_code: Optional[str] = None
    customer_name: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    issued_at: datetime

    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# QR Code response
class QRCodeResponse(BaseModel):
    payment_id: int
    qr_code_data: str
    amount: Decimal
    order_code: str