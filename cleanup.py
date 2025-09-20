#!/usr/bin/env python3
"""
Script để dọn dẹp file rác trong dự án FastAPI
Chạy script này định kỳ để giữ dự án sạch sẽ
"""

import os
import shutil
import glob
from pathlib import Path

def clean_python_cache():
    """Xóa tất cả thư mục __pycache__ và file .pyc"""
    print("🧹 Đang xóa Python cache files...")
    
    # Xóa thư mục __pycache__
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_path = os.path.join(root, dir_name)
                print(f"  Xóa: {cache_path}")
                shutil.rmtree(cache_path, ignore_errors=True)
    
    # Xóa file .pyc
    for pyc_file in glob.glob('**/*.pyc', recursive=True):
        print(f"  Xóa: {pyc_file}")
        os.remove(pyc_file)

def clean_temp_files():
    """Xóa các file tạm thời"""
    print("🧹 Đang xóa file tạm thời...")
    
    temp_patterns = [
        '**/*.tmp',
        '**/*.temp',
        '**/*~',
        '**/.DS_Store',
        '**/Thumbs.db',
        '**/desktop.ini'
    ]
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            print(f"  Xóa: {file_path}")
            os.remove(file_path)

def clean_logs():
    """Xóa file log cũ"""
    print("🧹 Đang xóa file log...")
    
    log_patterns = [
        '**/*.log',
        '**/logs/**'
    ]
    
    for pattern in log_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path):
                print(f"  Xóa: {file_path}")
                os.remove(file_path)

def clean_coverage():
    """Xóa file coverage"""
    print("🧹 Đang xóa file coverage...")
    
    coverage_patterns = [
        '**/.coverage*',
        '**/htmlcov/**',
        '**/.pytest_cache/**',
        '**/.mypy_cache/**'
    ]
    
    for pattern in coverage_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path):
                print(f"  Xóa: {file_path}")
                os.remove(file_path)
            elif os.path.isdir(file_path):
                print(f"  Xóa thư mục: {file_path}")
                shutil.rmtree(file_path, ignore_errors=True)

def main():
    """Hàm chính để dọn dẹp"""
    print("🚀 Bắt đầu dọn dẹp dự án...")
    print("=" * 50)
    
    try:
        clean_python_cache()
        clean_temp_files()
        clean_logs()
        clean_coverage()
        
        print("=" * 50)
        print("✅ Hoàn thành dọn dẹp!")
        print("💡 Tip: Chạy script này định kỳ để giữ dự án sạch sẽ")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình dọn dẹp: {e}")

if __name__ == "__main__":
    main()
