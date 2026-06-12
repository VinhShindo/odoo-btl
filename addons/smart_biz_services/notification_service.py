# notification_service.py
import requests
import logging
from .config_helper import config

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class NotificationService:
    """Service gửi thông báo Telegram - Hoàn toàn độc lập"""
    
    def __init__(self):
        self.telegram_token = config.telegram_bot_token
    
    def send_telegram(self, chat_id: str, title: str, content: str) -> bool:
        """Gửi tin nhắn Telegram"""
        if not self.telegram_token:
            _logger.warning("Telegram bot token not configured")
            return False
        
        if not chat_id:
            _logger.warning("No chat_id provided")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        message = f"*{title}*\n\n{content}"
        
        try:
            response = requests.post(url, json={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }, timeout=10)
            
            success = response.status_code == 200
            if success:
                _logger.info(f"Telegram sent to {chat_id}")
            else:
                _logger.error(f"Telegram failed: {response.text}")
            return success
            
        except Exception as e:
            _logger.error(f"Telegram error: {str(e)}")
            return False
    
    def send_email(self, to_email: str, title: str, content: str, 
                   smtp_config: dict = None) -> bool:
        """Gửi email (cần cấu hình SMTP)"""
        # Nếu không có SMTP, chỉ log
        if not smtp_config:
            _logger.info(f"[EMAIL SIMULATION] To: {to_email}, Title: {title}")
            _logger.info(f"Content: {content[:200]}...")
            return True
        
        # Nếu có SMTP thì gửi thật
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from_email', 'noreply@company.com')
            msg['To'] = to_email
            msg['Subject'] = title
            
            msg.attach(MIMEText(content, 'html'))
            
            with smtplib.SMTP(smtp_config.get('host', 'smtp.gmail.com'), 
                              smtp_config.get('port', 587)) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            _logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            _logger.error(f"Email failed: {str(e)}")
            return False