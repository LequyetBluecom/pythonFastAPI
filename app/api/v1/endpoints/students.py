from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.responses import paginated_response
from app.core.dependencies import get_db, get_current_user
from app.models import User, Student, UserRole
from app.schemas import StudentCreate, StudentResponse

router = APIRouter()

@router.get("/")
def get_students(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách học sinh"""
    query = db.query(Student)
    if q:
        like = f"%{q}%"
        query = query.filter((Student.name.ilike(like)) | (Student.student_code.ilike(like)) | (Student.class_name.ilike(like)))
    if current_user.role == UserRole.PARENT:
        # Phụ huynh chỉ xem được học sinh của mình
        query = query.filter(Student.user_id == current_user.id)
    total = query.count()
    data = query.offset(skip).limit(limit).all()
    return paginated_response(data=data, total=total, page=(skip // max(limit,1)) + 1, per_page=limit)

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

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_data: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy học sinh")
    student.name = student_data.name
    student.student_code = student_data.student_code
    student.class_name = student_data.class_name
    student.grade = student_data.grade
    student.user_id = student_data.user_id
    db.commit()
    db.refresh(student)
    return student

@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy học sinh")
    db.delete(student)
    db.commit()
    return {"message": "Đã xóa học sinh"}