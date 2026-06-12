# config_helper.py
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

class ConfigHelper:
    """Đọc cấu hình từ file JSON - Tập trung tất cả config"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Đọc file config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            _logger.info("✅ Config loaded successfully")
        except Exception as e:
            _logger.error(f"❌ Failed to load config: {str(e)}")
            self._config = {}
    
    # ============ GEMINI ============
    @property
    def gemini_api_key(self):
        return self._config.get('gemini', {}).get('api_key', '')
    
    @property
    def gemini_model(self):
        return self._config.get('gemini', {}).get('model', 'gemini-1.5-flash')
    
    # ============ TELEGRAM ============
    @property
    def telegram_bot_token(self):
        return self._config.get('telegram', {}).get('bot_token', '')
    
    @property
    def telegram_default_chat_id(self):
        return self._config.get('telegram', {}).get('default_chat_id', '')
    
    # ============ EMAIL ============
    @property
    def email_smtp_server(self):
        return self._config.get('email', {}).get('smtp_server', 'smtp.gmail.com')
    
    @property
    def email_smtp_port(self):
        return self._config.get('email', {}).get('smtp_port', 465)
    
    @property
    def email_sender(self):
        return self._config.get('email', {}).get('sender_email', '')
    
    @property
    def email_app_password(self):
        return self._config.get('email', {}).get('sender_app_password', '')
    
    @property
    def email_default_recipient(self):
        return self._config.get('email', {}).get('default_recipient', '')
    
    # ============ GOOGLE ============
    @property
    def google_token_file(self):
        token_file = self._config.get('google', {}).get('token_file', 'token.json')
        # Hỗ trợ đường dẫn tuyệt đối hoặc tương đối
        if os.path.isabs(token_file):
            return token_file
        return os.path.join(os.path.dirname(__file__), token_file)
    
    @property
    def google_credentials_file(self):
        creds_file = self._config.get('google', {}).get('credentials_file', 'credentials.json')
        if os.path.isabs(creds_file):
            return creds_file
        return os.path.join(os.path.dirname(__file__), creds_file)
    
    @property
    def google_default_calendar_id(self):
        return self._config.get('google', {}).get('default_calendar_id', 'primary')
    
    # ============ DEFAULTS ============
    @property
    def default_employee_name(self):
        return self._config.get('defaults', {}).get('employee_name', 'Nhân viên')
    
    @property
    def default_employee_email(self):
        return self._config.get('defaults', {}).get('employee_email', '')
    
    @property
    def default_employee_chat_id(self):
        return self._config.get('defaults', {}).get('employee_chat_id', '')
    
    @property
    def default_meeting_duration(self):
        return self._config.get('defaults', {}).get('meeting_duration_minutes', 30)
    
    # ============ UTILITY ============
    def reload(self):
        self._load_config()

# Singleton instance
config = ConfigHelper()