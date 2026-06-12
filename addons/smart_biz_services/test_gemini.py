# test_full.py - Form mẫu chuyên nghiệp
import os
import sys
import json
from datetime import datetime, timedelta

# Thêm thư mục hiện tại vào path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ai_helper import AIHelper
from notif_helper import NotifHelper
from google_helper import GoogleHelper
from agent_helper import AgentHelper

# ============ CẤU HÌNH MẶC ĐỊNH (ĐỌC TỪ CONFIG) ============
# Các giá trị này sẽ được lấy từ config.json thay vì hardcode
# ===========================================================

# Tạo văn bản mẫu dài để test tóm tắt
LONG_TEXT = """
Công ty TNHH Sản xuất Giày dép ABC được thành lập từ năm 2010, 
hiện có quy mô 250 nhân viên, doanh thu đạt 150 tỷ đồng/năm. 
Công ty đang vận hành 3 nhà máy tại Bình Dương, Đồng Nai và TP.HCM.

Hiện tại, công ty đang gặp nhiều khó khăn trong việc quản lý sản xuất 
vì các phân xưởng hoạt động độc lập, không có sự kết nối. Việc theo dõi 
nguyên vật liệu nhập kho, sản lượng sản xuất và tồn kho thành phẩm 
đang được quản lý bằng Excel, dẫn đến tình trạng thiếu chính xác và 
chậm trễ trong báo cáo.

Ban lãnh đạo công ty quyết định cần triển khai một hệ thống ERP 
để giải quyết các vấn đề trên. Yêu cầu cụ thể:
1. Quản lý sản xuất theo lệnh sản xuất
2. Quản lý nguyên vật liệu và tồn kho
3. Quản lý đơn hàng và kế hoạch sản xuất
4. Báo cáo real-time theo từng phân xưởng
5. Tích hợp với phần mềm kế toán hiện tại

Ngân sách dự kiến: 500-700 triệu đồng
Thời gian triển khai mong muốn: 4 tháng
Đã có đội ngũ IT nội bộ 5 người để hỗ trợ triển khai.
"""


def clear_screen():
    """Xóa màn hình"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title):
    """In header đẹp"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def print_subheader(title):
    """In subheader"""
    print(f"\n▶ {title}")
    print("-"*50)


def print_success(message):
    """In thông báo thành công"""
    print(f"   ✅ {message}")


def print_error(message):
    """In thông báo lỗi"""
    print(f"   ❌ {message}")


def print_info(message):
    """In thông báo thông tin"""
    print(f"   ℹ️ {message}")


def print_result(success, message, data=None):
    """In kết quả"""
    if success:
        print(f"   ✅ {message}")
        if data:
            print(f"   📄 {data}")
    else:
        print(f"   ❌ {message}")
        if data:
            print(f"   📄 {data}")


def print_meeting_info(meeting_link, meeting_time, calendar_link=None):
    """In thông tin meeting đẹp"""
    print("\n" + "="*70)
    print(" 🎯 THÔNG TIN CUỘC HỌP")
    print("="*70)
    print(f"\n   🔗 LINK GOOGLE MEET:")
    print(f"      {meeting_link}")
    print(f"\n   📅 THỜI GIAN:")
    print(f"      {meeting_time}")
    if calendar_link:
        print(f"\n   📆 GOOGLE CALENDAR:")
        print(f"      {calendar_link}")
    print("\n   ⏰ LƯU Ý:")
    print("      • Hệ thống sẽ tự động nhắc nhở 5 phút trước giờ họp")
    print("      • Hệ thống sẽ tự động mở link khi đến giờ")
    print("      • Vui lòng tham gia đúng giờ để đảm bảo cuộc họp diễn ra suôn sẻ")
    print("\n" + "="*70)


