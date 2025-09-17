"""
Service xử lý hóa đơn điện tử
Tích hợp với nhà cung cấp HĐĐT (Viettel, VNPT, MISA...)
"""
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
import requests
import hashlib
from sqlalchemy.orm import Session
from app.models import Invoice, Order, User, Student, OrderStatus
from jinja2 import Environment, FileSystemLoader

class EInvoiceProvider:
    """Service tích hợp với nhà cung cấp HĐĐT"""
    
    def __init__(self):
        self.api_url = os.getenv("EINVOICE_API_URL", "https://api.demo-einvoice.com")
        self.api_key = os.getenv("EINVOICE_API_KEY", "demo-key")
        self.company_tax_code = os.getenv("COMPANY_TAX_CODE", "0123456789")
        self.company_name = os.getenv("COMPANY_NAME", "Trường Tiểu học ABC")
        
    def create_invoice(self, invoice_data: Dict) -> Dict:
        """
        Gửi dữ liệu hóa đơn tới nhà cung cấp HĐĐT
        Trả về XML ký số và mã tra cứu
        """
        # Tạo XML hóa đơn theo chuẩn
        xml_data = self._generate_invoice_xml(invoice_data)
        
        # Payload gửi tới nhà cung cấp
        payload = {
            "company_tax_code": self.company_tax_code,
            "invoice_type": "01GTKT",  # Hóa đơn GTGT
            "invoice_data": xml_data,
            "convert_option": {
                "is_convert_to_pdf": True,
                "is_send_email": False  # Sẽ tự gửi email qua hệ thống của mình
            }
        }
        
        # Trong production gọi API thật
        # response = requests.post(
        #     f"{self.api_url}/invoices/create",
        #     json=payload,
        #     headers={"Authorization": f"Bearer {self.api_key}"}
        # )
        
        # Mock response cho development
        invoice_code = f"C25TTA{datetime.now().strftime('%y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        lookup_code = f"TCT{uuid.uuid4().hex[:8].upper()}"
        
        mock_response = {
            "success": True,
            "invoice_code": invoice_code,
            "lookup_code": lookup_code,
            "invoice_number": invoice_data["invoice_number"],
            "signed_xml": xml_data,  # Trong thực tế sẽ là XML đã ký số
            "pdf_url": f"{self.api_url}/invoices/{invoice_code}/pdf",
            "issued_at": datetime.now().isoformat()
        }
        
        return mock_response
        
    def _generate_invoice_xml(self, data: Dict) -> str:
        """Tạo XML hóa đơn theo chuẩn Nghị định 123/2020"""
        root = ET.Element("Invoice")
        
        # Header
        header = ET.SubElement(root, "InvoiceHeader")
        ET.SubElement(header, "InvoiceType").text = "01GTKT"
        ET.SubElement(header, "InvoiceCode").text = data["invoice_number"]
        ET.SubElement(header, "InvoiceDate").text = datetime.now().strftime("%Y-%m-%d")
        
        # Seller info
        seller = ET.SubElement(root, "SellerInfo")
        ET.SubElement(seller, "TaxCode").text = self.company_tax_code
        ET.SubElement(seller, "CompanyName").text = self.company_name
        ET.SubElement(seller, "Address").text = data.get("seller_address", "")
        
        # Buyer info
        buyer = ET.SubElement(root, "BuyerInfo")
        ET.SubElement(buyer, "BuyerName").text = data["customer_name"]
        ET.SubElement(buyer, "BuyerTaxCode").text = data.get("customer_tax_code", "")
        ET.SubElement(buyer, "BuyerAddress").text = data.get("customer_address", "")
        
        # Invoice items
        items = ET.SubElement(root, "InvoiceItems")
        item = ET.SubElement(items, "Item")
        ET.SubElement(item, "Description").text = data["description"]
        ET.SubElement(item, "Quantity").text = "1"
        ET.SubElement(item, "UnitPrice").text = str(data["amount"])
        ET.SubElement(item, "Amount").text = str(data["amount"])
        ET.SubElement(item, "TaxRate").text = str(data.get("tax_rate", 0))
        ET.SubElement(item, "TaxAmount").text = str(data.get("tax_amount", 0))
        
        # Totals
        totals = ET.SubElement(root, "InvoiceTotals")
        ET.SubElement(totals, "TotalAmount").text = str(data["total_amount"])
        ET.SubElement(totals, "TotalTaxAmount").text = str(data.get("tax_amount", 0))
        ET.SubElement(totals, "GrandTotal").text = str(data["total_amount"])
        
        return ET.tostring(root, encoding='unicode')

