from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.dependencies import get_db, get_current_user
from app.core.security import verify_password, create_access_token, get_password_hash, verify_token
from app.core.responses import success_response, created_response, error_response
from app.models import User, UserRole
from app.schemas import LoginRequest, Token, UserCreate, UserResponse

router = APIRouter()

@router.post("/login", summary="Cấp token (Admin)", description="Đăng nhập bằng tài khoản Admin để nhận Bearer token. Tất cả API khác yêu cầu token này.", openapi_extra={
    "x-codeSamples": [
        {
            "lang": "cURL",
            "source": "curl -X POST 'http://localhost:5000/api/v1/auth/login' -H 'Content-Type: application/json' -d '{\n  \"email\": \"user@example.com\",\n  \"password\": \"your-password\"\n}'"
        },
        {
            "lang": "JavaScript (fetch)",
            "source": "fetch('http://localhost:5000/api/v1/auth/login', {\n  method: 'POST',\n  headers: { 'Content-Type': 'application/json' },\n  body: JSON.stringify({ email: 'user@example.com', password: 'your-password' })\n}).then(r => r.json()).then(console.log);"
        },
        {
            "lang": "PHP (cURL)",
            "source": "$ch = curl_init('http://localhost:5000/api/v1/auth/login');\n$data = json_encode(['email' => 'user@example.com', 'password' => 'your-password']);\ncurl_setopt_array($ch, [\n  CURLOPT_POST => true,\n  CURLOPT_HTTPHEADER => ['Content-Type: application/json'],\n  CURLOPT_POSTFIELDS => $data,\n  CURLOPT_RETURNTRANSFER => true\n]);\n$resp = curl_exec($ch);\ncurl_close($ch);\necho $resp;"
        }
    ]
})
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập và trả về access token"""
    # Chỉ cho phép Admin lấy token hệ thống
    admin = db.query(User).filter(User.email == request.email).first()
    if not admin or admin.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Admin được phép lấy token")
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản đã bị vô hiệu hóa"
        )
    
    from app.core.config import settings
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return success_response(
        data={"access_token": access_token, "token_type": "bearer"},
        message="Đăng nhập thành công"
    )

@router.post("/register", summary="Đăng ký phụ huynh", description="Tạo tài khoản với vai trò phụ huynh (parent). Admin/staff tạo qua kênh khác.", openapi_extra={
    "x-codeSamples": [
        {
            "lang": "cURL",
            "source": "curl -X POST 'http://localhost:5000/api/v1/auth/register' -H 'Content-Type: application/json' -d '{\n  \"name\": \"Nguyen Van A\",\n  \"email\": \"parent@example.com\",\n  \"phone\": \"0900000000\",\n  \"password\": \"Secret123!\",\n  \"role\": \"parent\"\n}'"
        },
        {
            "lang": "JavaScript (fetch)",
            "source": "fetch('http://localhost:5000/api/v1/auth/register', {\n  method: 'POST',\n  headers: { 'Content-Type': 'application/json' },\n  body: JSON.stringify({ name: 'Nguyen Van A', email: 'parent@example.com', phone: '0900000000', password: 'Secret123!', role: 'parent' })\n}).then(r => r.json()).then(console.log);"
        },
        {
            "lang": "PHP (cURL)",
            "source": "$ch = curl_init('http://localhost:5000/api/v1/auth/register');\n$data = json_encode(['name'=>'Nguyen Van A','email'=>'parent@example.com','phone'=>'0900000000','password'=>'Secret123!','role'=>'parent']);\ncurl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_HTTPHEADER=>['Content-Type: application/json'], CURLOPT_POSTFIELDS=>$data, CURLOPT_RETURNTRANSFER=>true]);\n$resp = curl_exec($ch); curl_close($ch); echo $resp;"
        }
    ]
})
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký tài khoản phụ huynh mới"""
    # Kiểm tra email đã tồn tại
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng"
        )
    
    # SECURITY: Chỉ cho phép đăng ký với role PARENT
    # Admin và staff được tạo bởi admin thông qua endpoint khác
    if user_data.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ có thể đăng ký với vai trò phụ huynh"
        )
    
    # Tạo user mới
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        role=UserRole.PARENT,  # Force parent role
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Return sanitized user data without password
    user_response = UserResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        phone=db_user.phone,
        role=db_user.role,
        is_active=db_user.is_active,
        created_at=db_user.created_at
    )
    
    return created_response(
        data=user_response,
        message="Đăng ký tài khoản thành công"
    )


@router.get("/me", summary="Thông tin người dùng hiện tại", description="Trả thông tin user từ access token (Bearer).", openapi_extra={
    "x-codeSamples": [
        {
            "lang": "cURL",
            "source": "curl -X GET 'http://localhost:5000/api/v1/auth/me' -H 'Authorization: Bearer <ACCESS_TOKEN>'"
        },
        {
            "lang": "JavaScript (fetch)",
            "source": "fetch('http://localhost:5000/api/v1/auth/me', { headers: { Authorization: 'Bearer <ACCESS_TOKEN>' } }).then(r => r.json()).then(console.log);"
        },
        {
            "lang": "PHP (cURL)",
            "source": "$ch = curl_init('http://localhost:5000/api/v1/auth/me');\ncurl_setopt_array($ch, [CURLOPT_HTTPHEADER=>['Authorization: Bearer <ACCESS_TOKEN>'], CURLOPT_RETURNTRANSFER=>true]);\n$resp = curl_exec($ch); curl_close($ch); echo $resp;"
        }
    ]
})
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Lấy thông tin user hiện tại"""
    # Return sanitized user data
    user_response = UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
    
    return success_response(
        data=user_response,
        message="Thông tin user hiện tại"
    )