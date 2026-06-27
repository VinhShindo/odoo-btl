# models/notification_templates.py
from datetime import datetime

class NotificationTemplates:
    """Template chuẩn cho email và telegram"""
    
    # Cấu hình công ty (cần điều chỉnh theo thực tế)
    COMPANY_NAME = "Công ty Cổ phần Công nghệ SmartBiz"
    COMPANY_LOGO_URL = "https://your-domain.com/logo.png"  # Thay bằng URL thật
    COMPANY_PHONE = "024.1234.5678"
    COMPANY_EMAIL = "contact@smartbiz.vn"
    COMPANY_WEBSITE = "https://smartbiz.vn"
    COMPANY_ADDRESS = "Tầng 12, Tòa nhà VTC, Số 23 Lê Trọng Tấn, Hà Nội"
    
    # Mapping trạng thái
    STATUS_VN = {
        'tiem_nang': 'Tiềm năng - Đang đánh giá',
        'da_xac_thuc': 'Đã xác thực - Chờ tư vấn',
        'dang_tu_van': 'Đang tư vấn - Đã liên hệ',
        'da_gui_bao_gia': 'Đã gửi báo giá - Chờ phản hồi',
        'dam_phan': 'Đàm phán - Thương lượng hợp đồng',
        'sap_ky_hd': 'Sắp ký hợp đồng - Hoàn thiện thủ tục',
        'thanh_cong': 'Thành công - Đã ký hợp đồng',
        'that_bai': 'Đã kết thúc - Không thành công'
    }
    
    NEXT_STEP_VN = {
        'tiem_nang': 'Chúng tôi sẽ liên hệ để xác thực nhu cầu chi tiết',
        'da_xac_thuc': 'Chuyên viên tư vấn sẽ gọi điện để tư vấn giải pháp',
        'dang_tu_van': 'Tiếp tục trao đổi và hoàn thiện báo giá',
        'da_gui_bao_gia': 'Vui lòng xem xét báo giá và phản hồi',
        'dam_phan': 'Lên lịch họp đàm phán các điều khoản',
        'sap_ky_hd': 'Hoàn thiện hồ sơ và tiến hành ký kết',
        'thanh_cong': 'Triển khai dịch vụ theo hợp đồng',
        'that_bai': 'Xin phép lưu hồ sơ để hợp tác sau'
    }
    
    @classmethod
    def get_status_display(cls, status_code):
        return cls.STATUS_VN.get(status_code, status_code)
    
    @classmethod
    def get_next_step(cls, status_code):
        return cls.NEXT_STEP_VN.get(status_code, 'Chúng tôi sẽ cập nhật sau')