class InvoiceService:
    """Service xử lý business logic hóa đơn"""
    
    def __init__(self, db: Session):
        self.db = db
        self.einvoice_provider = EInvoiceProvider()
        
        # Setup Jinja2 template engine
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        os.makedirs(template_dir, exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
    def generate_invoice(self, order_id: int) -> Dict:
        """Tạo hóa đơn điện tử cho đơn hàng đã thanh toán"""
        # Lấy thông tin đơn hàng
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.PAID:
            raise ValueError("Đơn hàng chưa được thanh toán")
            
        # Lấy thông tin học sinh và phụ huynh
        student = self.db.query(Student).filter(Student.id == order.student_id).first()
        parent = self.db.query(User).filter(User.id == student.user_id).first()
        
        # Tạo số hóa đơn
        invoice_number = f"HD{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Dữ liệu hóa đơn
        invoice_data = {
            "invoice_number": invoice_number,
            "customer_name": parent.name,
            "customer_tax_code": "",  # Phụ huynh thường không có MST
            "customer_address": "",
            "description": order.description,
            "amount": order.amount,
            "tax_rate": 0,  # Học phí thường không chịu VAT
            "tax_amount": 0,
            "total_amount": order.amount,
            "student_name": student.name,
            "student_code": student.student_code,
            "class_name": student.class_name
        }
        
        # Gửi tới nhà cung cấp HĐĐT
        einvoice_response = self.einvoice_provider.create_invoice(invoice_data)
        
        if not einvoice_response.get("success"):
            raise ValueError("Không thể tạo hóa đơn điện tử")
            
        # Lưu invoice record
        invoice = Invoice(
            order_id=order_id,
            invoice_number=invoice_number,
            invoice_code=einvoice_response["invoice_code"],
            e_invoice_code=einvoice_response["lookup_code"],
            customer_name=parent.name,
            customer_tax_code="",
            customer_address="",
            amount=order.amount,
            tax_amount=0,
            total_amount=order.amount
        )
        
        self.db.add(invoice)
        
        # Cập nhật order status
        order.status = OrderStatus.INVOICED
        
        self.db.commit()
        self.db.refresh(invoice)
        
        # Tạo PDF
        pdf_path = self._generate_pdf(invoice, invoice_data)
        invoice.pdf_path = pdf_path
        
        # Lưu XML
        xml_path = self._save_xml(einvoice_response["signed_xml"], invoice.id)
        invoice.xml_path = xml_path
        
        self.db.commit()
        
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice_number,
            "invoice_code": einvoice_response["invoice_code"],
            "lookup_code": einvoice_response["lookup_code"],
            "pdf_path": pdf_path,
            "xml_path": xml_path
        }
        
    def _generate_pdf(self, invoice: Invoice, data: Dict) -> str:
        """Tạo PDF hóa đơn sử dụng WeasyPrint"""
        # Lazy import WeasyPrint to avoid hard dependency at app startup
        try:
            from weasyprint import HTML  # type: ignore
        except Exception:
            HTML = None  # type: ignore
        
        # Tạo template HTML nếu chưa có
        self._ensure_invoice_template()
        
        # Load template
        template = self.jinja_env.get_template("invoice_template.html")
        
        # Render HTML
        html_content = template.render(
            invoice=invoice,
            data=data,
            company_name=os.getenv("COMPANY_NAME", "Trường Tiểu học ABC"),
            company_address=os.getenv("COMPANY_ADDRESS", ""),
            company_phone=os.getenv("COMPANY_PHONE", ""),
            generated_at=datetime.now()
        )
        
        pdf_dir = "invoices/pdf"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = f"{pdf_dir}/invoice_{invoice.id}.pdf"
        
        if HTML is not None:
            # Generate real PDF if WeasyPrint is available
            HTML(string=html_content).write_pdf(pdf_path)
            return pdf_path
        
        # Fallback: save HTML alongside (no PDF engine available)
        html_fallback_path = f"{pdf_dir}/invoice_{invoice.id}.html"
        with open(html_fallback_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return html_fallback_path
        
    def _save_xml(self, xml_content: str, invoice_id: int) -> str:
        """Lưu file XML hóa đơn"""
        xml_dir = "invoices/xml"
        os.makedirs(xml_dir, exist_ok=True)
        xml_path = f"{xml_dir}/invoice_{invoice_id}.xml"
        
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
            
        return xml_path
        
    def _ensure_invoice_template(self):
        """Tạo template HTML hóa đơn nếu chưa có"""
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "invoice_template.html"
        )
        
        if not os.path.exists(template_path):
            template_content = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Hóa đơn điện tử</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .invoice-info { margin: 20px 0; }
        .customer-info { margin: 20px 0; }
        .items-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .items-table th, .items-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .items-table th { background-color: #f2f2f2; }
        .total { text-align: right; font-weight: bold; margin: 20px 0; }
        .signatures { display: flex; justify-content: space-between; margin-top: 40px; }
        .signature { text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>HÓA ĐƠN ĐIỆN TỬ</h1>
        <p>Invoice Number: {{ invoice.invoice_number }}</p>
        <p>Mã tra cứu: {{ invoice.e_invoice_code }}</p>
    </div>
    
    <div class="company-info">
        <h2>{{ company_name }}</h2>
        <p>Địa chỉ: {{ company_address }}</p>
        <p>Điện thoại: {{ company_phone }}</p>
    </div>
    
    <div class="invoice-info">
        <p><strong>Ngày phát hành:</strong> {{ invoice.issued_at.strftime('%d/%m/%Y') }}</p>
        <p><strong>Học sinh:</strong> {{ data.student_name }} ({{ data.student_code }})</p>
        <p><strong>Lớp:</strong> {{ data.class_name }}</p>
    </div>
    
    <div class="customer-info">
        <p><strong>Người thanh toán:</strong> {{ invoice.customer_name }}</p>
        <p><strong>Địa chỉ:</strong> {{ invoice.customer_address or 'N/A' }}</p>
    </div>
    
    <table class="items-table">
        <thead>
            <tr>
                <th>Mô tả</th>
                <th>Số lượng</th>
                <th>Đơn giá</th>
                <th>Thành tiền</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{{ data.description }}</td>
                <td>1</td>
                <td>{{ "{:,.0f}".format(invoice.amount) }} VNĐ</td>
                <td>{{ "{:,.0f}".format(invoice.amount) }} VNĐ</td>
            </tr>
        </tbody>
    </table>
    
    <div class="total">
        <p>Tổng tiền chưa thuế: {{ "{:,.0f}".format(invoice.amount) }} VNĐ</p>
        <p>Thuế VAT ({{ data.tax_rate }}%): {{ "{:,.0f}".format(invoice.tax_amount) }} VNĐ</p>
        <p><strong>Tổng cộng: {{ "{:,.0f}".format(invoice.total_amount) }} VNĐ</strong></p>
        <p><strong>Bằng chữ: {{ data.amount_in_words or '' }}</strong></p>
    </div>
    
    <div class="signatures">
        <div class="signature">
            <p><strong>Người mua hàng</strong></p>
            <p>(Ký và ghi rõ họ tên)</p>
            <br><br><br>
            <p>{{ invoice.customer_name }}</p>
        </div>
        <div class="signature">
            <p><strong>Người bán hàng</strong></p>
            <p>(Ký và ghi rõ họ tên)</p>
            <br><br><br>
            <p>{{ company_name }}</p>
        </div>
    </div>
    
    <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #666;">
        <p>Hóa đơn được tạo tự động bởi hệ thống - {{ generated_at.strftime('%d/%m/%Y %H:%M:%S') }}</p>
        <p>Tra cứu hóa đơn tại: tracuuhoadon.gdt.gov.vn với mã: {{ invoice.e_invoice_code }}</p>
    </div>
</body>
</html>
            '''
            
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content.strip())