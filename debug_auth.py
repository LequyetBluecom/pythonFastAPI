#!/usr/bin/env python3
"""
Script debug authentication
"""

from app.database import SessionLocal
from sqlalchemy import text
from app.models import User, UserRole

def debug_admin():
    """Debug admin user"""
    print("🔍 Đang debug admin user...")
    
    db = SessionLocal()
    try:
        # Lấy admin user
        admin = db.query(User).filter(User.email == "admin@school.com").first()
        
        if admin:
            print(f"✅ Admin user found:")
            print(f"   ID: {admin.id}")
            print(f"   Name: {admin.name}")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role}")
            print(f"   Role type: {type(admin.role)}")
            print(f"   Role value: {admin.role.value if hasattr(admin.role, 'value') else 'No value'}")
            print(f"   UserRole.ADMIN: {UserRole.ADMIN}")
            print(f"   UserRole.ADMIN type: {type(UserRole.ADMIN)}")
            print(f"   UserRole.ADMIN value: {UserRole.ADMIN.value}")
            print(f"   Comparison: {admin.role == UserRole.ADMIN}")
            print(f"   Is active: {admin.is_active}")
        else:
            print("❌ Admin user not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def test_password():
    """Test password verification"""
    print("\n🔐 Đang test password...")
    
    from app.core.security import verify_password
    
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@school.com").first()
        if admin:
            password = "admin123"
            is_valid = verify_password(password, admin.hashed_password)
            print(f"   Password 'admin123' valid: {is_valid}")
            print(f"   Hashed password: {admin.hashed_password[:50]}...")
        else:
            print("❌ Admin not found")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_admin()
    test_password()