def test_ai_summarize():
    """Test 1: Tóm tắt văn bản với AI"""
    print_header("🤖 TEST 1: AI SUMMARIZE DOCUMENT")
    
    try:
        ai = AIHelper()
        print_info(f"Input text length: {len(LONG_TEXT)} characters")
        
        print_subheader("Summary (max 150 chars):")
        summary_short = ai.summarize_document(LONG_TEXT, max_length=150)
        print_success(summary_short)
        
        print_subheader("Summary (max 300 chars):")
        summary_long = ai.summarize_document(LONG_TEXT, max_length=300)
        print_success(summary_long)
        
        return True
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_ai_classify():
    """Test 2: Phân loại khách hàng"""
    print_header("🏷️ TEST 2: AI CLASSIFY CUSTOMER")
    
    try:
        ai = AIHelper()
        result = ai.classify_customer(LONG_TEXT)
        
        print_subheader("Classification Result:")
        print(f"   • Customer Type: {result.get('customer_type', 'N/A')}")
        print(f"   • Industry: {result.get('industry', 'N/A')}")
        print(f"   • Priority: {result.get('priority', 'N/A')}")
        print(f"   • Estimated Value: {result.get('estimated_value', 'N/A')}")
        
        return True
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_ai_assign_employee():
    """Test 3: Phân công nhân viên"""
    print_header("👥 TEST 3: AI ASSIGN EMPLOYEE")
    
    try:
        ai = AIHelper()
        employees = [
            "Nguyễn Văn A - Chuyên gia ERP, 5 năm kinh nghiệm",
            "Trần Thị B - Chuyên gia sản xuất, 8 năm kinh nghiệm",
            "Lê Văn C - Chuyên gia tư vấn giải pháp, 3 năm kinh nghiệm",
            "Phạm Thị D - Chuyên gia quản lý kho, 6 năm kinh nghiệm"
        ]
        
        print_subheader("Available Employees:")
        for emp in employees:
            print(f"   • {emp}")
        
        result = ai.assign_employee("Công ty ABC", LONG_TEXT, employees)
        print_subheader("Selected Employee:")
        print_success(result)
        
        return True
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_ai_generate_message():
    """Test 4: Tạo tin nhắn cho khách hàng"""
    print_header("💬 TEST 4: AI GENERATE MESSAGE")
    
    try:
        ai = AIHelper()
        
        print("   📌 Message options:")
        print("      1. Dùng nội dung mẫu (demo)")
        print("      2. Nhập nội dung tùy chỉnh")
        choice = input("\n   👉 Your choice (1 or 2): ").strip()
        
        if choice == '2':
            print_subheader("Enter Custom Information:")
            customer_name = input("   Customer name: ").strip() or "Công ty ABC"
            requirement = input("   Requirement: ").strip() or LONG_TEXT[:300]
            employee_name = input("   Employee name: ").strip() or "Nguyễn Văn A"
            meeting_link = input("   Meeting link (optional): ").strip() or "https://meet.google.com/abc-defg-hij"
        else:
            customer_name = "Công ty ABC"
            requirement = LONG_TEXT[:300]
            employee_name = "Nguyễn Văn A"
            meeting_link = "https://meet.google.com/abc-defg-hij"
        
        message = ai.generate_customer_message(
            customer_name=customer_name,
            requirement=requirement,
            employee_name=employee_name,
            meeting_link=meeting_link
        )
        
        print_subheader("Generated Message:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        
        return True
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_ai_sentiment():
    """Test 5: Phân tích cảm xúc"""
    print_header("😊 TEST 5: AI SENTIMENT ANALYSIS")
    
    try:
        ai = AIHelper()
        
        print("   📌 Sentiment options:")
        print("      1. Dùng văn bản mẫu")
        print("      2. Nhập văn bản tùy chỉnh")
        choice = input("\n   👉 Your choice (1 or 2): ").strip()
        
        if choice == '2':
            text = input("   Enter text to analyze: ").strip()
            if not text:
                text = "Rất hài lòng với dịch vụ!"
        else:
            text = "Rất hài lòng với dịch vụ, nhân viên tư vấn nhiệt tình, giải pháp phù hợp!"
        
        result = ai.analyze_sentiment(text)
        
        print_subheader("Analysis Result:")
        print(f"   • Sentiment: {result.get('sentiment', 'N/A')}")
        print(f"   • Score: {result.get('score', 0.5)}")
        print(f"   • Key Points: {result.get('key_points', [])}")
        
        return True
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_telegram():
    """Test 6: Gửi Telegram với form nhập đẹp"""
    print_header("📱 TEST 6: TELEGRAM NOTIFICATION")
    
    try:
        notif = NotifHelper()
        
        # Hiển thị thông tin cấu hình
        print_info(f"Default Chat ID: {notif.default_chat_id}")
        print_info(f"Bot Token: {'✅ Configured' if notif.telegram_token else '❌ Not configured'}")
        
        print("\n   📌 Options:")
        print("      1. Gửi đến Chat ID mặc định (đã cấu hình)")
        print("      2. Nhập Chat ID khác")
        print("      3. Nhập nội dung tin nhắn tùy chỉnh")
        
        choice = input("\n   👉 Your choice (1, 2 or 3): ").strip()
        
        # Xác định chat_id
        if choice == '2':
            chat_id = input("\n   📱 Enter Chat ID: ").strip()
            if not chat_id:
                chat_id = notif.default_chat_id
                print_info(f"Using default chat_id: {chat_id}")
        else:
            chat_id = notif.default_chat_id
            print_info(f"Using default chat_id: {chat_id}")
        
        # Xác định nội dung
        if choice == '3':
            print_subheader("📝 Enter Message Content:")
            title = input("   Title: ").strip() or "Thông báo từ Smart Service"
            print("   Content (Enter để kết thúc, gõ 'END' trên dòng mới):")
            lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                lines.append(line)
            content = "\n".join(lines) if lines else "Xin chào! Đây là tin nhắn test."
        else:
            title = "🎉 THÔNG BÁO TỪ SMART BUSINESS SERVICES"
            content = f"""Xin chào!

📌 Đây là tin nhắn test từ hệ thống Smart Business Services.

⏰ Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
✅ Hệ thống đang hoạt động tốt!

📋 Nội dung: Yêu cầu tư vấn của bạn đã được tiếp nhận.
👤 Nhân viên phụ trách: Nguyễn Văn A
🔗 Link họp: https://meet.google.com/abc-defg-hij

Cảm ơn bạn đã tin tưởng sử dụng dịch vụ!
Trân trọng."""
        
        print_subheader("📤 Sending...")
        result = notif.send_telegram(chat_id, title, content)
        
        if result:
            print_success(f"Telegram sent successfully to {chat_id}")
            print_info("Vui lòng kiểm tra Telegram của bạn!")
        else:
            print_error("Failed to send. Make sure you started a chat with the bot first.")
        
        return result
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_email():
    """Test 7: Gửi Email với form nhập đẹp"""
    print_header("📧 TEST 7: EMAIL NOTIFICATION")
    
    try:
        notif = NotifHelper()
        
        # Hiển thị thông tin cấu hình
        print_info(f"Sender Email: {notif.sender_email}")
        print_info(f"Default Recipient: {notif.default_recipient}")
        print_info(f"SMTP Server: {notif.smtp_server}:{notif.smtp_port}")
        
        print("\n   📌 Options:")
        print("      1. Gửi đến email mặc định (đã cấu hình)")
        print("      2. Nhập email nhận khác")
        print("      3. Nhập nội dung email tùy chỉnh")
        
        choice = input("\n   👉 Your choice (1, 2 or 3): ").strip()
        
        # Xác định email nhận
        if choice == '2':
            to_email = input("\n   📧 Recipient email: ").strip()
            if not to_email:
                to_email = notif.default_recipient
                print_info(f"Using default recipient: {to_email}")
        else:
            to_email = notif.default_recipient
            print_info(f"Using default recipient: {to_email}")
        
        # Xác định nội dung
        if choice == '3':
            print_subheader("📝 Enter Email Content:")
            subject = input("   Subject: ").strip() or "Thông báo từ Smart Service"
            print("   Body (Enter để kết thúc, gõ 'END' trên dòng mới):")
            lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                lines.append(line)
            body = "\n".join(lines) if lines else "Đây là email test từ hệ thống."
            is_html = input("   Use HTML format? (y/n): ").strip().lower() == 'y'
        else:
            subject = "🎉 THÔNG BÁO TỪ SMART BUSINESS SERVICES"
            is_html = True
            body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .footer {{ text-align: center; padding: 10px; color: #666; font-size: 12px; border-top: 1px solid #ddd; }}
                    .button {{ display: inline-block; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
                    .info {{ background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🎉 Smart Business Services</h2>
                        <p>Hệ thống quản lý thông minh</p>
                    </div>
                    <div class="content">
                        <h3>Xin chào Quý khách hàng,</h3>
                        <p>Cảm ơn bạn đã tin tưởng và sử dụng dịch vụ của <b>Smart Business Services</b>.</p>
                        
                        <div class="info">
                            <p><b>📋 Thông tin:</b></p>
                            <ul>
                                <li>Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}</li>
                                <li>Dịch vụ: Tư vấn giải pháp ERP</li>
                                <li>Trạng thái: <span style="color: green;">✅ Đã tiếp nhận</span></li>
                            </ul>
                        </div>
                        
                        <p>Nhân viên phụ trách: <b>Nguyễn Văn A</b> sẽ liên hệ với bạn trong thời gian sớm nhất.</p>
                        
                        <p>Nếu bạn có bất kỳ câu hỏi nào, vui lòng phản hồi email này hoặc liên hệ hotline: <b>1900 XXXX</b>.</p>
                        
                        <p>Trân trọng,<br/><b>Đội ngũ Smart Business Services</b></p>
                    </div>
                    <div class="footer">
                        <p>Email tự động - Vui lòng không phản hồi email này</p>
                        <p>&copy; 2024 Smart Business Services. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        print_subheader("📤 Sending...")
        result = notif.send_email(to_email, subject, body, is_html)
        
        if result:
            print_success(f"Email sent successfully to {to_email}")
            print_info("Vui lòng kiểm tra hộp thư của bạn (cả Spam/Thư rác)!")
        else:
            print_error("Failed to send email")
        
        return result
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_contract_meeting():
    """Test 8: Tạo meeting khi chốt hợp đồng - Form chuyên nghiệp"""
    print_header("📅 TEST 8: CHỐT HỢP ĐỒNG - TẠO LỊCH HỌP")
    
    try:
        google = GoogleHelper()
        notif = NotifHelper()
        
        # Hiển thị thông tin xác thực
        if google._is_authenticated:
            print_success("Google Calendar: ✅ Đã xác thực")
        else:
            print("Google Calendar: ⚠️ Chưa xác thực (sẽ dùng chế độ giả lập)")
        
        print_subheader("⏰ CHỌN THỜI GIAN HỌP")
        print("   1. Họp sau 30 giây (để test auto-open)")
        print("   2. Chọn thời gian cụ thể")
        print("   3. Hệ thống tự đề xuất (sau 2 ngày làm việc, 10:00)")
        
        time_choice = input("\n   👉 Your choice (1, 2 or 3): ").strip()
        
        if time_choice == '1':
            meeting_time = datetime.now() + timedelta(seconds=30)
            print_success(f"Sẽ họp lúc: {meeting_time.strftime('%H:%M:%S %d/%m/%Y')} (sau 30 giây)")
        elif time_choice == '2':
            print_subheader("📅 NHẬP THỜI GIAN CỤ THỂ")
            year = int(input("   Năm (YYYY): ").strip() or datetime.now().year)
            month = int(input("   Tháng (MM): ").strip() or datetime.now().month)
            day = int(input("   Ngày (DD): ").strip() or datetime.now().day)
            hour = int(input("   Giờ (0-23): ").strip() or 10)
            minute = int(input("   Phút (0-59): ").strip() or 0)
            meeting_time = datetime(year, month, day, hour, minute)
            print_success(f"Đã chọn: {meeting_time.strftime('%H:%M %d/%m/%Y')}")
        else:
            meeting_time = None
            print_info("Hệ thống sẽ tự động đề xuất thời gian")
        
        print_subheader("📋 THÔNG TIN HỢP ĐỒNG")
        print("   (Để trống để dùng giá trị mặc định)\n")
        
        contract_data = {
            'contract_id': input("   Mã hợp đồng: ").strip() or f"HD{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'customer_name': input("   Tên khách hàng: ").strip() or "Công ty TNHH ABC",
            'customer_email': input("   Email khách hàng: ").strip() or notif.default_recipient,
            'customer_phone': input("   SĐT khách hàng: ").strip() or "0901234567",
            'employee_name': input("   Tên nhân viên: ").strip() or "Nguyễn Văn A",
            'employee_email': input("   Email nhân viên: ").strip() or notif.sender_email,
            'employee_chat_id': input("   Telegram Chat ID (nhân viên): ").strip() or notif.default_chat_id,
            'meeting_time': meeting_time,
            'duration_minutes': 30,
            'title': f"Ký hợp đồng {input('   Tên hợp đồng: ').strip() or 'Triển khai ERP'}"
        }
        
        print_subheader("⏳ ĐANG XỬ LÝ...")
        result = google.create_contract_meeting(contract_data)
        
        if result.get('success'):
            print_success("Meeting đã được tạo thành công!")
            print_meeting_info(
                meeting_link=result['meeting_link'],
                meeting_time=result['meeting_time'],
                calendar_link=result.get('calendar_link')
            )
            
            # Gửi thông báo qua Telegram cho nhân viên
            print_subheader("📱 GỬI THÔNG BÁO TELEGRAM")
            notif.send_telegram(
                contract_data['employee_chat_id'],
                "📅 LỊCH HỌP ĐƯỢC TẠO",
                f"""
✅ Hợp đồng {contract_data['contract_id']} đã được tạo thành công!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 THÔNG TIN HỢP ĐỒNG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Mã hợp đồng: {contract_data['contract_id']}
• Khách hàng: {contract_data['customer_name']}
• Nhân viên: {contract_data['employee_name']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 LỊCH HỌP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Thời gian: {result['meeting_time']}
• Link họp: {result['meeting_link']}

⏰ Hệ thống sẽ tự động mở link khi đến giờ!
                """
            )
            
            # Gửi email cho khách hàng
            print_subheader("📧 GỬI EMAIL CHO KHÁCH HÀNG")
            notif.send_email(
                contract_data['customer_email'],
                f"📅 LỊCH HỌP - Hợp đồng {contract_data['contract_id']}",
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        .container {{ max-width: 600px; margin: 0 auto; }}
                        .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                        .content {{ padding: 20px; }}
                        .meeting-info {{ background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                        .button {{ background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                        .footer {{ text-align: center; padding: 15px; color: #666; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>🎉 THÔNG BÁO LỊCH HỌP</h2>
                        </div>
                        <div class="content">
                            <h3>Kính gửi {contract_data['customer_name']},</h3>
                            <p>Hợp đồng <b>{contract_data['contract_id']}</b> đã được tạo thành công.</p>
                            
                            <div class="meeting-info">
                                <h3>📅 Thông tin cuộc họp:</h3>
                                <ul>
                                    <li><b>Thời gian:</b> {result['meeting_time']}</li>
                                    <li><b>Thời lượng:</b> {contract_data['duration_minutes']} phút</li>
                                    <li><b>Nhân viên phụ trách:</b> {contract_data['employee_name']}</li>
                                </ul>
                                <p style="margin-top: 15px;">
                                    <a href="{result['meeting_link']}" class="button">🔗 Tham gia cuộc họp</a>
                                </p>
                            </div>
                            
                            <p><b>Lưu ý:</b></p>
                            <ul>
                                <li>Vui lòng tham gia đúng giờ</li>
                                <li>Kiểm tra microphone và camera trước khi tham gia</li>
                                <li>Click vào link trên để tham gia cuộc họp</li>
                            </ul>
                            
                            <p>Trân trọng cảm ơn!<br/><b>Đội ngũ Smart Business Services</b></p>
                        </div>
                        <div class="footer">
                            <p>Email tự động - Vui lòng không phản hồi email này</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                is_html=True
            )
            
            if time_choice == '1':
                print_success("⏰ Sẽ tự động mở link trong trình duyệt sau 30 giây!")
        else:
            print_error("Tạo meeting thất bại")
        
        return result.get('success', False)
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_agent():
    """Test 9: Agent Full Flow"""
    print_header("🚀 TEST 9: AGENT FULL FLOW")
    
    try:
        agent = AgentHelper()
        
        print("   📌 Options:")
        print("      1. Dùng thông tin mẫu (demo nhanh)")
        print("      2. Nhập thông tin khách hàng thực")
        choice = input("\n   👉 Your choice (1 or 2): ").strip()
        
        if choice == '2':
            print_subheader("📋 NHẬP THÔNG TIN KHÁCH HÀNG")
            customer = {
                'name': input("   Tên khách hàng: ").strip() or "Công ty ABC",
                'email': input("   Email khách hàng: ").strip() or "customer@example.com",
                'phone': input("   SĐT khách hàng: ").strip() or "0901234567",
                'telegram_chat_id': input("   Telegram Chat ID: ").strip() or "",
            }
            
            print_subheader("📝 NHẬP YÊU CẦU")
            requirement = input("   Yêu cầu (Enter để dùng mẫu): ").strip()
            if not requirement:
                requirement = "Tôi cần triển khai ERP cho công ty sản xuất giày dép với 200 nhân viên, ngân sách 500 triệu, mong muốn demo trong tuần này."
                print_info("Đã dùng yêu cầu mẫu")
        else:
            customer = {
                'name': 'Công ty ABC',
                'email': 'customer@example.com',
                'phone': '0901234567',
                'telegram_chat_id': '',
                'available_employees': [
                    "Nguyễn Văn A - Chuyên gia ERP",
                    "Trần Thị B - Chuyên gia CRM",
                    "Lê Văn C - Chuyên gia tư vấn"
                ]
            }
            requirement = "Tôi cần triển khai ERP cho công ty sản xuất giày dép với 200 nhân viên, ngân sách 500 triệu, mong muốn demo trong tuần này."
        
        print_subheader("⏳ ĐANG XỬ LÝ...")
        result = agent.process_new_lead(customer, requirement)
        
        print_subheader("📊 KẾT QUẢ XỬ LÝ")
        print(f"   • Status: {'✅ Thành công' if result.get('status') == 'success' else '❌ Thất bại'}")
        
        classification = result.get('classification', {})
        print(f"   • Loại khách hàng: {classification.get('customer_type', 'N/A')}")
        print(f"   • Lĩnh vực: {classification.get('industry', 'N/A')}")
        print(f"   • Mức độ ưu tiên: {classification.get('priority', 'N/A')}")
        print(f"   • Nhân viên phụ trách: {result.get('employee_name', 'N/A')}")
        print(f"   • Link họp: {result.get('meeting_link', 'N/A')}")
        
        if result.get('error'):
            print_error(f"Error: {result.get('error')}")
        
        return result.get('status') == 'success'
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def show_menu():
    """Hiển thị menu chính đẹp"""
    print("\n" + "="*70)
    print(" 🏢 SMART BUSINESS SERVICES - HỆ THỐNG QUẢN LÝ THÔNG MINH")
    print("="*70)
    
    menu_items = [
        ("1", "🤖 AI - Tóm tắt văn bản (Summarize)"),
        ("2", "🤖 AI - Phân loại khách hàng (Classify)"),
        ("3", "🤖 AI - Phân công nhân viên (Assign)"),
        ("4", "🤖 AI - Tạo tin nhắn (Generate)"),
        ("5", "🤖 AI - Phân tích cảm xúc (Sentiment)"),
        ("6", "📱 TELEGRAM - Gửi thông báo"),
        ("7", "📧 EMAIL - Gửi thông báo"),
        ("8", "📅 CONTRACT MEETING - Tạo lịch họp khi chốt hợp đồng ⭐"),
        ("9", "🚀 AGENT - Xử lý tự động toàn bộ quy trình"),
        ("0", "❌ Thoát")
    ]
    
    for key, name in menu_items:
        print(f"   {key}. {name}")
    
    print("\n" + "-"*70)
    print("   💡 Gợi ý: Chọn 8 để test chức năng chính (Chốt hợp đồng + Tạo meeting)")
    print("="*70)


def main():
    """Hàm chính"""
    clear_screen()
    
    print("\n" + "="*70)
    print(" 🚀 SMART BUSINESS SERVICES - HỆ THỐNG QUẢN LÝ THÔNG MINH")
    print("="*70)
    print("\n📌 HỆ THỐNG BAO GỒM:")
    print("   • 🤖 AI: Tóm tắt, phân loại, phân công nhân viên, sinh tin nhắn")
    print("   • 📱 TELEGRAM: Gửi thông báo qua Telegram")
    print("   • 📧 EMAIL: Gửi thông báo qua Email")
    print("   • 📅 GOOGLE MEET: Tạo lịch họp tự động")
    print("   • 🚀 AGENT: Xử lý tự động toàn bộ quy trình")
    
    tests_map = {
        '1': test_ai_summarize,
        '2': test_ai_classify,
        '3': test_ai_assign_employee,
        '4': test_ai_generate_message,
        '5': test_ai_sentiment,
        '6': test_telegram,
        '7': test_email,
        '8': test_contract_meeting,
        '9': test_agent,
    }
    
    while True:
        show_menu()
        choice = input("\n👉 Vui lòng chọn chức năng (0-9): ").strip()
        
        if choice == '0':
            print("\n👋 Cảm ơn bạn đã sử dụng Smart Business Services!")
            print("   Hẹn gặp lại!\n")
            break
        
        if choice in tests_map:
            clear_screen()
            tests_map[choice]()
            
            print("\n" + "-"*50)
            input("🔄 Nhấn Enter để tiếp tục...")
            clear_screen()
        else:
            print_error("Lựa chọn không hợp lệ! Vui lòng chọn 0-9")
            input("Nhấn Enter để thử lại...")


if __name__ == '__main__':
    main()