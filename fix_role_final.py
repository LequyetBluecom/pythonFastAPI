#!/usr/bin/env python3
"""
Script sửa role cuối cùng
"""

from app.database import SessionLocal
from sqlalchemy import text

def fix_role():
    """Sửa role trong database"""
    print("🔧 Đang sửa role trong database...")
    
    db = SessionLocal()
    try:
        # Cập nhật role từ 'admin' thành 'ADMIN'
        result = db.execute(text("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@school.com'"))
        db.commit()
        
        print("✅ Role đã được cập nhật")
        
        # Kiểm tra
        check_result = db.execute(text("SELECT role FROM users WHERE email = 'admin@school.com'"))
        role = check_result.fetchone()
        print(f"   Current role: '{role[0]}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    fix_role()
