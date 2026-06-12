# ai_helper.py
import json
import re
import logging
import requests
import os
import sys

# Đảm bảo import được config_helper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_helper import config

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class AIHelper:
    """Service AI sử dụng Gemini"""
    
    def __init__(self):
        self.api_key = config.gemini_api_key
        self.model = config.gemini_model
        self._base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
    
    def _call_gemini(self, prompt: str, max_tokens: int = 500) -> str:
        """Gọi Gemini API"""
        if not self.api_key:
            _logger.warning("Gemini API key not configured")
            return None
        
        url = f"{self._base_url}?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                _logger.error(f"Gemini API error: {response.status_code}")
                return None
        except Exception as e:
            _logger.error(f"Gemini API failed: {str(e)}")
            return None
    
    def summarize_document(self, text: str, max_length: int = 200) -> str:
        """Tóm tắt văn bản"""
        if not text or len(text) < 50:
            return text
        
        prompt = f"""
        Bạn là trợ lý AI chuyên nghiệp. Hãy tóm tắt văn bản sau bằng tiếng Việt, 
        ngắn gọn nhưng vẫn giữ được ý chính. Tóm tắt không quá {max_length} ký tự.
        
        Văn bản cần tóm tắt:
        {text[:3000]}
        
        Tóm tắt:
        """
        
        result = self._call_gemini(prompt, max_tokens=300)
        if result:
            if len(result) > max_length:
                result = result[:max_length] + "..."
            return result
        
        return text[:max_length] + ("..." if len(text) > max_length else "")
    
    def classify_customer(self, text: str) -> dict:
        """Phân loại khách hàng"""
        prompt = f"""
        Phân tích yêu cầu của khách hàng sau và trả về JSON với các trường:
        - customer_type: loại khách hàng (Enterprise/SME/Startup/Individual)
        - industry: lĩnh vực (ERP/CRM/Ecommerce/HRM/Accounting/Other)
        - priority: mức độ ưu tiên (High/Medium/Low)
        - estimated_value: giá trị ước tính (High/Medium/Low)
        
        Yêu cầu của khách hàng:
        {text[:2000]}
        
        Chỉ trả về JSON, không có text khác:
        """
        
        result = self._call_gemini(prompt, max_tokens=200)
        if result:
            try:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return {
            'customer_type': 'SME',
            'industry': 'Other',
            'priority': 'Medium',
            'estimated_value': 'Medium'
        }

    def evaluate_customer_profile(self, customer_name: str, customer_type: str,
                                  source: str, industry: str,
                                  address: str, description: str) -> dict:
        """Đánh giá hồ sơ khách hàng và trả về điểm AI cùng lý do."""
        prompt = f"""
        Bạn là trợ lý AI chuyên nghiệp. Dựa vào dữ liệu khách hàng, hãy đánh giá hồ sơ sau
        và trả về một JSON duy nhất với hai trường:
        - ai_score: điểm từ 0 đến 100
        - ai_reason: lý do ngắn gọn bằng tiếng Việt

        Dữ liệu khách hàng:
        - Tên: {customer_name}
        - Loại khách hàng: {customer_type}
        - Nguồn: {source}
        - Ngành nghề: {industry}
        - Địa chỉ: {address}
        - Mô tả: {description}

        Chỉ trả về JSON, không có text giải thích khác:
        """

        result = self._call_gemini(prompt, max_tokens=250)
        if result:
            try:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return {
                        'ai_score': float(parsed.get('ai_score', 0)) if parsed.get('ai_score') is not None else 0.0,
                        'ai_reason': str(parsed.get('ai_reason', '')).strip()
                    }
            except Exception:
                pass

        return {
            'ai_score': 0.0,
            'ai_reason': 'Không đánh giá được do AI không trả về kết quả hợp lệ.'
        }

    def route_lead(self, area: str, industry: str, customer_type: str,
                   priority: str, ai_score: float, ai_reason: str,
                   agents: list = None) -> dict:
        """Chọn nhân viên tốt nhất dựa trên lead routing."""
        if agents is None:
            agents = []

        agents_text = ""
        if agents:
            details = []
            for agent in agents:
                details.append(
                    f"- user_id: {agent.get('user_id', '')}, name: {agent.get('name', '')}, "
                    f"job: {agent.get('job', 'Unknown')}, department: {agent.get('department', 'Unknown')}, "
                    f"region: {agent.get('region', 'Unknown')}, load: {agent.get('load', 'Unknown')}"
                )
            agents_text = "\n".join(details)
        else:
            agents_text = "- none"

        prompt = f"""
        Bạn là hệ thống định tuyến lead.
        Dựa trên thông tin sau, hãy chọn nhân viên phù hợp nhất.

        Dữ liệu lead:
        - Khu vực: {area}
        - Ngành nghề: {industry}
        - Loại khách hàng: {customer_type}
        - Độ ưu tiên: {priority}
        - AI score: {ai_score}
        - AI reason: {ai_reason}

        Danh sách nhân viên:
        {agents_text}

        Hãy trả về một JSON duy nhất với các trường:
        - employee_id: id của nhân viên được chọn
        - confidence: số từ 0 đến 1
        - reason: lý do ngắn gọn

        Nếu không thể chọn được hoặc confidence thấp, trả về confidence 0 và employee_id null.
        Chỉ trả về JSON, không có text khác.
        """

        result = self._call_gemini(prompt, max_tokens=250)
        if result:
            try:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    employee_id = parsed.get('employee_id')
                    if employee_id is not None and str(employee_id).isdigit():
                        employee_id = int(employee_id)
                    else:
                        employee_id = None
                    confidence = parsed.get('confidence', 0.0) or 0.0
                    return {
                        'employee_id': employee_id,
                        'confidence': float(confidence),
                        'reason': str(parsed.get('reason', '')).strip()
                    }
            except Exception:
                pass

        return {
            'employee_id': None,
            'confidence': 0.0,
            'reason': 'Không xác định'
        }
    
    def assign_employee(self, customer_name: str, requirement_text: str, 
                        employees: list = None) -> str:
        """Chọn nhân viên phù hợp"""
        if employees is None:
            employees = ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"]
        
        if len(employees) == 1:
            return employees[0]
        
        prompt = f"""
        Bạn là quản lý nhân sự. Dựa vào yêu cầu của khách hàng, hãy chọn nhân viên phù hợp nhất.
        
        Danh sách nhân viên:
        {chr(10).join([f'- {e}' for e in employees])}
        
        Khách hàng: {customer_name}
        Yêu cầu: {requirement_text[:500]}
        
        Hãy chọn MỘT người phù hợp nhất và chỉ trả về TÊN CHÍNH XÁC của người đó.
        """
        
        result = self._call_gemini(prompt, max_tokens=50)
        if result:
            for emp in employees:
                if emp.lower() in result.lower():
                    return emp
        
        return employees[0]
    
    def generate_customer_message(self, customer_name: str, requirement: str,
                                  employee_name: str, meeting_link: str = None) -> str:
        """Tạo tin nhắn cho khách hàng"""
        prompt = f"""
        Bạn là nhân viên chăm sóc khách hàng. Tạo tin nhắn thông báo bằng tiếng Việt, 
        thân thiện và chuyên nghiệp với nội dung:
        
        - Gửi đến khách hàng: {customer_name}
        - Yêu cầu của khách: {requirement[:500]}
        - Nhân viên phụ trách: {employee_name}
        - Link Google Meet: {meeting_link or 'chưa được tạo'}
        
        Tin nhắn cần có: Lời chào, xác nhận yêu cầu, thông tin nhân viên, link họp, lời cảm ơn.
        
        Tin nhắn:
        """
        
        result = self._call_gemini(prompt, max_tokens=400)
        if result:
            return result.strip()

        meeting_text = f"\n\nLink Google Meet: {meeting_link}" if meeting_link else ""
        return f"""
Xin chào {customer_name},

Cảm ơn bạn đã liên hệ. Yêu cầu của bạn đã được tiếp nhận.

Nhân viên phụ trách: {employee_name}{meeting_text}

Chúng tôi sẽ liên hệ lại sớm nhất.

Trân trọng,
Đội ngũ hỗ trợ
"""

    def generate_message(self, customer_name: str, requirement: str,
                         employee_name: str, meeting_link: str = None) -> str:
        """Alias cho dịch vụ generate_message hiện có."""
        return self.generate_customer_message(
            customer_name=customer_name,
            requirement=requirement,
            employee_name=employee_name,
            meeting_link=meeting_link,
        )
    
    def analyze_sentiment(self, text: str) -> dict:
        """Phân tích cảm xúc"""
        prompt = f"""
        Phân tích cảm xúc văn bản sau, trả về JSON:
        - sentiment: positive/negative/neutral
        - score: float 0-1
        - key_points: list các điểm chính
        
        Văn bản: {text[:1000]}
        
        JSON:
        """
        
        result = self._call_gemini(prompt, max_tokens=200)
        if result:
            try:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return {'sentiment': 'neutral', 'score': 0.5, 'key_points': []}