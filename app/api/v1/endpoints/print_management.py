"""
Router cho Quản lý In ấn
Hỗ trợ in hóa đơn qua LAN/WAN và quản lý máy in
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, UserRole, Printer, PrintJob, PrinterAgent
from app.routers.auth import get_current_user
from app.services.print_service import PrintJobService, PrinterService, PrintAgentService
from pydantic import BaseModel

router = APIRouter()

# Schemas cho print management
class PrinterCreate(BaseModel):
    name: str
    location: Optional[str] = ""
    ip_address: Optional[str] = ""
    printer_type: Optional[str] = "NETWORK"

class PrinterResponse(BaseModel):
    id: int
    name: str
    location: Optional[str]
    ip_address: Optional[str]
    printer_type: str
    is_active: bool
    
    class Config:
        from_attributes = True

class PrintJobCreate(BaseModel):
    invoice_id: int
    printer_id: int
    copies: Optional[int] = 1
    paper_size: Optional[str] = "A4"

class PrintJobResponse(BaseModel):
    id: int
    printer_id: int
    invoice_id: int
    status: str
    sent_at: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

class PrintAgentCreate(BaseModel):
    host_id: str
    host_name: Optional[str] = ""
    jwt_token: Optional[str] = ""

@router.get("/printers", response_model=List[PrinterResponse])
def get_printers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách máy in"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và kế toán mới có quyền quản lý máy in"
        )
    
    printer_service = PrinterService(db)
    return printer_service.get_active_printers()

@router.post("/printers", response_model=PrinterResponse)
def create_printer(
    printer_data: PrinterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Đăng ký máy in mới"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền thêm máy in"
        )
    
    try:
        printer_service = PrinterService(db)
        printer = printer_service.register_printer(printer_data.dict())
        
        if not printer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể đăng ký máy in"
            )
        
        return printer
    except Exception as e:
        print(f"Error creating printer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tạo máy in"
        )

@router.get("/printers/discover")
def discover_printers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tự động phát hiện máy in trên mạng"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền quét máy in"
        )
    
    printer_service = PrinterService(db)
    discovered_printers = printer_service.discover_network_printers()
    
    return {
        "discovered_printers": discovered_printers,
        "message": f"Tìm thấy {len(discovered_printers)} máy in trên mạng"
    }

@router.post("/jobs", response_model=PrintJobResponse)
def create_print_job(
    job_data: PrintJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo job in hóa đơn"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và kế toán mới có quyền in hóa đơn"
        )
    
    try:
        print_service = PrintJobService(db)
        print_job = print_service.create_print_job(
            invoice_id=job_data.invoice_id,
            printer_id=job_data.printer_id,
            options={
                'copies': job_data.copies,
                'paper_size': job_data.paper_size
            }
        )
        
        if not print_job:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tạo job in"
            )
        
        return print_job
    except Exception as e:
        print(f"Error creating print job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi tạo job in"
        )

@router.get("/jobs", response_model=List[PrintJobResponse])
def get_print_jobs(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách job in"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và kế toán mới có quyền xem job in"
        )
    
    print_service = PrintJobService(db)
    return print_service.get_print_jobs(status=status_filter)

@router.post("/jobs/{job_id}/retry")
def retry_print_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Thử lại job in bị lỗi"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin và kế toán mới có quyền retry job in"
        )
    
    try:
        print_service = PrintJobService(db)
        success = print_service.retry_failed_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể retry job in"
            )
        
        return {"message": "Job in đã được thử lại thành công"}
    except Exception as e:
        print(f"Error retrying print job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi retry job in"
        )

@router.post("/agents")
def register_print_agent(
    agent_data: PrintAgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Đăng ký Print Agent cho in từ xa"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền đăng ký print agent"
        )
    
    try:
        agent_service = PrintAgentService(db)
        agent = agent_service.register_agent(agent_data.dict())
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể đăng ký print agent"
            )
        
        return {
            "message": "Print agent đã được đăng ký thành công",
            "agent_id": agent.id,
            "host_id": agent.host_id
        }
    except Exception as e:
        print(f"Error registering print agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi đăng ký print agent"
        )

@router.get("/agents")
def get_print_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách Print Agent"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền xem print agent"
        )
    
    agents = db.query(PrinterAgent).filter(PrinterAgent.is_active == True).all()
    
    return {
        "agents": [
            {
                "id": agent.id,
                "host_id": agent.host_id,
                "host_name": agent.host_name,
                "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
                "is_active": agent.is_active
            }
            for agent in agents
        ]
    }