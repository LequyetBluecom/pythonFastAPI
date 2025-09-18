"""
Service gửi email notification
Gửi hóa đơn điện tử và thông báo thanh toán
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader

class EmailService:
    """Service gửi email"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)
        self.sender_name = os.getenv("SENDER_NAME", "Hệ thống thanh toán trường học")
        
        # Setup Jinja2 cho email templates
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "email")
        os.makedirs(template_dir, exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Tạo các template email cơ bản
        self._ensure_email_templates()
        
    def send_invoice_email(
        self, 
        recipient_email: str, 
        recipient_name: str,
        invoice_data: dict,
        pdf_path: Optional[str] = None,
        xml_path: Optional[str] = None
    ) -> bool:
        """Gửi email hóa đơn điện tử cho phụ huynh"""
        try:
            # Load template
            template = self.jinja_env.get_template("invoice_notification.html")
            
            # Render HTML content
            html_content = template.render(
                recipient_name=recipient_name,
                invoice_data=invoice_data,
                company_name=os.getenv("COMPANY_NAME", "Trường Tiểu học ABC")
            )
            
            # Tạo email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Hóa đơn điện tử #{invoice_data['invoice_number']}"
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            
            # Text version (fallback)
            text_content = f"""
Kính gửi {recipient_name},

Hóa đơn điện tử của bạn đã được phát hành thành công.

Thông tin hóa đơn:
- Số hóa đơn: {invoice_data['invoice_number']}
- Mã tra cứu: {invoice_data.get('lookup_code', 'N/A')}
- Học sinh: {invoice_data.get('student_name', 'N/A')}
- Số tiền: {invoice_data.get('total_amount', 0):,.0f} VNĐ
- Nội dung: {invoice_data.get('description', 'N/A')}

Bạn có thể tra cứu hóa đơn tại: https://tracuuhoadon.gdt.gov.vn

Trân trọng,
{self.sender_name}
            """
            
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Attach PDF nếu có
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= invoice_{invoice_data["invoice_number"]}.pdf'
                    )
                    msg.attach(part)
            
            # Attach XML nếu có
            if xml_path and os.path.exists(xml_path):
                with open(xml_path, "rb") as attachment:
                    part = MIMEBase('application', 'xml')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= invoice_{invoice_data["invoice_number"]}.xml'
                    )
                    msg.attach(part)
            
            # Gửi email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"Error sending invoice email: {e}")
            return False
            
    def send_payment_confirmation(
        self,
        recipient_email: str,
        recipient_name: str,
        payment_data: dict
    ) -> bool:
        """Gửi email xác nhận thanh toán thành công"""
        try:
            template = self.jinja_env.get_template("payment_confirmation.html")
            
            html_content = template.render(
                recipient_name=recipient_name,
                payment_data=payment_data,
                company_name=os.getenv("COMPANY_NAME", "Trường Tiểu học ABC")
            )
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Xác nhận thanh toán #{payment_data['payment_code']}"
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            
            text_content = f"""
Kính gửi {recipient_name},

Thanh toán của bạn đã được xử lý thành công.

Thông tin thanh toán:
- Mã giao dịch: {payment_data['payment_code']}
- Số tiền: {payment_data.get('amount', 0):,.0f} VNĐ
- Học sinh: {payment_data.get('student_name', 'N/A')}
- Nội dung: {payment_data.get('description', 'N/A')}
- Thời gian: {payment_data.get('paid_at', 'N/A')}

Hóa đơn điện tử sẽ được gửi trong thời gian sớm nhất.

Trân trọng,
{self.sender_name}
            """
            
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"Error sending payment confirmation: {e}")
            return False
            
    def send_payment_reminder(
        self,
        recipient_emails: List[str],
        overdue_orders: List[dict]
    ) -> bool:
        """Gửi email nhắc nhở thanh toán cho các khoản quá hạn"""
        try:
            template = self.jinja_env.get_template("payment_reminder.html")
            
            for email in recipient_emails:
                # Filter orders for this parent
                parent_orders = [o for o in overdue_orders if o.get('parent_email') == email]
                if not parent_orders:
                    continue
                    
                html_content = template.render(
                    parent_name=parent_orders[0].get('parent_name', 'Phụ huynh'),
                    orders=parent_orders,
                    company_name=os.getenv("COMPANY_NAME", "Trường Tiểu học ABC")
                )
                
                msg = MIMEMultipart('alternative')
                msg['Subject'] = "Nhắc nhở thanh toán học phí"
                msg['From'] = f"{self.sender_name} <{self.sender_email}>"
                msg['To'] = email
                
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                    
            return True
            
        except Exception as e:
            print(f"Error sending payment reminders: {e}")
            return False
    
    def send_password_reset(self, recipient_email: str, recipient_name: str, reset_url: str) -> bool:
        """Gửi email đặt lại mật khẩu"""
        try:
            subject = "Đặt lại mật khẩu"
            html_content = f"""
            <p>Xin chào {recipient_name},</p>
            <p>Bạn đã yêu cầu đặt lại mật khẩu. Vui lòng nhấn vào liên kết dưới đây để đặt lại:</p>
            <p><a href=\"{reset_url}\">Đặt lại mật khẩu</a></p>
            <p>Nếu bạn không yêu cầu, vui lòng bỏ qua email này.</p>
            """.strip()
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return False
            
    def _ensure_email_templates(self):
        """Tạo các email template cơ bản"""
        templates = {
            "invoice_notification.html": '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; }
        .header { background: #007bff; color: white; text-align: center; padding: 20px; }
        .content { background: white; padding: 20px; margin: 20px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; }
        .info-table { width: 100%; border-collapse: collapse; }
        .info-table td { padding: 8px; border-bottom: 1px solid #eee; }
        .info-table .label { font-weight: bold; width: 30%; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ company_name }}</h1>
            <h2>HÓA ĐƠN ĐIỆN TỬ</h2>
        </div>
        
        <div class="content">
            <p>Kính gửi <strong>{{ recipient_name }}</strong>,</p>
            
            <p>Hóa đơn điện tử cho khoản học phí đã được phát hành thành công.</p>
            
            <table class="info-table">
                <tr>
                    <td class="label">Số hóa đơn:</td>
                    <td>{{ invoice_data.invoice_number }}</td>
                </tr>
                <tr>
                    <td class="label">Mã tra cứu:</td>
                    <td>{{ invoice_data.lookup_code or 'N/A' }}</td>
                </tr>
                <tr>
                    <td class="label">Học sinh:</td>
                    <td>{{ invoice_data.student_name or 'N/A' }}</td>
                </tr>
                <tr>
                    <td class="label">Lớp:</td>
                    <td>{{ invoice_data.class_name or 'N/A' }}</td>
                </tr>
                <tr>
                    <td class="label">Nội dung:</td>
                    <td>{{ invoice_data.description or 'N/A' }}</td>
                </tr>
                <tr>
                    <td class="label">Số tiền:</td>
                    <td><strong>{{ "{:,.0f}".format(invoice_data.total_amount or 0) }} VNĐ</strong></td>
                </tr>
            </table>
            
            <p>Bạn có thể tra cứu hóa đơn tại: <a href="https://tracuuhoadon.gdt.gov.vn">tracuuhoadon.gdt.gov.vn</a></p>
            
            <p>File PDF và XML hóa đơn được đính kèm theo email này.</p>
        </div>
        
        <div class="footer">
            <p>Email này được gửi tự động từ hệ thống quản lý học phí</p>
            <p>{{ company_name }}</p>
        </div>
    </div>
</body>
</html>
            ''',
            
            "payment_confirmation.html": '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; }
        .header { background: #28a745; color: white; text-align: center; padding: 20px; }
        .content { background: white; padding: 20px; margin: 20px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; }
        .success-icon { font-size: 48px; color: #28a745; text-align: center; }
        .info-table { width: 100%; border-collapse: collapse; }
        .info-table td { padding: 8px; border-bottom: 1px solid #eee; }
        .info-table .label { font-weight: bold; width: 30%; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ company_name }}</h1>
            <h2>XÁC NHẬN THANH TOÁN</h2>
        </div>
        
        <div class="content">
            <div class="success-icon">✓</div>
            
            <p>Kính gửi <strong>{{ recipient_name }}</strong>,</p>
            
            <p>Thanh toán của bạn đã được xử lý thành công!</p>
            
            <table class="info-table">
                <tr>
                    <td class="label">Mã giao dịch:</td>
                    <td>{{ payment_data.payment_code }}</td>
                </tr>
                <tr>
                    <td class="label">Học sinh:</td>
                    <td>{{ payment_data.student_name or 'N/A' }}</td>
                </tr>
                <tr>
                    <td class="label">Nội dung:</td>
                    <td>{{ payment_data.description or 'N/A' }}</td>
                </tr>
                <tr>
                    <td class="label">Số tiền:</td>
                    <td><strong>{{ "{:,.0f}".format(payment_data.amount or 0) }} VNĐ</strong></td>
                </tr>
                <tr>
                    <td class="label">Thời gian:</td>
                    <td>{{ payment_data.paid_at or 'N/A' }}</td>
                </tr>
            </table>
            
            <p>Hóa đơn điện tử sẽ được phát hành và gửi đến email của bạn trong thời gian sớm nhất.</p>
        </div>
        
        <div class="footer">
            <p>Email này được gửi tự động từ hệ thống quản lý học phí</p>
            <p>{{ company_name }}</p>
        </div>
    </div>
</body>
</html>
            ''',
            
            "payment_reminder.html": '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; }
        .header { background: #ffc107; color: #212529; text-align: center; padding: 20px; }
        .content { background: white; padding: 20px; margin: 20px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; }
        .orders-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .orders-table th, .orders-table td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        .orders-table th { background-color: #f2f2f2; }
        .overdue { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ company_name }}</h1>
            <h2>NHẮC NHỞ THANH TOÁN</h2>
        </div>
        
        <div class="content">
            <p>Kính gửi <strong>{{ parent_name }}</strong>,</p>
            
            <p>Chúng tôi xin thông báo có các khoản học phí sau chưa được thanh toán:</p>
            
            <table class="orders-table">
                <thead>
                    <tr>
                        <th>Học sinh</th>
                        <th>Lớp</th>
                        <th>Nội dung</th>
                        <th>Số tiền</th>
                        <th>Hạn thanh toán</th>
                    </tr>
                </thead>
                <tbody>
                    {% for order in orders %}
                    <tr>
                        <td>{{ order.student_name }}</td>
                        <td>{{ order.class_name }}</td>
                        <td>{{ order.description }}</td>
                        <td>{{ "{:,.0f}".format(order.amount) }} VNĐ</td>
                        <td class="overdue">{{ order.due_date }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <p>Để tránh ảnh hưởng đến việc học của con em, quý phụ huynh vui lòng thanh toán trong thời gian sớm nhất.</p>
            
            <p>Mọi thắc mắc xin liên hệ với nhà trường để được hỗ trợ.</p>
        </div>
        
        <div class="footer">
            <p>Email này được gửi tự động từ hệ thống quản lý học phí</p>
            <p>{{ company_name }}</p>
        </div>
    </div>
</body>
</html>
            '''
        }
        
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "email")
        for filename, content in templates.items():
            file_path = os.path.join(template_dir, filename)
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content.strip())