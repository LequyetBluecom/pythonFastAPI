#!/usr/bin/env python3
"""
Script cập nhật role trực tiếp
"""

from app.database import SessionLocal
from sqlalchemy import text

def update_role():
    """Cập nhật role"""
    print("🔧 Đang cập nhật role...")
    
    db = SessionLocal()
    try:
        # Cập nhật role
        db.execute(text("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@school.com'"))
        db.commit()
        print("✅ Role đã được cập nhật")
        
        # Kiểm tra
        result = db.execute(text("SELECT role FROM users WHERE email = 'admin@school.com'"))
        role = result.fetchone()
        print(f"   Role: '{role[0]}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    update_role()
