# google_helper.py
import json
import logging
import os
import sys
from datetime import datetime, timedelta
import threading
import time
import webbrowser
import subprocess
import platform
import random
import string
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_helper import config

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service tạo Google Calendar event và Google Meet thật"""
    
    def __init__(self):
        self.token_file = config.google_token_file
        self.credentials_file = config.google_credentials_file
        self.calendar_id = config.google_default_calendar_id
        self._credentials = None
    
    def _get_credentials(self):
        """Lấy credentials từ token file"""
        if self._credentials is None:
            try:
                if os.path.exists(self.token_file):
                    self._credentials = Credentials.from_authorized_user_file(
                        self.token_file,
                        ["https://www.googleapis.com/auth/calendar"]
                    )
                    _logger.info("✅ Google Calendar credentials loaded")
                else:
                    _logger.error(f"❌ Token file not found: {self.token_file}")
                    _logger.info("   Please run create_token.py first to authenticate")
                    return None
            except Exception as e:
                _logger.error(f"❌ Failed to load credentials: {str(e)}")
                return None
        return self._credentials
    
    def create_meeting(self, title: str, start_time: datetime, end_time: datetime, 
                       attendees: list = None, description: str = "") -> dict:
        """Tạo Google Calendar event với Google Meet"""
        _logger.info("Calling Google Calendar API...")
        credentials = self._get_credentials()
        if not credentials:
            return None
        
        try:
            service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
            
            calendar = service.calendars().get(
                calendarId="primary"
            ).execute() 

            print(calendar)
            
            event = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "Asia/Ho_Chi_Minh",
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "Asia/Ho_Chi_Minh",
                },
                "attendees": [{"email": email} for email in (attendees or []) if email],
                "conferenceData": {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {"type": "hangoutsMeet"}
                    }
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 60},
                        {"method": "popup", "minutes": 15},
                    ]
                }
            }
            
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                conferenceDataVersion=1,
                sendUpdates="all"
            ).execute()
            
            # Lấy link Google Meet
            meet_link = None
            if "conferenceData" in created_event and "entryPoints" in created_event["conferenceData"]:
                for entry in created_event["conferenceData"]["entryPoints"]:
                    if entry.get("entryPointType") == "video":
                        meet_link = entry.get("uri")
                        break
            
            return {
                "meet_link": meet_link,
                "calendar_link": created_event.get("htmlLink", ""),
                "event_id": created_event.get("id", "")
            }
        except Exception as e:
            _logger.error(f"❌ Failed to create calendar event: {str(e)}")
            return None


class MeetingScheduler:
    """Lớp quản lý lịch trình meeting - Chạy trong thread riêng"""
    
    _instance = None
    _scheduled_meetings = []
    _timer_thread = None
    _running = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._start_scheduler()
        return cls._instance
    
    def _start_scheduler(self):
        if not self._running:
            self._running = True
            self._timer_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self._timer_thread.start()
            _logger.info("✅ Meeting scheduler started")
    
    def _run_scheduler(self):
        while self._running:
            try:
                now = datetime.now()
                for meeting in self._scheduled_meetings[:]:
                    meeting_time = meeting.get('meeting_time')
                    notified = meeting.get('notified', False)
                    
                    if meeting_time and not notified:
                        time_diff = (meeting_time - now).total_seconds()
                        if 0 < time_diff <= 300:
                            self._send_reminder(meeting)
                            meeting['notified'] = True
                        if 0 < time_diff <= 30 and meeting.get('auto_open'):
                            self._auto_open(meeting)
            except Exception as e:
                _logger.error(f"Scheduler error: {str(e)}")
            time.sleep(10)
    
    def _send_reminder(self, meeting):
        _logger.info(f"🔔 REMINDER: '{meeting['title']}' at {meeting['meeting_time'].strftime('%H:%M:%S %d/%m/%Y')}")
        _logger.info(f"   Link: {meeting['meeting_link']}")
    
    def _auto_open(self, meeting):
        _logger.info(f"🚀 Auto-opening meeting: '{meeting['title']}'")
        url = meeting['meeting_link']
        system = platform.system()
        try:
            if system == 'Windows':
                os.startfile(url)
            elif system == 'Darwin':
                subprocess.run(['open', url])
            else:
                for browser in ['google-chrome', 'chromium-browser', 'firefox', 'xdg-open']:
                    try:
                        subprocess.Popen([browser, url])
                        break
                    except:
                        continue
        except Exception as e:
            _logger.error(f"Cannot open browser: {e}")
    
    def schedule(self, meeting_info: dict):
        self._scheduled_meetings.append(meeting_info)
        _logger.info(f"📅 Scheduled: {meeting_info['title']} at {meeting_info['meeting_time'].strftime('%H:%M:%S %d/%m/%Y')}")


class GoogleHelper:
    """Service tạo Google Meet và quản lý lịch họp"""
    
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        self.scheduler = MeetingScheduler()
        self.token_file = config.google_token_file
        self._is_authenticated = os.path.exists(self.token_file)
        _logger.info(f"Token file = {self.token_file}")
        _logger.info(f"Exists = {os.path.exists(self.token_file)}")
        self.default_duration = config.default_meeting_duration
    
    def create_contract_meeting(self, contract_data: dict) -> dict:
        """Tạo meeting khi chốt hợp đồng"""
        _logger.info(f"📋 Creating meeting for contract: {contract_data.get('contract_id')}")
        
        # Xác định thời gian
        meeting_time = contract_data.get('meeting_time')
        if not meeting_time:
            meeting_time = self._suggest_time()
        
        duration = contract_data.get('duration_minutes', self.default_duration)
        end_time = meeting_time + timedelta(minutes=duration)
        
        # Tạo meeting
        meeting_data = self._create_meeting(
            customer_email=contract_data.get('customer_email'),
            customer_name=contract_data.get('customer_name'),
            employee_name=contract_data.get('employee_name'),
            title=contract_data.get('title', 'Ký hợp đồng'),
            meeting_time=meeting_time,
            end_time=end_time
        )
        
        if meeting_data is None:
            # Fallback
            meeting_link = self._fallback_link(meeting_time)
            calendar_link = self._fallback_calendar(meeting_time, duration, meeting_link)
        else:
            meeting_link = meeting_data.get("meet_link", "")
            calendar_link = meeting_data.get("calendar_link", "")
        
        # Lên lịch
        self.scheduler.schedule({
            'contract_id': contract_data.get('contract_id'),
            'title': contract_data.get('title', 'Ký hợp đồng'),
            'customer_name': contract_data.get('customer_name'),
            'customer_email': contract_data.get('customer_email'),
            'employee_name': contract_data.get('employee_name'),
            'employee_chat_id': contract_data.get('employee_chat_id'),
            'meeting_link': meeting_link,
            'calendar_link': calendar_link,
            'meeting_time': meeting_time,
            'auto_open': True,
            'notified': False
        })
        
        return {
            'success': True,
            'meeting_link': meeting_link,
            'calendar_link': calendar_link,
            'meeting_time': meeting_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _suggest_time(self):
        now = datetime.now()
        suggested = now + timedelta(days=2)
        if suggested.weekday() >= 5:
            suggested = now + timedelta(days=(7 - suggested.weekday()) + 1)
        return suggested.replace(hour=10, minute=0, second=0, microsecond=0)
    
    def _create_meeting(self, customer_email, customer_name, employee_name, title, meeting_time, end_time):
        if not self._is_authenticated:
            return None
        
        _logger.info(f"Token file = {self.token_file}")
        _logger.info(f"Authenticated = {self._is_authenticated}")
        
        attendees = [customer_email] if customer_email else []
        description = f"""
