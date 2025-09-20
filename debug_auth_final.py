#!/usr/bin/env python3
"""
Script debug authentication cuối cùng
"""

from app.database import SessionLocal
from sqlalchemy import text
from app.models import User, UserRole

def debug_auth_logic():
    """Debug logic authentication"""
    print("🔍 Đang debug logic authentication...")
    
    db = SessionLocal()
    try:
        # Lấy user từ database
        user = db.query(User).filter(User.email == "admin@school.com").first()
        
        if user:
            print(f"✅ User found:")
            print(f"   ID: {user.id}")
            print(f"   Name: {user.name}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Role type: {type(user.role)}")
            print(f"   Role value: {user.role.value if hasattr(user.role, 'value') else 'No value'}")
            print(f"   UserRole.ADMIN: {UserRole.ADMIN}")
            print(f"   UserRole.ADMIN type: {type(UserRole.ADMIN)}")
            print(f"   UserRole.ADMIN value: {UserRole.ADMIN.value}")
            print(f"   user.role == UserRole.ADMIN: {user.role == UserRole.ADMIN}")
            print(f"   str(user.role) == str(UserRole.ADMIN): {str(user.role) == str(UserRole.ADMIN)}")
            print(f"   user.role.value == UserRole.ADMIN.value: {user.role.value == UserRole.ADMIN.value}")
            print(f"   Is active: {user.is_active}")
        else:
            print("❌ User not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def test_password_verification():
    """Test password verification"""
    print("\n🔐 Đang test password verification...")
    
    from app.core.security import verify_password
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@school.com").first()
        if user:
            password = "admin123"
            is_valid = verify_password(password, user.hashed_password)
            print(f"   Password 'admin123' valid: {is_valid}")
            print(f"   Hashed password: {user.hashed_password[:50]}...")
        else:
            print("❌ User not found")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_auth_logic()
    test_password_verification()
