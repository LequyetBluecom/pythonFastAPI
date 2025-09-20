#!/usr/bin/env python3
"""
Script sửa role của admin user
"""

from app.database import SessionLocal
from sqlalchemy import text

def fix_admin_role():
    """Sửa role của admin user"""
    print("🔧 Đang sửa role của admin user...")
    
    db = SessionLocal()
    try:
        # Cập nhật role từ 'admin' thành 'ADMIN'
        result = db.execute(text("""
            UPDATE users 
            SET role = 'ADMIN' 
            WHERE email = 'admin@school.com'
        """))
        
        db.commit()
        print("✅ Role đã được cập nhật thành 'ADMIN'")
        
        # Kiểm tra lại
        check_result = db.execute(text("SELECT role FROM users WHERE email = 'admin@school.com'"))
        role = check_result.fetchone()
        print(f"   Current role: {role[0] if role else 'Not found'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    fix_admin_role()
