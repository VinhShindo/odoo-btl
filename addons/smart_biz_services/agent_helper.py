# agent_helper.py
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_helper import AIHelper
from notif_helper import NotifHelper
from google_helper import GoogleHelper

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class AgentHelper:
    """Agent xử lý lead tự động"""
    
    def __init__(self):
        self.ai = AIHelper()
        self.notification = NotifHelper()
        self.google = GoogleHelper()
    
    def route_lead(self, lead_data: dict, agents_meta: list = None) -> dict:
        """Định tuyến lead sang nhân viên phù hợp."""
        _logger.info('AgentHelper.route_lead called')
        return self.ai.route_lead(
            area=lead_data.get('area', 'Không xác định'),
            industry=lead_data.get('industry', 'Không xác định'),
            customer_type=lead_data.get('customer_type', 'Không xác định'),
            priority=lead_data.get('priority', 'Medium'),
            ai_score=lead_data.get('ai_score', 0.0),
            ai_reason=lead_data.get('ai_reason', ''),
            agents=agents_meta
        )
    
    def process_new_lead(self, customer: dict, requirement_text: str) -> dict:
        """Xử lý lead mới hoàn toàn tự động"""
        _logger.info(f"Agent xử lý lead cho {customer.get('name', 'Unknown')}")
        
        result = {
            'status': 'processing',
            'timestamp': datetime.now().isoformat(),
            'customer': customer.get('name')
        }
        
        try:
            # 1. AI phân tích
            classification = self.ai.classify_customer(requirement_text)
            result['classification'] = classification
            
            # 2. Chọn nhân viên
            employees = customer.get('available_employees', 
                                     ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"])
            employee_name = self.ai.assign_employee(
                customer.get('name', 'Khách hàng'),
                requirement_text,
                employees
            )
            result['employee_name'] = employee_name
            
            # 3. Tạo Google Meet
            meeting_link = self.google.create_meeting(
                customer_email=customer.get('email', ''),
                customer_name=customer.get('name', 'Khách hàng'),
                title=f"Tư vấn {classification.get('industry', 'dịch vụ')} - {customer.get('name', '')}",
                duration_minutes=30
            )
            result['meeting_link'] = meeting_link
            
            # 4. Tạo nội dung tin nhắn
            message = self.ai.generate_customer_message(
                customer_name=customer.get('name', 'Khách hàng'),
                requirement=requirement_text,
                employee_name=employee_name,
                meeting_link=meeting_link
            )
            
            # 5. Gửi thông báo Telegram
            if customer.get('telegram_chat_id'):
                self.notification.send_telegram(
                    customer['telegram_chat_id'],
                    f"Tiếp nhận yêu cầu: {classification.get('industry', 'Tư vấn')}",
                    message
                )
            
            # 6. Gửi email
            if customer.get('email'):
                self.notification.send_email(
                    customer['email'],
                    f"Tiếp nhận yêu cầu: {classification.get('industry', 'Tư vấn')}",
                    message
                )
            
            # 7. Lưu vào Google Sheet
            self.google.add_to_sheet({
                'name': customer.get('name', ''),
                'phone': customer.get('phone', ''),
                'email': customer.get('email', ''),
                'employee_name': employee_name,
                'status': 'New Lead',
                'priority': classification.get('priority', 'Medium')
            })
            
            result['status'] = 'success'
            _logger.info(f"✅ Agent xử lý thành công cho {customer.get('name')}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            _logger.error(f"❌ Agent thất bại: {str(e)}")
        
        return result

    def generate_employee_folder_structure(self, employee_name: str) -> list:
        """Trả về danh sách tên thư mục con cho hồ sơ nhân viên.

        Hàm này có thể được mở rộng để gọi AI nếu cần, nhưng hiện tại
        trả về cấu trúc mặc định.
        """
        try:
            # Có thể dùng AI để gợi ý cấu trúc, ví dụ:
            # suggestion = self.ai.generate_folder_structure(employee_name)
            # nếu không có AI, trả về cấu trúc mặc định
            return [
                '01 - Hồ sơ cá nhân',
                '02 - Hợp đồng',
                '03 - Bằng cấp/chứng chỉ',
                '04 - Đào tạo',
                '05 - Hồ sơ đánh giá'
            ]
        except Exception as e:
            _logger.error('generate_employee_folder_structure lỗi: %s', e)
            return []