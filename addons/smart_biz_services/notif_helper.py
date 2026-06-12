# notif_helper.py
import requests
import logging
import os
import sys
import smtplib
from email.message import EmailMessage
import ssl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_helper import config

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class NotifHelper:
    """Service gửi thông báo Telegram và Email"""
    
    def __init__(self):
        # Lấy từ config
        self.telegram_token = config.telegram_bot_token
        self.default_chat_id = config.telegram_default_chat_id
        
        self.smtp_server = config.email_smtp_server
        self.smtp_port = config.email_smtp_port
        self.sender_email = config.email_sender
        self.sender_password = config.email_app_password
        self.default_recipient = config.email_default_recipient
    
    def send_telegram(self, chat_id: str = None, title: str = "", content: str = "", use_default: bool = True) -> bool:
        """
        Gửi tin nhắn Telegram
        
        Args:
            chat_id: ID người nhận (nếu None và use_default=True thì dùng default)
            title: Tiêu đề tin nhắn
            content: Nội dung tin nhắn
            use_default: Cho phép dùng default chat_id nếu không có chat_id
        """
        # Xác định chat_id
        target_chat_id = chat_id
        if not target_chat_id and use_default:
            target_chat_id = self.default_chat_id
            _logger.info(f"📱 Using default chat_id: {target_chat_id}")
        
        if not target_chat_id:
            _logger.warning("⚠️ No chat_id provided and no default configured")
            return False
        
        if not self.telegram_token:
            _logger.warning("⚠️ Telegram bot token not configured")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        message = f"{title}\n\n{content}"
        
        try:
            response = requests.post(url, json={
                'chat_id': target_chat_id,
                'text': message,
            }, timeout=10)
            
            success = response.status_code == 200
            if success:
                _logger.info(f"✅ Telegram sent to {target_chat_id}")
            else:
                error_msg = response.json() if response.text else {}
                _logger.error(f"❌ Telegram failed: {error_msg.get('description', 'Unknown error')}")
            return success
        except Exception as e:
            _logger.error(f"❌ Telegram error: {str(e)}")
            return False
    
    def send_email(self, to_email: str = None, subject: str = "", body: str = "", 
                   is_html: bool = True, use_default: bool = True) -> bool:
        """
        Gửi email
        
        Args:
            to_email: Email người nhận (nếu None và use_default=True thì dùng default)
            subject: Tiêu đề email
            body: Nội dung email
            is_html: Nội dung có phải HTML không
            use_default: Cho phép dùng default recipient nếu không có to_email
        """
        # Xác định email nhận
        target_email = to_email
        if not target_email and use_default:
            target_email = self.default_recipient
            _logger.info(f"📧 Using default recipient: {target_email}")
        
        if not target_email:
            _logger.warning("⚠️ No recipient email provided and no default configured")
            return False
        
        if not self.sender_email or not self.sender_password:
            _logger.warning("⚠️ Email credentials not configured")
            return False
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = target_email
        
        if is_html:
            msg.set_content("Vui lòng xem email này dưới dạng HTML.")
            msg.add_alternative(body, subtype='html')
        else:
            msg.set_content(body)
        
        context = ssl.create_default_context()
        
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            _logger.info(f"✅ Email sent to {target_email}")
            return True
        except Exception as e:
            _logger.error(f"❌ Email failed: {e}")
            return False