from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Student, UserRole
from app.schemas import StudentCreate, StudentResponse
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[StudentResponse])
def get_students(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách học sinh"""
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem được học sinh của mình
        students = db.query(Student).filter(Student.user_id == current_user.id).all()
    else:
        # Admin, kế toán, giáo vụ xem được tất cả
        students = db.query(Student).offset(skip).limit(limit).all()
    
    return students

@router.post("/", response_model=StudentResponse)
def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo học sinh mới"""
    # Chỉ admin và giáo vụ có thể tạo học sinh
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và giáo vụ mới có quyền tạo học sinh"
        )
    
    # Kiểm tra mã học sinh đã tồn tại
    existing_student = db.query(Student).filter(
        Student.student_code == student_data.student_code
    ).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã học sinh đã tồn tại"
        )
    
    # Kiểm tra phụ huynh tồn tại
    parent = db.query(User).filter(User.id == student_data.user_id).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phụ huynh"
        )
    
    # Tạo học sinh mới
    db_student = Student(
        name=student_data.name,
        student_code=student_data.student_code,
        class_name=student_data.class_name,
        grade=student_data.grade,
        user_id=student_data.user_id
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy thông tin học sinh theo ID"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy học sinh"
        )
    
    # Kiểm tra quyền truy cập
    if current_user.role == UserRole.PARENT and student.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không có quyền xem thông tin học sinh này"
        )
    
    return student