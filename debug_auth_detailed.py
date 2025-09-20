#!/usr/bin/env python3
"""
Script debug authentication chi tiết
"""

from app.database import SessionLocal
from sqlalchemy import text
from app.models import User, UserRole

def debug_database():
    """Debug database"""
    print("🔍 Đang debug database...")
    
    db = SessionLocal()
    try:
        # Kiểm tra user trong database
        result = db.execute(text("SELECT id, name, email, role FROM users WHERE email = 'admin@school.com'"))
        user_data = result.fetchone()
        
        if user_data:
            print(f"✅ User found in database:")
            print(f"   ID: {user_data[0]}")
            print(f"   Name: {user_data[1]}")
            print(f"   Email: {user_data[2]}")
            print(f"   Role: '{user_data[3]}' (type: {type(user_data[3])})")
        else:
            print("❌ User not found in database")
            return False
        
        # Kiểm tra với SQLAlchemy ORM
        print("\n🔍 Đang kiểm tra với SQLAlchemy ORM...")
        try:
            user = db.query(User).filter(User.email == "admin@school.com").first()
            if user:
                print(f"✅ User found via ORM:")
                print(f"   ID: {user.id}")
                print(f"   Name: {user.name}")
                print(f"   Email: {user.email}")
                print(f"   Role: {user.role}")
                print(f"   Role type: {type(user.role)}")
                print(f"   Role == UserRole.ADMIN: {user.role == UserRole.ADMIN}")
                print(f"   UserRole.ADMIN: {UserRole.ADMIN}")
                print(f"   UserRole.ADMIN.value: {UserRole.ADMIN.value}")
            else:
                print("❌ User not found via ORM")
        except Exception as e:
            print(f"❌ Error with ORM: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        db.close()

def test_password_hash():
    """Test password hash"""
    print("\n🔐 Đang test password hash...")
    
    from app.core.security import verify_password
    
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT hashed_password FROM users WHERE email = 'admin@school.com'"))
        hashed = result.fetchone()
        
        if hashed:
            password = "admin123"
            is_valid = verify_password(password, hashed[0])
            print(f"   Password 'admin123' valid: {is_valid}")
            print(f"   Hash: {hashed[0][:50]}...")
        else:
            print("❌ No password hash found")
    except Exception as e:
        print(f"❌ Password error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_database()
    test_password_hash()
