"""
Service xử lý logic thanh toán QR code
Tích hợp với các cổng thanh toán được NHNN cấp phép
"""
import os
import qrcode
import io
import base64
import uuid
import requests
from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Payment, Order, PaymentStatus
from datetime import datetime

class PaymentGatewayService:
    """Service tích hợp với cổng thanh toán"""
    
    def __init__(self):
        self.gateway_url = os.getenv("PAYMENT_GATEWAY_URL", "https://api.demo-payment.com")
        self.api_key = os.getenv("PAYMENT_API_KEY", "demo-key")
        self.merchant_id = os.getenv("MERCHANT_ID", "demo-merchant")
        
    def create_qr_payment(self, order: Order, amount: Decimal) -> Dict:
        """
        Tạo QR code thanh toán qua API cổng thanh toán thật
        Trong production sẽ tích hợp với Viettel Pay, VNPay, etc.
        """
        # Tạo mã giao dịch unique
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Payload gửi tới cổng thanh toán
        payload = {
            "merchant_id": self.merchant_id,
            "transaction_id": transaction_id,
            "amount": float(amount),
            "currency": "VND",
            "description": f"Thanh toán {order.description}",
            "order_id": order.order_code,
            "return_url": f"{os.getenv('BASE_URL', 'http://localhost:5000')}/payments/return",
            "notify_url": f"{os.getenv('BASE_URL', 'http://localhost:5000')}/api/payments/webhook"
        }
        
        # Trong production sẽ gọi API thật
        # response = requests.post(f"{self.gateway_url}/create-payment", 
        #                         json=payload, 
        #                         headers={"Authorization": f"Bearer {self.api_key}"})
        
        # Mock response cho development
        mock_response = {
            "success": True,
            "transaction_id": transaction_id,
            "qr_data": f"VIETQR|{self.merchant_id}|{transaction_id}|{amount}|VND|{order.description[:50]}",
            "deep_link": f"vnpay://payment?amount={amount}&desc={order.description}",
            "expires_at": datetime.now().isoformat()
        }
        
        return mock_response
        
    def generate_qr_image(self, qr_data: str) -> str:
        """Tạo QR code image từ data"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Tạo image và convert sang base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
        
    def verify_webhook(self, webhook_data: Dict, signature: str) -> bool:
        """Xác minh webhook signature từ cổng thanh toán"""
        # Trong production sẽ verify signature thật
        # expected_signature = hmac.new(
        #     self.webhook_secret.encode(),
        #     json.dumps(webhook_data).encode(),
        #     hashlib.sha256
        # ).hexdigest()
        # return hmac.compare_digest(expected_signature, signature)
        
        return True  # Mock cho development
        
class PaymentService:
    """Service xử lý business logic thanh toán"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gateway = PaymentGatewayService()
        
    def create_payment_request(self, order_id: int, amount: Decimal) -> Dict:
        """Tạo yêu cầu thanh toán và QR code"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Không tìm thấy đơn hàng")
            
        # Gọi API cổng thanh toán
        gateway_response = self.gateway.create_qr_payment(order, amount)
        
        if not gateway_response.get("success"):
            raise ValueError("Không thể tạo thanh toán")
            
        # Tạo QR image
        qr_image = self.gateway.generate_qr_image(gateway_response["qr_data"])
        
        # Lưu payment record
        payment = Payment(
            order_id=order_id,
            payment_code=gateway_response["transaction_id"],
            gateway_txn_id=gateway_response["transaction_id"],
            amount=amount,
            payment_method="QR_CODE",
            qr_code_data=gateway_response["qr_data"],
            status=PaymentStatus.PENDING
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        return {
            "payment_id": payment.id,
            "payment_code": payment.payment_code,
            "qr_code_image": f"data:image/png;base64,{qr_image}",
            "qr_data": gateway_response["qr_data"],
            "deep_link": gateway_response.get("deep_link"),
            "amount": amount,
            "order_code": order.order_code,
            "expires_at": gateway_response.get("expires_at")
        }
        
    def process_webhook(self, webhook_data: Dict) -> bool:
        """Xử lý webhook từ cổng thanh toán"""
        transaction_id = webhook_data.get("transaction_id")
        status = webhook_data.get("status")
        
        if not transaction_id or not status:
            return False
            
        # Tìm payment record
        payment = self.db.query(Payment).filter(
            Payment.payment_code == transaction_id
        ).first()
        
        if not payment:
            return False
            
        # Cập nhật trạng thái
        if status == "success":
            payment.status = PaymentStatus.SUCCESS
            payment.paid_at = datetime.now()
            
            # Cập nhật order status
            order = self.db.query(Order).filter(Order.id == payment.order_id).first()
            if order:
                order.status = "PAID"
                
        elif status == "failed":
            payment.status = PaymentStatus.FAILED
            
        self.db.commit()
        return True