Cuộc họp ký hợp đồng

Khách hàng: {customer_name}
Nhân viên: {employee_name}
Thời gian: {meeting_time.strftime('%H:%M %d/%m/%Y')}
"""
        return self.calendar_service.create_meeting(
            title=title,
            start_time=meeting_time,
            end_time=end_time,
            attendees=attendees,
            description=description
        )
    
    def _fallback_link(self, meeting_time):
        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        link = f"https://meet.google.com/{code}"
        _logger.info(f"🔗 [FALLBACK] {link}")
        return link
    
    def _fallback_calendar(self, meeting_time, duration, link):
        start = meeting_time.strftime('%Y%m%dT%H%M%S')
        end = (meeting_time + timedelta(minutes=duration)).strftime('%Y%m%dT%H%M%S')
        return f"https://calendar.google.com/calendar/render?action=TEMPLATE&dates={start}/{end}&details={link}"
    
    def create_meeting(self, customer_email, customer_name, title, duration_minutes=30) -> str:
        meeting_time = datetime.now() + timedelta(minutes=2)
        end_time = meeting_time + timedelta(minutes=duration_minutes)
        result = self._create_meeting(customer_email, customer_name, "Nhân viên", title, meeting_time, end_time)
        if result:
            return result.get("meet_link", "")
        return self._fallback_link(meeting_time)