class TelegramTemplates:
    """Template tin nhắn Telegram - Ngắn gọn, súc tích"""
    
    @staticmethod
    def customer_created(customer_name, customer_type, industry, address, 
                         ai_score, ai_reason, employee_name):
        return f"""🏢 **SMARTBIZ - KHÁCH HÀNG MỚI**
━━━━━━━━━━━━━━━━━━━━━━━

📋 **Thông tin khách hàng**
• Họ tên: {customer_name}
• Loại hình: {customer_type}
• Ngành nghề: {industry}
• Địa chỉ: {address}

🎯 **Đánh giá AI**
• Điểm tiềm năng: {ai_score}/100
• Nhận định: {ai_reason}

👤 **Phụ trách**: {employee_name}

⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━
_SmartBiz - Giải pháp chuyển đổi số toàn diện_"""

    @staticmethod
    def customer_status_updated(customer_name, old_status, new_status, 
                                employee_name, next_step):
        return f"""🔄 **CẬP NHẬT TRẠNG THÁI KHÁCH HÀNG**
━━━━━━━━━━━━━━━━━━━━━━━

👤 **Khách hàng**: {customer_name}
📊 **Trạng thái**: {new_status}
👨‍💼 **Phụ trách**: {employee_name}

📌 **Công việc tiếp theo**:
{next_step}

⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━
_SmartBiz - Đồng hành cùng thành công của bạn_"""

    @staticmethod
    def contract_approved(contract_name, customer_name, contract_value, 
                          start_date, end_date, summary):
        # Format số tiền
        value_str = f"{contract_value:,.0f}".replace(',', '.')
        return f"""📄 **HỢP ĐỒNG ĐƯỢC PHÊ DUYỆT**
━━━━━━━━━━━━━━━━━━━━━━━

📑 **Số HĐ**: {contract_name}
👤 **Khách hàng**: {customer_name}
💰 **Giá trị**: {value_str} VNĐ

📅 **Hiệu lực**: {start_date} → {end_date}

📝 **Tóm tắt**:
{summary[:200] + '...' if len(summary) > 200 else summary}

⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━
_SmartBiz - Chuyển đổi số thành công_"""

    @staticmethod
    def document_approved(doc_name, doc_type, customer_name, summary):
        return f"""📁 **VĂN BẢN ĐƯỢC PHÊ DUYỆT**
━━━━━━━━━━━━━━━━━━━━━━━

📄 **Tiêu đề**: {doc_name}
🏷️ **Loại**: {doc_type}
👤 **Khách hàng**: {customer_name or 'N/A'}

📝 **Tóm tắt**:
{summary[:200] + '...' if len(summary) > 200 else summary}

⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━
_SmartBiz - Quản lý văn bản thông minh_"""

    @staticmethod
    def employee_created(employee_name, department, job_title):
        return f"""👥 **NHÂN VIÊN MỚI**
━━━━━━━━━━━━━━━━━━━━━━━

👤 **Họ tên**: {employee_name}
🏢 **Phòng ban**: {department}
📌 **Chức vụ**: {job_title}

📝 Hồ sơ nhân sự đã được tạo trong hệ thống.

⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━
_SmartBiz - Quản trị nhân sự hiệu quả_"""

    @staticmethod
    def quotation_negotiation(quotation_name, customer_name, meeting_link):
        return f"""🤝 **ĐÀM PHÁN BÁO GIÁ**
━━━━━━━━━━━━━━━━━━━━━━━

📄 **Báo giá**: {quotation_name}
👤 **Khách hàng**: {customer_name}

🔗 **Link Google Meet**:
{meeting_link}

📌 Vui lòng tham gia đúng giờ để trao đổi chi tiết.

⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━
_SmartBiz - Giải pháp tối ưu cho doanh nghiệp_"""
    
    @staticmethod
    def customer_reassigned(customer_name, old_employee, new_employee, reason, confidence):
        return f"""🔄 **THAY ĐỔI NGƯỜI PHỤ TRÁCH**
    ━━━━━━━━━━━━━━━━━━━━━━━

    👤 **Khách hàng**: {customer_name}
    👋 **Cũ**: {old_employee}
    ✨ **Mới**: {new_employee}

    📊 **Độ tin cậy**: {int(confidence * 100)}%
    📝 **Lý do**: {reason[:200]}

    ⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
    ━━━━━━━━━━━━━━━━━━━━━━━
    _SmartBiz - Phân công thông minh_"""

    @staticmethod
    def meeting_created(customer_name, meeting_link, reason, meeting_title):
        return f"""📅 **LỊCH HỌP ĐƯỢC TẠO**
    ━━━━━━━━━━━━━━━━━━━━━━━

    👤 **Khách hàng**: {customer_name}
    📌 **Tiêu đề**: {meeting_title}
    📝 **Lý do**: {reason}

    🔗 **Link tham gia**:
    {meeting_link}

    ⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}
    ━━━━━━━━━━━━━━━━━━━━━━━
    _SmartBiz - Tự động tạo lịch họp thông minh_"""


