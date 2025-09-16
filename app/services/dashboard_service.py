"""
Service cung cấp dữ liệu dashboard và báo cáo
Phục vụ các role khác nhau: Admin, Kế toán, Giáo vụ, Phụ huynh
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models import (
    User, Student, Order, Payment, Invoice, UserRole, 
    OrderStatus, PaymentStatus
)

class DashboardService:
    """Service cung cấp dữ liệu dashboard"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_admin_dashboard(self) -> Dict:
        """Dashboard cho Admin - tổng quan toàn hệ thống"""
        try:
            today = datetime.now().date()
            this_month_start = today.replace(day=1)
            last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
            
            # Thống kê tổng quan
            total_students = self.db.query(Student).count()
            total_parents = self.db.query(User).filter(User.role == UserRole.PARENT).count()
            total_staff = self.db.query(User).filter(User.role != UserRole.PARENT).count()
            
            # Thống kê đơn hàng
            total_orders = self.db.query(Order).count()
            paid_orders = self.db.query(Order).filter(Order.status == OrderStatus.PAID).count()
            pending_orders = self.db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
            invoiced_orders = self.db.query(Order).filter(Order.status == OrderStatus.INVOICED).count()
            
            # Thống kê doanh thu
            total_revenue = self.db.query(func.sum(Payment.amount)).filter(
                Payment.status == PaymentStatus.SUCCESS
            ).scalar() or Decimal('0')
            
            monthly_revenue = self.db.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.status == PaymentStatus.SUCCESS,
                    Payment.paid_at >= this_month_start
                )
            ).scalar() or Decimal('0')
            
            last_month_revenue = self.db.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.status == PaymentStatus.SUCCESS,
                    Payment.paid_at >= last_month_start,
                    Payment.paid_at < this_month_start
                )
            ).scalar() or Decimal('0')
            
            # Tính tốc độ tăng trưởng
            growth_rate = 0
            if last_month_revenue > 0:
                growth_rate = float((monthly_revenue - last_month_revenue) / last_month_revenue * 100)
                
            # Đơn hàng quá hạn
            overdue_orders = self.db.query(Order).filter(
                and_(
                    Order.status == OrderStatus.PENDING,
                    Order.due_date < datetime.now()
                )
            ).count()
            
            # Thống kê theo ngày gần đây (7 ngày)
            daily_stats = []
            for i in range(7):
                date = today - timedelta(days=i)
                daily_revenue = self.db.query(func.sum(Payment.amount)).filter(
                    and_(
                        Payment.status == PaymentStatus.SUCCESS,
                        func.date(Payment.paid_at) == date
                    )
                ).scalar() or Decimal('0')
                
                daily_orders = self.db.query(Order).filter(
                    func.date(Order.created_at) == date
                ).count()
                
                daily_stats.append({
                    'date': date.isoformat(),
                    'revenue': float(daily_revenue),
                    'orders': daily_orders
                })
                
            return {
                'overview': {
                    'total_students': total_students,
                    'total_parents': total_parents,
                    'total_staff': total_staff,
                    'total_orders': total_orders,
                    'paid_orders': paid_orders,
                    'pending_orders': pending_orders,
                    'invoiced_orders': invoiced_orders,
                    'overdue_orders': overdue_orders
                },
                'revenue': {
                    'total': float(total_revenue),
                    'monthly': float(monthly_revenue),
                    'last_month': float(last_month_revenue),
                    'growth_rate': round(growth_rate, 2)
                },
                'daily_stats': daily_stats
            }
            
        except Exception as e:
            print(f"Error getting admin dashboard: {e}")
            return {}
            
    def get_accountant_dashboard(self) -> Dict:
        """Dashboard cho Kế toán - tập trung vào hóa đơn và doanh thu"""
        try:
            today = datetime.now().date()
            this_month_start = today.replace(day=1)
            
            # Thống kê hóa đơn
            total_invoices = self.db.query(Invoice).count()
            monthly_invoices = self.db.query(Invoice).filter(
                Invoice.issued_at >= this_month_start
            ).count()
            
            # Đơn hàng cần phát hành hóa đơn
            need_invoice = self.db.query(Order).filter(
                Order.status == OrderStatus.PAID
            ).count()
            
            # Doanh thu theo tháng
            monthly_revenue_data = []
            for i in range(6):  # 6 tháng gần nhất
                month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                revenue = self.db.query(func.sum(Payment.amount)).filter(
                    and_(
                        Payment.status == PaymentStatus.SUCCESS,
                        Payment.paid_at >= month_start,
                        Payment.paid_at <= month_end
                    )
                ).scalar() or Decimal('0')
                
                invoice_count = self.db.query(Invoice).filter(
                    and_(
                        Invoice.issued_at >= month_start,
                        Invoice.issued_at <= month_end
                    )
                ).count()
                
                monthly_revenue_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'revenue': float(revenue),
                    'invoices': invoice_count
                })
                
            # Top 10 khoản thu lớn nhất tháng này
            top_payments = self.db.query(Payment).join(Order).join(Student).join(User).filter(
                and_(
                    Payment.status == PaymentStatus.SUCCESS,
                    Payment.paid_at >= this_month_start
                )
            ).order_by(Payment.amount.desc()).limit(10).all()
            
            top_payments_data = []
            for payment in top_payments:
                order = self.db.query(Order).filter(Order.id == payment.order_id).first()
                student = self.db.query(Student).filter(Student.id == order.student_id).first()
                parent = self.db.query(User).filter(User.id == student.user_id).first()
                
                top_payments_data.append({
                    'payment_code': payment.payment_code,
                    'amount': float(payment.amount),
                    'student_name': student.name,
                    'parent_name': parent.name,
                    'description': order.description,
                    'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
                })
                
            return {
                'overview': {
                    'total_invoices': total_invoices,
                    'monthly_invoices': monthly_invoices,
                    'need_invoice': need_invoice,
                    'monthly_revenue': float(self.db.query(func.sum(Payment.amount)).filter(
                        and_(
                            Payment.status == PaymentStatus.SUCCESS,
                            Payment.paid_at >= this_month_start
                        )
                    ).scalar() or Decimal('0'))
                },
                'monthly_revenue_chart': monthly_revenue_data,
                'top_payments': top_payments_data
            }
            
        except Exception as e:
            print(f"Error getting accountant dashboard: {e}")
            return {}
            
    def get_teacher_dashboard(self) -> Dict:
        """Dashboard cho Giáo vụ - tập trung vào học sinh và khoản phí"""
        try:
            today = datetime.now().date()
            this_month_start = today.replace(day=1)
            
            # Thống kê học sinh
            total_students = self.db.query(Student).count()
            
            # Thống kê theo lớp
            class_stats = self.db.query(
                Student.class_name,
                func.count(Student.id).label('student_count')
            ).group_by(Student.class_name).all()
            
            class_stats_data = [
                {'class_name': stat.class_name, 'student_count': stat.student_count}
                for stat in class_stats
            ]
            
            # Thống kê thanh toán theo lớp
            class_payment_stats = []
            for class_stat in class_stats:
                class_name = class_stat.class_name
                
                # Tổng số đơn hàng của lớp
                total_orders = self.db.query(Order).join(Student).filter(
                    Student.class_name == class_name
                ).count()
                
                # Số đơn đã thanh toán
                paid_orders = self.db.query(Order).join(Student).filter(
                    and_(
                        Student.class_name == class_name,
                        Order.status.in_([OrderStatus.PAID, OrderStatus.INVOICED])
                    )
                ).count()
                
                # Tỷ lệ thanh toán
                payment_rate = (paid_orders / total_orders * 100) if total_orders > 0 else 0
                
                class_payment_stats.append({
                    'class_name': class_name,
                    'total_orders': total_orders,
                    'paid_orders': paid_orders,
                    'payment_rate': round(payment_rate, 1)
                })
                
            # Danh sách học sinh chưa thanh toán (quá hạn)
            overdue_students = self.db.query(Order, Student, User).join(
                Student, Order.student_id == Student.id
            ).join(
                User, Student.user_id == User.id
            ).filter(
                and_(
                    Order.status == OrderStatus.PENDING,
                    Order.due_date < datetime.now()
                )
            ).limit(20).all()
            
            overdue_data = []
            for order, student, parent in overdue_students:
                overdue_data.append({
                    'order_id': order.id,
                    'student_name': student.name,
                    'student_code': student.student_code,
                    'class_name': student.class_name,
                    'parent_name': parent.name,
                    'parent_email': parent.email,
                    'description': order.description,
                    'amount': float(order.amount),
                    'due_date': order.due_date.isoformat() if order.due_date else None,
                    'days_overdue': (datetime.now().date() - order.due_date.date()).days if order.due_date else 0
                })
                
            return {
                'overview': {
                    'total_students': total_students,
                    'total_classes': len(class_stats_data),
                    'overdue_count': len(overdue_data)
                },
                'class_stats': class_stats_data,
                'class_payment_stats': class_payment_stats,
                'overdue_students': overdue_data
            }
            
        except Exception as e:
            print(f"Error getting teacher dashboard: {e}")
            return {}
            
    def get_parent_dashboard(self, parent_user_id: int) -> Dict:
        """Dashboard cho Phụ huynh - chỉ xem thông tin của con mình"""
        try:
            # Lấy danh sách học sinh của phụ huynh
            students = self.db.query(Student).filter(Student.user_id == parent_user_id).all()
            student_ids = [s.id for s in students]
            
            if not student_ids:
                return {'students': [], 'orders': [], 'payments': []}
            
            # Thống kê đơn hàng
            total_orders = self.db.query(Order).filter(
                Order.student_id.in_(student_ids)
            ).count()
            
            pending_orders = self.db.query(Order).filter(
                and_(
                    Order.student_id.in_(student_ids),
                    Order.status == OrderStatus.PENDING
                )
            ).count()
            
            paid_orders = self.db.query(Order).filter(
                and_(
                    Order.student_id.in_(student_ids),
                    Order.status.in_([OrderStatus.PAID, OrderStatus.INVOICED])
                )
            ).count()
            
            # Tổng số tiền đã thanh toán
            total_paid = self.db.query(func.sum(Payment.amount)).join(Order).filter(
                and_(
                    Order.student_id.in_(student_ids),
                    Payment.status == PaymentStatus.SUCCESS
                )
            ).scalar() or Decimal('0')
            
            # Tổng số tiền chưa thanh toán
            total_pending = self.db.query(func.sum(Order.amount)).filter(
                and_(
                    Order.student_id.in_(student_ids),
                    Order.status == OrderStatus.PENDING
                )
            ).scalar() or Decimal('0')
            
            # Danh sách đơn hàng chưa thanh toán
            pending_orders_detail = self.db.query(Order, Student).join(
                Student, Order.student_id == Student.id
            ).filter(
                and_(
                    Order.student_id.in_(student_ids),
                    Order.status == OrderStatus.PENDING
                )
            ).order_by(Order.due_date.asc()).all()
            
            pending_data = []
            for order, student in pending_orders_detail:
                is_overdue = order.due_date and order.due_date < datetime.now()
                pending_data.append({
                    'order_id': order.id,
                    'order_code': order.order_code,
                    'student_name': student.name,
                    'class_name': student.class_name,
                    'description': order.description,
                    'amount': float(order.amount),
                    'due_date': order.due_date.isoformat() if order.due_date else None,
                    'is_overdue': is_overdue
                })
                
            # Lịch sử thanh toán gần đây
            recent_payments = self.db.query(Payment, Order, Student).join(
                Order, Payment.order_id == Order.id
            ).join(
                Student, Order.student_id == Student.id
            ).filter(
                and_(
                    Order.student_id.in_(student_ids),
                    Payment.status == PaymentStatus.SUCCESS
                )
            ).order_by(Payment.paid_at.desc()).limit(10).all()
            
            payment_history = []
            for payment, order, student in recent_payments:
                payment_history.append({
                    'payment_code': payment.payment_code,
                    'student_name': student.name,
                    'description': order.description,
                    'amount': float(payment.amount),
                    'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
                })
                
            # Thông tin học sinh
            students_data = []
            for student in students:
                student_orders = self.db.query(Order).filter(Order.student_id == student.id).count()
                student_paid = self.db.query(Order).filter(
                    and_(
                        Order.student_id == student.id,
                        Order.status.in_([OrderStatus.PAID, OrderStatus.INVOICED])
                    )
                ).count()
                
                students_data.append({
                    'id': student.id,
                    'name': student.name,
                    'student_code': student.student_code,
                    'class_name': student.class_name,
                    'grade': student.grade,
                    'total_orders': student_orders,
                    'paid_orders': student_paid
                })
                
            return {
                'overview': {
                    'total_orders': total_orders,
                    'pending_orders': pending_orders,
                    'paid_orders': paid_orders,
                    'total_paid': float(total_paid),
                    'total_pending': float(total_pending)
                },
                'students': students_data,
                'pending_orders': pending_data,
                'payment_history': payment_history
            }
            
        except Exception as e:
            print(f"Error getting parent dashboard: {e}")
            return {}
            
    def generate_revenue_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        group_by: str = 'day'  # day, week, month
    ) -> Dict:
        """Tạo báo cáo doanh thu theo khoảng thời gian"""
        try:
            # Lấy dữ liệu thanh toán trong khoảng thời gian
            payments = self.db.query(Payment).filter(
                and_(
                    Payment.status == PaymentStatus.SUCCESS,
                    Payment.paid_at >= start_date,
                    Payment.paid_at <= end_date
                )
            ).all()
            
            # Group dữ liệu theo yêu cầu
            grouped_data = {}
            total_revenue = Decimal('0')
            
            for payment in payments:
                if not payment.paid_at:
                    continue
                    
                if group_by == 'day':
                    key = payment.paid_at.date().isoformat()
                elif group_by == 'week':
                    # Lấy thứ 2 của tuần
                    week_start = payment.paid_at.date() - timedelta(days=payment.paid_at.weekday())
                    key = week_start.isoformat()
                elif group_by == 'month':
                    key = payment.paid_at.strftime('%Y-%m')
                else:
                    key = payment.paid_at.date().isoformat()
                    
                if key not in grouped_data:
                    grouped_data[key] = {
                        'revenue': Decimal('0'),
                        'count': 0,
                        'period': key
                    }
                    
                grouped_data[key]['revenue'] += payment.amount
                grouped_data[key]['count'] += 1
                total_revenue += payment.amount
                
            # Convert to list và sort
            revenue_data = []
            for key in sorted(grouped_data.keys()):
                data = grouped_data[key]
                revenue_data.append({
                    'period': key,
                    'revenue': float(data['revenue']),
                    'count': data['count']
                })
                
            return {
                'total_revenue': float(total_revenue),
                'total_transactions': len(payments),
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'group_by': group_by,
                'data': revenue_data
            }
            
        except Exception as e:
            print(f"Error generating revenue report: {e}")
            return {}
            
    def get_collection_report(self, class_name: Optional[str] = None) -> Dict:
        """Báo cáo thu học phí theo lớp"""
        try:
            query = self.db.query(Order, Student, User).join(
                Student, Order.student_id == Student.id
            ).join(
                User, Student.user_id == User.id
            )
            
            if class_name:
                query = query.filter(Student.class_name == class_name)
                
            orders = query.all()
            
            # Tổng hợp dữ liệu
            collection_data = {}
            for order, student, parent in orders:
                class_key = student.class_name
                
                if class_key not in collection_data:
                    collection_data[class_key] = {
                        'class_name': class_key,
                        'total_orders': 0,
                        'paid_orders': 0,
                        'pending_orders': 0,
                        'total_amount': Decimal('0'),
                        'paid_amount': Decimal('0'),
                        'pending_amount': Decimal('0'),
                        'students': set()
                    }
                    
                data = collection_data[class_key]
                data['total_orders'] += 1
                data['total_amount'] += order.amount
                data['students'].add(student.id)
                
                if order.status in [OrderStatus.PAID, OrderStatus.INVOICED]:
                    data['paid_orders'] += 1
                    data['paid_amount'] += order.amount
                else:
                    data['pending_orders'] += 1
                    data['pending_amount'] += order.amount
                    
            # Convert sang list và tính tỷ lệ
            result = []
            for class_key, data in collection_data.items():
                collection_rate = (data['paid_amount'] / data['total_amount'] * 100) if data['total_amount'] > 0 else 0
                
                result.append({
                    'class_name': data['class_name'],
                    'student_count': len(data['students']),
                    'total_orders': data['total_orders'],
                    'paid_orders': data['paid_orders'],
                    'pending_orders': data['pending_orders'],
                    'total_amount': float(data['total_amount']),
                    'paid_amount': float(data['paid_amount']),
                    'pending_amount': float(data['pending_amount']),
                    'collection_rate': round(collection_rate, 2)
                })
                
            # Sort theo tỷ lệ thu
            result.sort(key=lambda x: x['collection_rate'], reverse=True)
            
            return {
                'classes': result,
                'summary': {
                    'total_classes': len(result),
                    'total_amount': sum(c['total_amount'] for c in result),
                    'total_paid': sum(c['paid_amount'] for c in result),
                    'total_pending': sum(c['pending_amount'] for c in result),
                    'overall_rate': round(sum(c['paid_amount'] for c in result) / sum(c['total_amount'] for c in result) * 100, 2) if sum(c['total_amount'] for c in result) > 0 else 0
                }
            }
            
        except Exception as e:
            print(f"Error generating collection report: {e}")
            return {}