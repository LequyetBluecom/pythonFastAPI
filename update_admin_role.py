#!/usr/bin/env python3
"""
Script cập nhật role admin
"""

from app.database import SessionLocal
from sqlalchemy import text

def update_admin_role():
    """Cập nhật role admin"""
    print("🔧 Đang cập nhật role admin...")
    
    db = SessionLocal()
    try:
        # Cập nhật role
        db.execute(text("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@school.com'"))
        db.commit()
        print("✅ Role đã được cập nhật")
        
        # Kiểm tra
        result = db.execute(text("SELECT role FROM users WHERE email = 'admin@school.com'"))
        role = result.fetchone()
        print(f"   Current role: {role[0] if role else 'Not found'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_role()
