# README - HỆ THỐNG TỰ ĐỘNG HÓA CRM & THÔNG BÁO

## 📋 MỤC LỤC
1. [Tổng quan](#tổng-quan)
2. [Các trigger kích hoạt](#các-trigger-kích-hoạt)
3. [Luồng xử lý chi tiết](#luồng-xử-lý-chi-tiết)
4. [Cấu hình hệ thống](#cấu-hình-hệ-thống)
5. [Các file đã sửa đổi](#các-file-đã-sửa-đổi)
6. [Hướng dẫn cài đặt](#hướng-dẫn-cài-đặt)
7. [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)
8. [Nâng cấp trong tương lai](#nâng-cấp-trong-tương-lai)

---

## 1. TỔNG QUAN

Hệ thống tự động hóa quy trình CRM với các tính năng:
- **AI đánh giá khách hàng** và gán nhân viên phù hợp
- **Tự động gửi thông báo** qua Telegram và Email (HTML)
- **Tự động tạo Google Meet** cho các cuộc họp quan trọng
- **Phân tích cảm xúc** từ nội dung tương tác khách hàng
- **Tóm tắt văn bản tự động** bằng AI

---

## 2. CÁC TRIGGER KÍCH HOẠT

### 2.1 KHÁCH HÀNG (Customer)

| STT | Sự kiện | AI | Telegram | Email | Google Meet |
|-----|---------|-----|----------|-------|-------------|
| 1 | **Tạo mới khách hàng** | ✅ Đánh giá & gán NV | ✅ Nội bộ | ✅ NV phụ trách | ❌ |
| 2 | **KH tiềm năng cao** (ai_score≥80 hoặc priority='high') | ❌ | ✅ Nội bộ | ✅ Khách hàng | ✅ 30 phút |
| 3 | **Cập nhật trạng thái** | ❌ | ✅ Nội bộ | ✅ Khách hàng | ❌ |
| 4 | **Cập nhật thông tin** (loại/ngành/doanh thu) | ✅ Đánh giá lại NV | ✅ Nội bộ | ❌ | ❌ |

### 2.2 HỢP ĐỒNG (Contract)

| STT | Sự kiện | AI | Telegram | Email | Google Meet |
|-----|---------|-----|----------|-------|-------------|
| 5 | **Tạo mới hợp đồng** | ❌ | ✅ Nội bộ | ✅ Khách hàng | ✅ 45 phút |
| 6 | **Sắp hết hạn** (còn 30 ngày) | ❌ | ✅ Nội bộ | ✅ Khách hàng | ✅ 30 phút |
| 7 | **Phê duyệt hợp đồng** | ✅ Tóm tắt | ✅ Nội bộ | ✅ Khách hàng | ❌ |

### 2.3 BÁO GIÁ (Quotation)

| STT | Sự kiện | AI | Telegram | Email | Google Meet |
|-----|---------|-----|----------|-------|-------------|
| 8 | **Vào đàm phán** (status='dam_phan') | ❌ | ✅ Nội bộ | ✅ Khách hàng | ✅ 30 phút |

### 2.4 TƯƠNG TÁC (CustomerInteraction)

| STT | Sự kiện | AI | Telegram | Email | Google Meet |
|-----|---------|-----|----------|-------|-------------|
| 9 | **Tạo khiếu nại** (type='khieu_nai') | ❌ | ✅ Nội bộ | ✅ Khách hàng | ✅ 45 phút |
| 10 | **Cảm xúc tiêu cực** (score≥0.8) | ✅ Phân tích | ✅ Nội bộ | ✅ Khách hàng | ✅ 30 phút |

### 2.5 NHÂN VIÊN (NhanVien)

| STT | Sự kiện | AI | Telegram | Email | Google Meet |
|-----|---------|-----|----------|-------|-------------|
| 11 | **Tạo mới nhân viên** | ❌ | ✅ Nội bộ | ✅ Nhân viên | ❌ |
| 12 | **Cập nhật phòng ban/chức vụ** | ❌ | ✅ Nội bộ | ✅ Nhân viên | ❌ |

### 2.6 VĂN BẢN (VanBan)

| STT | Sự kiện | AI | Telegram | Email | Google Meet |
|-----|---------|-----|----------|-------|-------------|
| 13 | **Phê duyệt văn bản** | ✅ Tóm tắt | ✅ Nội bộ | ✅ Khách hàng | ❌ |

---

## 3. LUỒNG XỬ LÝ CHI TIẾT

### 3.1 Luồng tạo khách hàng mới

```
1. Người dùng tạo khách hàng mới
   │
   ├── 2. AI đánh giá hồ sơ (evaluate_customer_profile)
   │       → Trả về ai_score (0-100) và ai_reason
   │
   ├── 3. Tìm nhân viên phù hợp nhất (_find_best_employee)
   │       → Lấy danh sách tất cả nhân viên
   │       → Tính load hiện tại và KPI
   │       → AI route_lead chọn người phù hợp
   │
   ├── 4. Gán nhân viên (_reassign_employee_if_better)
   │       → Nếu chưa có: gán luôn
   │       → Nếu có: chỉ gán lại nếu confidence ≥ 0.8
   │
   ├── 5. Nếu ai_score ≥ 80 hoặc priority='high'
   │       → Tạo Google Meet (30 phút)
   │       → Gửi email mời họp cho khách hàng
   │
   ├── 6. Gửi Telegram nội bộ (customer_created)
   │
   └── 7. Gửi Email cho nhân viên phụ trách (customer_created)
```

### 3.2 Luồng xử lý hợp đồng sắp hết hạn

```
1. Người dùng mở menu "Hợp đồng" (tree view)
   │
   ├── 2. Hệ thống tự động kiểm tra (get_view override)
   │       → Tìm hợp đồng có date_end = today + 30 days
   │       → status = 'hieu_luc'
   │       → meeting_created = False
   │
   ├── 3. Với mỗi hợp đồng tìm được
   │       → Tạo Google Meet gia hạn (30 phút)
   │       → Gửi email mời họp cho khách hàng
   │       → Đánh dấu meeting_created = True
   │
   └── 4. Gửi Telegram nội bộ thông báo
```

### 3.3 Luồng phân tích cảm xúc

```
1. Người dùng tạo/cập nhật tương tác có nội dung
   │
   ├── 2. AI phân tích cảm xúc (analyze_sentiment)
   │       → sentiment: positive/negative/neutral
   │       → score: 0-1
   │       → summary: tóm tắt nội dung
   │
   ├── 3. Nếu sentiment='negative' và score ≥ 0.8
   │       → Tạo Google Meet khắc phục (30 phút)
   │       → Gửi email mời họp cho khách hàng
   │
   └── 4. Nếu sentiment='negative' và score ≥ 0.6
           → Tạo activity cho quản lý trong Odoo
```

---

## 4. CẤU HÌNH HỆ THỐNG

### 4.1 Cấu hình công ty (notification_templates.py)

```python
COMPANY_NAME = "Công ty Cổ phần Công nghệ SmartBiz"
COMPANY_PHONE = "024.1234.5678"
COMPANY_EMAIL = "contact@smartbiz.vn"
COMPANY_WEBSITE = "https://smartbiz.vn"
COMPANY_ADDRESS = "Tầng 12, Tòa nhà VTC, Số 23 Lê Trọng Tấn, Hà Nội"
```

### 4.2 Cấu hình Telegram (config_helper.py)

```python
telegram_bot_token = "YOUR_BOT_TOKEN"
telegram_default_chat_id = "YOUR_CHAT_ID"
```

### 4.3 Cấu hình Email (config_helper.py)

```python
email_smtp_server = "smtp.gmail.com"
email_smtp_port = 465
email_sender = "your-email@gmail.com"
email_app_password = "your-app-password"
email_default_recipient = "admin@company.com"
```

### 4.4 Cấu hình Google Meet (config_helper.py)

```python
google_credentials_file = "path/to/credentials.json"
google_token_file = "path/to/token.json"
google_default_calendar_id = "primary"
default_meeting_duration = 30
```

### 4.5 Cấu hình AI Gemini (config_helper.py)

```python
gemini_api_key = "YOUR_GEMINI_API_KEY"
gemini_model = "gemini-1.5-flash"
```

---

## 5. CÁC FILE ĐÃ SỬA ĐỔI

### 5.1 File cốt lõi

| File | Mô tả |
|------|-------|
| `models/models.py` | Các model Customer, Contract, Interaction, NhanVien |
| `models/notification_templates.py` | Template Telegram và Email |
| `smart_biz_services/notif_helper.py` | Service gửi thông báo |
| `smart_biz_services/ai_helper.py` | Service AI (Gemini) |
| `smart_biz_services/google_helper.py` | Service Google Meet |
| `smart_biz_services/agent_helper.py` | Service định tuyến lead |

### 5.2 Các method đã thêm

**Customer class:**
```python
_find_best_employee()          # Tìm nhân viên phù hợp nhất
_reassign_employee_if_better() # Gán lại nhân viên nếu tốt hơn
_create_meeting()              # Tạo Google Meet
```

**Contract class:**
```python
_create_contract_meeting()     # Tạo meeting cho hợp đồng
check_and_create_expiry_meeting() # Kiểm tra hợp đồng sắp hết hạn
get_view()                     # Override để tự động kiểm tra
action_check_expiring()        # Kiểm tra thủ công
```

**CustomerInteraction class:**
```python
_create_negative_feedback_meeting() # Meeting cho phản hồi tiêu cực
_create_complaint_meeting()         # Meeting cho khiếu nại
```

### 5.3 Các template đã thêm

**TelegramTemplates:**
- `customer_created`
- `customer_status_updated`
- `contract_approved`
- `document_approved`
- `employee_created`
- `employee_updated`
- `quotation_negotiation`
- `customer_reassigned`
- `meeting_created`

**EmailTemplates:**
- `customer_created`
- `customer_status_updated`
- `contract_approved`
- `document_approved`
- `employee_created`
- `employee_updated`
- `quotation_negotiation`
- `meeting_invitation`

---

## 6. HƯỚNG DẪN CÀI ĐẶT

### 6.1 Yêu cầu hệ thống

- Odoo 16 trở lên
- Python 3.8+
- Internet connection (cho AI, Telegram, Email, Google Meet)

### 6.2 Cài đặt thư viện Python

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install requests
pip install pytesseract pillow pdf2image PyPDF2
```

### 6.3 Cấu hình Google OAuth (cho Google Meet)

```bash
# Tạo credentials.json từ Google Cloud Console
# Enable Google Calendar API
# Sau đó chạy:
python -c "from smart_biz_services.google_helper import GoogleHelper; GoogleHelper().calendar_service._get_credentials()"
```

### 6.4 Cấu hình Tesseract OCR (cho scan tài liệu)

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-vie

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### 6.5 Khởi tạo database

```bash
# Nâng cấp module
./odoo-bin -u your_module_name -d your_database
```

---

## 7. XỬ LÝ LỖI THƯỜNG GẶP

### 7.1 Lỗi gửi Telegram

```
⚠️ Telegram bot token not configured
```
**Giải pháp:** Kiểm tra `telegram_bot_token` trong config_helper.py

### 7.2 Lỗi gửi Email

```
❌ Email failed: (535, b'5.7.8 Username and Password not accepted')
```
**Giải pháp:** Sử dụng App Password (không phải mật khẩu Gmail thường)

### 7.3 Lỗi Google Meet

```
❌ Token file not found: /path/to/token.json
```
**Giải pháp:** Chạy lệnh xác thực Google OAuth lần đầu

### 7.4 Lỗi AI Gemini

```
Gemini API error: 403
```
**Giải pháp:** Kiểm tra API key và billing trên Google Cloud

### 7.5 Lỗi phân tích cảm xúc

```
Lỗi phân tích cảm xúc cho interaction
```
**Giải pháp:** Kiểm tra nội dung có quá dài hoặc ký tự đặc biệt

---

## 8. NÂNG CẤP TRONG TƯƠNG LAI

### 8.1 Gợi ý nâng cấp

| STT | Tính năng | Mô tả |
|-----|-----------|-------|
| 1 | **SMS thông báo** | Tích hợp Twilio để gửi SMS |
| 2 | **Zalo notification** | Gửi thông báo qua Zalo OA |
| 3 | **Meeting reminder** | Nhắc lịch họp trước 15 phút |
| 4 | **Meeting recording** | Tự động ghi âm Google Meet |
| 5 | **Dashboard analytics** | Thống kê hiệu quả các trigger |
| 6 | **Multi-language** | Hỗ trợ tiếng Anh, tiếng Trung |

### 8.2 Mở rộng trigger

```python
# Ví dụ thêm trigger mới
@api.model
def create(self, vals):
    record = super().create(vals)
    
    # Custom trigger
    if record.custom_field == 'special_value':
        record._create_custom_meeting()
        record._send_custom_notification()
    
    return record
```

---

## 9. LIÊN HỆ & HỖ TRỢ

- **Email:** support@smartbiz.vn
- **Telegram:** t.me/smartbiz_support
- **Issue tracking:** GitHub Issues

---

## 10. CHANGELOG

### Version 1.0.0 (2026-06-15)

**Thêm mới:**
- ✅ AI đánh giá khách hàng và gán nhân viên
- ✅ 13 trigger gửi Telegram
- ✅ 13 trigger gửi Email HTML
- ✅ 6 trigger tạo Google Meet
- ✅ Phân tích cảm xúc tương tác
- ✅ Tóm tắt văn bản tự động
- ✅ Template email chuyên nghiệp
- ✅ Kiểm tra hợp đồng sắp hết hạn khi mở view

**Sửa lỗi:**
- ✅ Xóa code thừa trong Customer.create()
- ✅ Thêm subject_map cho meeting_invitation
- ✅ Sửa lỗi old_values trong create()

---

**© 2026 SmartBiz - Giải pháp chuyển đổi số toàn diện**