"""
Service quản lý in hóa đơn qua LAN/WAN
Hỗ trợ in trực tiếp qua IPP/CUPS và Print Agent từ xa
"""
import os
import json
import requests
import subprocess
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Printer, PrinterAgent, PrintJob, Invoice
from datetime import datetime
import tempfile

class PrinterService:
    """Service quản lý máy in"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def discover_network_printers(self) -> List[Dict]:
        """Tự động phát hiện máy in trên mạng LAN"""
        try:
            # Sử dụng CUPS để tìm máy in (Linux)
            if os.name == 'posix':
                result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                printers = []
                
                if result.returncode == 0:
                    lines = result.stdout.split('\\n')
                    for line in lines:
                        if 'printer' in line:
                            printer_name = line.split(' ')[1]
                            printers.append({
                                'name': printer_name,
                                'type': 'NETWORK',
                                'driver': 'IPP'
                            })
                            
                return printers
                
            # Windows printer discovery
            elif os.name == 'nt':
                # Có thể sử dụng WMI để tìm máy in Windows
                return []
                
        except Exception as e:
            print(f"Error discovering printers: {e}")
            
        return []
        
    def register_printer(self, printer_data: Dict) -> Optional[Printer]:
        """Đăng ký máy in mới vào hệ thống"""
        try:
            printer = Printer(
                name=printer_data['name'],
                location=printer_data.get('location', ''),
                ip_address=printer_data.get('ip_address', ''),
                printer_type=printer_data.get('type', 'NETWORK'),
                is_active=True
            )
            
            self.db.add(printer)
            self.db.commit()
            self.db.refresh(printer)
            
            return printer
            
        except Exception as e:
            print(f"Error registering printer: {e}")
            self.db.rollback()
            return None
            
    def get_active_printers(self) -> List[Printer]:
        """Lấy danh sách máy in đang hoạt động"""
        return self.db.query(Printer).filter(Printer.is_active == True).all()

class PrintAgentService:
    """Service quản lý Print Agent cho in từ xa"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def register_agent(self, agent_data: Dict) -> Optional[PrinterAgent]:
        """Đăng ký Print Agent mới"""
        try:
            agent = PrinterAgent(
                host_id=agent_data['host_id'],
                host_name=agent_data.get('host_name', ''),
                jwt_token=agent_data.get('jwt_token', ''),
                last_seen=datetime.now(),
                is_active=True
            )
            
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
            
            return agent
            
        except Exception as e:
            print(f"Error registering print agent: {e}")
            self.db.rollback()
            return None
            
    def send_print_job_to_agent(self, agent_id: int, job_data: Dict) -> bool:
        """Gửi job in tới Print Agent từ xa"""
        try:
            agent = self.db.query(PrinterAgent).filter(
                PrinterAgent.id == agent_id,
                PrinterAgent.is_active == True
            ).first()
            
            if not agent:
                return False
                
            # Tạo payload gửi tới agent
            payload = {
                'job_id': job_data['job_id'],
                'printer_name': job_data['printer_name'],
                'document_data': job_data['document_data'],
                'document_type': job_data.get('document_type', 'PDF'),
                'copies': job_data.get('copies', 1),
                'paper_size': job_data.get('paper_size', 'A4')
            }
            
            # Giả sử agent có endpoint để nhận job
            agent_url = f"http://{agent.host_name}:8080/print-job"
            
            response = requests.post(
                agent_url,
                json=payload,
                headers={'Authorization': f'Bearer {agent.jwt_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                # Cập nhật last_seen
                agent.last_seen = datetime.now()
                self.db.commit()
                return True
                
        except Exception as e:
            print(f"Error sending job to print agent: {e}")
            
        return False

class PrintJobService:
    """Service quản lý công việc in"""
    
    def __init__(self, db: Session):
        self.db = db
        self.printer_service = PrinterService(db)
        self.agent_service = PrintAgentService(db)
        
    def create_print_job(
        self, 
        invoice_id: int, 
        printer_id: int, 
        options: Optional[Dict] = None
    ) -> Optional[PrintJob]:
        """Tạo job in hóa đơn"""
        try:
            # Lấy thông tin hóa đơn
            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise ValueError("Không tìm thấy hóa đơn")
                
            # Lấy thông tin máy in
            printer = self.db.query(Printer).filter(Printer.id == printer_id).first()
            if not printer:
                raise ValueError("Không tìm thấy máy in")
                
            # Tạo dữ liệu in (có thể là HTML, PDF base64, etc.)
            print_data = self._prepare_print_data(invoice, options or {})
            
            # Tạo print job record
            print_job = PrintJob(
                printer_id=printer_id,
                invoice_id=invoice_id,
                job_data=json.dumps(print_data),
                status="pending"
            )
            
            self.db.add(print_job)
            self.db.commit()
            self.db.refresh(print_job)
            
            # Thực hiện in
            success = self._execute_print_job(print_job, printer)
            
            if success:
                print_job.status = "sent"
                print_job.sent_at = datetime.now()
            else:
                print_job.status = "failed"
                
            self.db.commit()
            
            return print_job
            
        except Exception as e:
            print(f"Error creating print job: {e}")
            self.db.rollback()
            return None
            
    def _prepare_print_data(self, invoice: Invoice, options: Dict) -> Dict:
        """Chuẩn bị dữ liệu in"""
        # Đọc file PDF nếu có
        if invoice.pdf_path and os.path.exists(invoice.pdf_path):
            with open(invoice.pdf_path, 'rb') as f:
                pdf_data = f.read()
                
            return {
                'type': 'PDF',
                'data': pdf_data.hex(),  # Convert to hex string
                'options': {
                    'copies': options.get('copies', 1),
                    'paper_size': options.get('paper_size', 'A4'),
                    'orientation': options.get('orientation', 'portrait')
                }
            }
            
        # Fallback: tạo HTML đơn giản để in
        return {
            'type': 'HTML',
            'data': self._generate_simple_html(invoice),
            'options': options
        }
        
    def _generate_simple_html(self, invoice: Invoice) -> str:
        """Tạo HTML đơn giản cho in nhanh"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .info {{ margin: 10px 0; }}
                .total {{ font-weight: bold; font-size: 14px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>HÓA ĐƠN ĐIỆN TỬ</h2>
                <p>Số: {invoice.invoice_number}</p>
            </div>
            
            <div class="info">
                <p><strong>Khách hàng:</strong> {invoice.customer_name}</p>
                <p><strong>Mã tra cứu:</strong> {invoice.e_invoice_code or 'N/A'}</p>
                <p><strong>Ngày phát hành:</strong> {invoice.issued_at.strftime('%d/%m/%Y')}</p>
            </div>
            
            <div class="total">
                <p>Tổng tiền: {invoice.total_amount:,.0f} VNĐ</p>
            </div>
            
            <div style="margin-top: 40px; text-align: center; font-size: 12px;">
                <p>--- Cảm ơn quý khách ---</p>
            </div>
        </body>
        </html>
        """
        
    def _execute_print_job(self, job: PrintJob, printer: Printer) -> bool:
        """Thực hiện in job"""
        try:
            job_data = json.loads(job.job_data)
            
            if printer.agent_id:
                # In qua Print Agent (WAN)
                return self.agent_service.send_print_job_to_agent(
                    printer.agent_id,
                    {
                        'job_id': job.id,
                        'printer_name': printer.name,
                        'document_data': job_data['data'],
                        'document_type': job_data['type'],
                        'copies': job_data['options'].get('copies', 1)
                    }
                )
            else:
                # In trực tiếp qua LAN
                return self._print_direct(printer, job_data)
                
        except Exception as e:
            print(f"Error executing print job: {e}")
            return False
            
    def _print_direct(self, printer: Printer, job_data: Dict) -> bool:
        """In trực tiếp qua CUPS/IPP (LAN)"""
        try:
            if job_data['type'] == 'PDF':
                # Tạo file tạm cho PDF
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(bytes.fromhex(job_data['data']))
                    temp_file_path = temp_file.name
                    
                # In bằng lpr command (Linux)
                if os.name == 'posix':
                    cmd = ['lpr', '-P', printer.name, temp_file_path]
                    
                    # Thêm options
                    options = job_data.get('options', {})
                    if options.get('copies', 1) > 1:
                        cmd.extend(['-#', str(options['copies'])])
                        
                    result = subprocess.run(cmd, capture_output=True)
                    
                    # Cleanup
                    os.unlink(temp_file_path)
                    
                    return result.returncode == 0
                    
            elif job_data['type'] == 'HTML':
                # Convert HTML to PDF rồi in
                from weasyprint import HTML
                
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    HTML(string=job_data['data']).write_pdf(temp_file.name)
                    
                    if os.name == 'posix':
                        result = subprocess.run(['lpr', '-P', printer.name, temp_file.name])
                        os.unlink(temp_file.name)
                        return result.returncode == 0
                        
        except Exception as e:
            print(f"Error in direct printing: {e}")
            
        return False
        
    def get_print_jobs(self, status: Optional[str] = None) -> List[PrintJob]:
        """Lấy danh sách job in"""
        query = self.db.query(PrintJob)
        
        if status:
            query = query.filter(PrintJob.status == status)
            
        return query.order_by(PrintJob.created_at.desc()).all()
        
    def retry_failed_job(self, job_id: int) -> bool:
        """Thử lại job in bị lỗi"""
        try:
            job = self.db.query(PrintJob).filter(PrintJob.id == job_id).first()
            if not job or job.status != 'failed':
                return False
                
            printer = self.db.query(Printer).filter(Printer.id == job.printer_id).first()
            if not printer:
                return False
                
            # Reset status và thử lại
            job.status = 'pending'
            self.db.commit()
            
            job_data = json.loads(job.job_data)
            success = self._execute_print_job(job, printer)
            
            if success:
                job.status = 'sent'
                job.sent_at = datetime.now()
            else:
                job.status = 'failed'
                
            self.db.commit()
            return success
            
        except Exception as e:
            print(f"Error retrying print job: {e}")
            return False