class EmailTemplates:
    """Template email HTML chuyên nghiệp"""
    
    @staticmethod
    def _get_base_html(content_body, title, recipient_name=None):
        """Base HTML template cho mọi email"""
        greeting = f"Xin chào {recipient_name}," if recipient_name else "Xin chào Quý khách,"
        
        return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #f5f7fa;
            line-height: 1.6;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #0052cc 0%, #0066ff 100%);
            padding: 32px 24px;
            text-align: center;
        }}
        .header h1 {{
            color: white;
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .header p {{
            color: rgba(255,255,255,0.9);
            margin: 8px 0 0;
            font-size: 14px;
        }}
        .content {{
            padding: 32px 28px;
        }}
        .greeting {{
            font-size: 16px;
            color: #1a2c3e;
            margin-bottom: 20px;
        }}
        .info-box {{
            background-color: #f0f4f8;
            border-left: 4px solid #0052cc;
            padding: 16px 20px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        .status-badge.potential {{ background: #e8f4f8; color: #00a3c4; }}
        .status-badge.verified {{ background: #e6f7e6; color: #00a86b; }}
        .status-badge.consulting {{ background: #fff3e0; color: #ff9800; }}
        .status-badge.quoted {{ background: #e3f2fd; color: #2196f3; }}
        .status-badge.negotiating {{ background: #f3e5f5; color: #9c27b0; }}
        .status-badge.contracting {{ background: #e8eaf6; color: #3f51b5; }}
        .status-badge.success {{ background: #e8f5e9; color: #4caf50; }}
        .divider {{
            height: 1px;
            background: #e0e6ed;
            margin: 24px 0;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 24px 28px;
            text-align: center;
            font-size: 12px;
            color: #65748c;
            border-top: 1px solid #e0e6ed;
        }}
        .footer a {{
            color: #0052cc;
            text-decoration: none;
        }}
        .button {{
            display: inline-block;
            padding: 12px 28px;
            background: linear-gradient(135deg, #0052cc 0%, #0066ff 100%);
            color: white !important;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 16px 0;
        }}
        .info-row {{
            display: flex;
            margin: 12px 0;
        }}
        .info-label {{
            width: 120px;
            font-weight: 600;
            color: #1a2c3e;
        }}
        .info-value {{
            flex: 1;
            color: #4a5b6e;
        }}
        @media (max-width: 600px) {{
            .content {{ padding: 20px; }}
            .info-row {{ flex-direction: column; }}
            .info-label {{ width: auto; margin-bottom: 4px; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 24px 16px; background-color: #f5f7fa;">
    <div class="container">
        <div class="header">
            <h1>{NotificationTemplates.COMPANY_NAME}</h1>
            <p>Chuyển đổi số toàn diện - Kiến tạo thành công</p>
        </div>
        
        <div class="content">
            <div class="greeting">
                {greeting}
            </div>
            
            {content_body}
            
            <div class="divider"></div>
            
            <div style="font-size: 14px; color: #4a5b6e;">
                <strong>Cần hỗ trợ?</strong><br>
                📞 Hotline: {NotificationTemplates.COMPANY_PHONE}<br>
                📧 Email: {NotificationTemplates.COMPANY_EMAIL}<br>
                🌐 Website: {NotificationTemplates.COMPANY_WEBSITE}
            </div>
        </div>
        
        <div class="footer">
            <p>&copy; {datetime.now().year} {NotificationTemplates.COMPANY_NAME}. Tất cả các quyền được bảo lưu.</p>
            <p>{NotificationTemplates.COMPANY_ADDRESS}</p>
            <p style="margin-top: 12px;">
                <a href="#">Chính sách bảo mật</a> | <a href="#">Điều khoản sử dụng</a>
            </p>
        </div>
    </div>
</body>
</html>"""
    
    @staticmethod
    def customer_status_updated(customer_name, status_code, employee_name, 
                                next_step, note=None, recipient_name=None):
        """Template email cập nhật trạng thái khách hàng"""
        status_display = NotificationTemplates.get_status_display(status_code)
        
        # Map status to badge class
        badge_class = {
            'tiem_nang': 'potential',
            'da_xac_thuc': 'verified',
            'dang_tu_van': 'consulting',
            'da_gui_bao_gia': 'quoted',
            'dam_phan': 'negotiating',
            'sap_ky_hd': 'contracting',
            'thanh_cong': 'success'
        }.get(status_code, 'potential')
        
        content_body = f"""
            <div class="info-box">
                <strong>📢 CẬP NHẬT TRẠNG THÁI HỒ SƠ</strong>
            </div>
            
            <div class="info-row">
                <div class="info-label">Khách hàng:</div>
                <div class="info-value">{customer_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Trạng thái:</div>
                <div class="info-value">
                    <span class="status-badge {badge_class}">{status_display}</span>
                </div>
            </div>
            <div class="info-row">
                <div class="info-label">Người phụ trách:</div>
                <div class="info-value">{employee_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Công việc tiếp theo:</div>
                <div class="info-value">{next_step}</div>
            </div>
            {f'<div class="info-row"><div class="info-label">Ghi chú:</div><div class="info-value">{note}</div></div>' if note else ''}
            
            <div style="margin-top: 24px; padding: 16px; background: #e8f4f8; border-radius: 8px;">
                <strong>💡 Lưu ý:</strong><br>
                Chúng tôi sẽ liên tục cập nhật tiến độ xử lý hồ sơ của Quý khách. 
                Mọi thắc mắc vui lòng liên hệ trực tiếp với nhân viên phụ trách hoặc 
                hotline {NotificationTemplates.COMPANY_PHONE}.
            </div>
        """
        
        return EmailTemplates._get_base_html(
            content_body, 
            f'Cập nhật trạng thái hồ sơ - {customer_name}',
            recipient_name
        )
    
    @staticmethod
    def customer_created(customer_name, customer_type, industry, address,
                        ai_score, ai_reason, employee_name, recipient_name=None):
        """Template email thông báo tạo khách hàng mới (nội bộ)"""
        content_body = f"""
            <div class="info-box">
                <strong>🆕 KHÁCH HÀNG MỚI ĐƯỢC TẠO</strong>
            </div>
            
            <div class="info-row">
                <div class="info-label">Họ tên:</div>
                <div class="info-value">{customer_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Loại hình:</div>
                <div class="info-value">{customer_type}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Ngành nghề:</div>
                <div class="info-value">{industry}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Địa chỉ:</div>
                <div class="info-value">{address}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Phụ trách:</div>
                <div class="info-value">{employee_name}</div>
            </div>
            
            <div class="info-box" style="background: #fff8e6; border-left-color: #ff9800;">
                <strong>🎯 ĐÁNH GIÁ TỪ AI</strong><br>
                • Điểm tiềm năng: <strong>{ai_score}/100</strong><br>
                • Nhận định: {ai_reason}
            </div>
        """
        return EmailTemplates._get_base_html(content_body, 'Khách hàng mới được tạo', recipient_name)
    
    @staticmethod
    def contract_approved(contract_name, customer_name, contract_value, 
                          start_date, end_date, summary, recipient_name=None):
        """Template email thông báo hợp đồng được phê duyệt"""
        value_str = f"{contract_value:,.0f}".replace(',', '.')
        content_body = f"""
            <div class="info-box">
                <strong>✅ HỢP ĐỒNG ĐÃ ĐƯỢC PHÊ DUYỆT</strong>
            </div>
            
            <div class="info-row">
                <div class="info-label">Số hợp đồng:</div>
                <div class="info-value">{contract_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Khách hàng:</div>
                <div class="info-value">{customer_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Giá trị hợp đồng:</div>
                <div class="info-value"><strong>{value_str} VNĐ</strong></div>
            </div>
            <div class="info-row">
                <div class="info-label">Thời hạn hiệu lực:</div>
                <div class="info-value">{start_date} → {end_date}</div>
            </div>
            
            <div class="info-box" style="background: #f0f4f8;">
                <strong>📝 TÓM TẮT HỢP ĐỒNG</strong><br>
                {summary}
            </div>
            
            <div style="text-align: center;">
                <a href="#" class="button">Xem chi tiết hợp đồng</a>
            </div>
        """
        return EmailTemplates._get_base_html(content_body, f'Hợp đồng {contract_name} đã được phê duyệt', recipient_name)
    
    @staticmethod
    def quotation_negotiation(quotation_name, customer_name, meeting_link, 
                              recipient_name=None):
        """Template email thông báo đàm phán báo giá"""
        content_body = f"""
            <div class="info-box">
                <strong>🤝 LỜI MỜI ĐÀM PHÁN BÁO GIÁ</strong>
            </div>
            
            <div class="info-row">
                <div class="info-label">Báo giá số:</div>
                <div class="info-value">{quotation_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Khách hàng:</div>
                <div class="info-value">{customer_name}</div>
            </div>
            
            <div class="info-box" style="background: #e8f4f8; text-align: center;">
                <strong>🔗 THAM GIA CUỘC HỌP TRỰC TUYẾN</strong><br>
                <a href="{meeting_link}" class="button" style="margin: 12px 0;">Tham gia Google Meet</a>
                <p style="font-size: 13px; margin-top: 8px;">
                    Nút bấm không hoạt động? Sao chép link sau vào trình duyệt:<br>
                    <a href="{meeting_link}" style="word-break: break-all;">{meeting_link}</a>
                </p>
            </div>
            
            <div style="margin-top: 20px;">
                <strong>📌 Lưu ý:</strong><br>
                - Vui lòng tham gia cuộc họp đúng giờ để trao đổi chi tiết.<br>
                - Đảm bảo thiết bị có microphone và camera để cuộc trao đổi hiệu quả.<br>
                - Có thể sử dụng Google Meet trên điện thoại qua ứng dụng Google Meet.
            </div>
        """
        return EmailTemplates._get_base_html(content_body, f'Lời mời đàm phán - Báo giá {quotation_name}', recipient_name)

    @staticmethod
    def employee_created(employee_name, department, job_title, recipient_name=None):
        """Template email thông báo nhân viên mới được tạo"""
        content_body = f"""
            <div class="info-box">
                <strong>👥 NHÂN VIÊN MỚI ĐƯỢC TẠO</strong>
            </div>
            
            <div class="info-row">
                <div class="info-label">Họ tên:</div>
                <div class="info-value">{employee_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Phòng ban:</div>
                <div class="info-value">{department}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Chức vụ:</div>
                <div class="info-value">{job_title}</div>
            </div>
            
            <div style="margin-top: 20px; padding: 16px; background: #e8f4f8; border-radius: 8px;">
                <strong>📌 Hướng dẫn:</strong><br>
                - Vui lòng kiểm tra và cập nhật đầy đủ thông tin hồ sơ nhân viên<br>
                - Phân công khách hàng và nhiệm vụ phù hợp<br>
                - Cấp quyền truy cập hệ thống theo chức năng công việc
            </div>
        """
        return EmailTemplates._get_base_html(
            content_body, 
            f'Chào mừng {employee_name} gia nhập {NotificationTemplates.COMPANY_NAME}',
            recipient_name or employee_name
        )

    @staticmethod
    def employee_updated(employee_name, department, job_title, manager, recipient_name=None):
        """Template email thông báo cập nhật thông tin nhân viên"""
        content_body = f"""
            <div class="info-box">
                <strong>🔄 CẬP NHẬT THÔNG TIN NHÂN VIÊN</strong>
            </div>
            
            <div class="info-row">
                <div class="info-label">Họ tên:</div>
                <div class="info-value">{employee_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Phòng ban:</div>
                <div class="info-value">{department}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Chức vụ:</div>
                <div class="info-value">{job_title}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Quản lý trực tiếp:</div>
                <div class="info-value">{manager}</div>
            </div>
            
            <div style="margin-top: 20px; padding: 16px; background: #e8f4f8; border-radius: 8px;">
                <strong>📌 Lưu ý:</strong><br>
                - Vui lòng kiểm tra lại thông tin cá nhân trên hệ thống<br>
                - Cập nhật chữ ký email nếu có thay đổi chức vụ
            </div>
        """
        return EmailTemplates._get_base_html(
            content_body,
            f'Cập nhật thông tin nhân viên - {employee_name}',
            recipient_name or employee_name
        )

    @staticmethod
    def document_approved(doc_name, doc_type, customer_name, summary, recipient_name=None):
        """Template email thông báo văn bản được phê duyệt"""
        content_body = f"""
            <div class="info-box">
                <strong>📄 VĂN BẢN ĐÃ ĐƯỢC PHÊ DUYỆT</strong>
            </div>
            
            <div class="info-row">
                <div class="info-label">Tiêu đề:</div>
                <div class="info-value">{doc_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Loại văn bản:</div>
                <div class="info-value">{doc_type}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Khách hàng:</div>
                <div class="info-value">{customer_name or 'N/A'}</div>
            </div>
            
            <div class="info-box" style="background: #f0f4f8;">
                <strong>📝 TÓM TẮT NỘI DUNG</strong><br>
                {summary}
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <a href="#" class="button">Tải xuống văn bản</a>
            </div>
        """
        return EmailTemplates._get_base_html(
            content_body, 
            f'Văn bản {doc_name} đã được phê duyệt',
            recipient_name
        )
    
    @staticmethod
    def meeting_invitation(customer_name, meeting_link, title, reason, recipient_name=None):
        """Template email mời họp chuyên nghiệp"""
        greeting = f"Xin chào {recipient_name or customer_name},"
        
        return f"""<!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lời mời họp trực tuyến - {title}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f5f7fa;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #0052cc 0%, #0066ff 100%);
                padding: 32px 24px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 32px 28px;
            }}
            .info-box {{
                background-color: #f0f4f8;
                border-left: 4px solid #0052cc;
                padding: 16px 20px;
                margin: 20px 0;
                border-radius: 8px;
            }}
            .button {{
                display: inline-block;
                padding: 14px 32px;
                background: linear-gradient(135deg, #0052cc 0%, #0066ff 100%);
                color: white !important;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                margin: 16px 0;
            }}
            .footer {{
                background-color: #f8fafc;
                padding: 24px 28px;
                text-align: center;
                font-size: 12px;
                color: #65748c;
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 24px 16px; background-color: #f5f7fa;">
        <div class="container">
            <div class="header">
                <h1>{NotificationTemplates.COMPANY_NAME}</h1>
                <p>Chuyển đổi số toàn diện - Kiến tạo thành công</p>
            </div>
            
            <div class="content">
                <p style="font-size: 16px; color: #1a2c3e;">{greeting}</p>
                
                <div class="info-box">
                    <strong>📅 THÔNG TIN CUỘC HỌP</strong>
                </div>
                
                <table width="100%" cellpadding="10" cellspacing="0">
                    <tr>
                        <td width="120" style="font-weight: 600;">Tiêu đề:</td>
                        <td>{title}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Lý do:</td>
                        <td>{reason}</td>
                    </tr>
                </table>
                
                <div class="info-box" style="background: #e8f4f8; text-align: center;">
                    <strong>🔗 THAM GIA CUỘC HỌP</strong><br>
                    <a href="{meeting_link}" class="button">Tham gia Google Meet</a>
                    <p style="font-size: 13px; margin-top: 12px;">
                        Hoặc sao chép link: <a href="{meeting_link}" style="word-break: break-all;">{meeting_link}</a>
                    </p>
                </div>
                
                <div style="margin-top: 24px; padding: 16px; background: #fff8e6; border-radius: 8px;">
                    <strong>📌 Lưu ý:</strong><br>
                    • Vui lòng tham gia đúng giờ để cuộc họp diễn ra hiệu quả<br>
                    • Đảm bảo thiết bị có microphone và camera<br>
                    • Có thể tham gia qua ứng dụng Google Meet trên điện thoại
                </div>
            </div>
            
            <div class="footer">
                <p>&copy; {datetime.now().year} {NotificationTemplates.COMPANY_NAME}</p>
                <p>Hotline: {NotificationTemplates.COMPANY_PHONE} | Email: {NotificationTemplates.COMPANY_EMAIL}</p>
            </div>
        </div>
    </body>
    </html>"""