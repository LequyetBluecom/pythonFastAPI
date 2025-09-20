#!/usr/bin/env python3
"""
Script sửa MySQL enum để chấp nhận ADMIN
"""

from app.database import SessionLocal
from sqlalchemy import text

def fix_mysql_enum():
    """Sửa MySQL enum"""
    print("🔧 Đang sửa MySQL enum...")
    
    db = SessionLocal()
    try:
        # Sửa enum để chấp nhận ADMIN
        db.execute(text("""
            ALTER TABLE users 
            MODIFY COLUMN role ENUM('ADMIN', 'ACCOUNTANT', 'TEACHER', 'PARENT') NOT NULL
        """))
        db.commit()
        print("✅ MySQL enum đã được sửa")
        
        # Kiểm tra
        result = db.execute(text("SHOW COLUMNS FROM users LIKE 'role'"))
        role_column = result.fetchone()
        print(f"   Role column: {role_column}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def update_admin_role():
    """Cập nhật role admin"""
    print("🔧 Đang cập nhật role admin...")
    
    db = SessionLocal()
    try:
        # Cập nhật role
        db.execute(text("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@school.com'"))
        db.commit()
        print("✅ Role admin đã được cập nhật")
        
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
    if fix_mysql_enum():
        update_admin_role()
