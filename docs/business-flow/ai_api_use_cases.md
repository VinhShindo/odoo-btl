# Use Case AI & API cho Odoo (Mail, Telegram, CRM, Google, Kế toán)

Tài liệu này mô tả chi tiết các trường hợp sử dụng AI và API trong Odoo. Mỗi use case bao gồm:
- Dữ liệu đầu vào (input),
- Kết quả trả về (output),
- Quy trình thực hiện và thao tác giao diện,
- Service gọi tới,
- Module và trigger liên quan.

> Ghi chú: các tên endpoint/service là ví dụ. Bạn có thể map tới hàm trong `addons/smart_biz_services/agent_helper.py` hoặc triển khai REST controller nội bộ như `/api/ai/<use_case>`.

---

## 1) Chấm điểm lead và ưu tiên xử lý

- Mục đích: Khi một lead mới được tạo, AI tự động chấm điểm và gán mức ưu tiên để nhân viên biết nên xử lý nhanh hay chưa.

### Input
- Thông tin lead mới: tên, email, điện thoại, mô tả, ngành nghề, nguồn lead, giá trị dự kiến.
- Ví dụ payload:
  ```json
  {
    "name":"Công ty ABC",
    "email":"contact@abc.com",
    "phone":"0909123456",
    "description":"Yêu cầu tư vấn phần mềm quản lý",
    "company_size":"50-100",
    "utm_source":"Google Ads",
    "created_at":"2026-06-10T10:12:00"
  }
  ```

### Output
- Điểm lead và mức ưu tiên:
  ```json
  {
    "lead_id":123,
    "score":0.87,
    "priority":"Cao",
    "reason":"Ngành dịch vụ, ngân sách lớn, yêu cầu gấp"
  }
  ```

### Quy trình giao diện
1. Khi tạo lead mới trong module CRM hoặc từ biểu mẫu web, Odoo tự động gọi AI.
2. Sau khi lưu lead, trên form `crm.lead` hiển thị thêm các trường `Điểm AI` và `Ưu tiên`.
3. Nhân viên có thể mở tab thông tin lead, xem lời giải thích ngắn gọn về lý do chấm điểm.
4. Khi hoàn thành, lead được gán tag `Ưu tiên cao/Trung bình/Thấp` và có thể tạo activity xử lý ngay.

### Gọi service
- `POST /api/ai/lead_score`
- hoặc `agent_helper.score_lead(lead_data)`

### Module/Trigger
- `crm`, `smart_biz_services`
- Trigger: `create()` trên `crm.lead` hoặc cron chạy định kỳ với lead mới

---

## 2) Tự động phân bổ nhân viên bán hàng / hỗ trợ

- Mục đích: Khi lead hoặc ticket mới vào, hệ thống tự động chọn người phụ trách tốt nhất dựa trên năng lực, khu vực và tải việc.

### Input
- Lead/ticket, thông tin kỹ năng agent, trạng thái công việc hiện tại.
- Ví dụ:
  ```json
  {
    "lead_id":123,
    "industry":"B2B",
    "region":"Hà Nội",
    "required_skill":["CRM","ERP"],
    "agents":[
      {"user_id":10,"skill":["ERP"],"load":2},
      {"user_id":11,"skill":["CRM","B2B"],"load":1}
    ]
  }
  ```

### Output
- Kết quả gán:
  ```json
  {
    "lead_id":123,
    "assigned_user_id":11,
    "reason":"Kinh nghiệm B2B, tải thấp, cùng khu vực Hà Nội"
  }
  ```

### Quy trình giao diện
1. Trên form `crm.lead`, sau khi AI chấm điểm xong, Odoo hiển thị gợi ý người phụ trách.
2. Người dùng có thể bấm nút `Gán tự động` hoặc `Xem đề xuất` để chấp nhận.
3. Khi gán xong, thông tin người phụ trách được cập nhật ngay trên form lead.
4. Thông báo gửi tới người nhận qua email hoặc Telegram nếu họ đã cấu hình.

### Gọi service
- `POST /api/ai/route_lead`
- hoặc `agent_helper.route_lead(lead, agents_meta)`

### Module/Trigger
- `crm`, `hr`, `smart_biz_services`
- Trigger: sau khi lead được tạo hoặc khi lead thay đổi trạng thái

---

## 3) Sinh nội dung email/Telegram tự động

- Mục đích: Tạo nhanh nội dung email hoặc tin nhắn Telegram theo ngữ cảnh đơn hàng, lead hoặc chăm sóc khách hàng.

### Input
- Loại thông báo và dữ liệu ngữ cảnh, ví dụ:
  ```json
  {
    "template":"order_confirmation",
    "order_id":"SO/2026/001",
    "customer_name":"Công ty ABC",
    "amount":12000000,
    "delivery_date":"2026-06-15"
  }
  ```

### Output
- Nội dung hoàn chỉnh để gửi:
  ```json
  {
    "subject":"Xác nhận đơn hàng SO/2026/001",
    "body_html":"<p>Xin chào...</p>",
    "telegram_text":"<b>Đơn hàng đã được xác nhận</b>..."
  }
  ```

### Quy trình giao diện
1. Trên form `sale.order`, nhân viên bấm nút `Tạo nội dung tự động`.
2. Hệ thống gọi AI và hiển thị bản xem trước nội dung email/tin nhắn.
3. Người dùng có thể sửa lại nội dung trước khi gửi.
4. Khi hoàn thành, hệ thống tự động lưu template và gửi theo lựa chọn Email hoặc Telegram.

### Gọi service
- `POST /api/ai/generate_message`
- hoặc `agent_helper.generate_notification(template, context)`

### Module/Trigger
- `sale`, `mail`, `customer_notification`, `smart_biz_services`

---

## 4) Tóm tắt tài liệu và cuộc họp

- Mục đích: Khi có biên bản họp, ghi chú hoặc tài liệu dài, AI tự động tổng hợp nội dung chính và đề xuất việc cần làm.

### Input
- Văn bản họp, văn bản tài liệu, hoặc đường dẫn tài liệu trên Google Drive.
- Ví dụ:
  ```json
  {
    "text":"Nội dung biên bản họp...",
    "format":"meeting_notes"
  }
  ```

### Output
- Tóm tắt chính và danh sách việc cần làm:
  ```json
  {
    "summary":"Cuộc họp xác nhận giá, tiến độ và thanh toán...",
    "action_items":[
      {"task":"Gửi báo giá", "owner":"Trịnh", "due":"2026-06-12"}
    ]
  }
  ```

### Quy trình giao diện
1. Sau khi upload file hoặc kết thúc sự kiện Google Calendar, người dùng bấm `Tóm tắt nhanh`.
2. Hệ thống hiển thị phần nội dung tóm tắt và các action item trên cùng một màn hình.
3. Nhấn `Tạo task` để chuyển action item thành `project.task` hoặc `crm.activity`.
4. Khi hoàn thành, tóm tắt được lưu lại trên chatter của lead hoặc đơn hàng.

### Gọi service
- `POST /api/ai/summarize`
- hoặc `agent_helper.summarize_text(text, opts)`

### Module/Trigger
- `google_calendar`, `documents`, `mail`, `project`, `smart_biz_services`

---

## 5) Trích xuất hóa đơn OCR và tự động ghi sổ

- Mục đích: Khi nhận hóa đơn ảnh hoặc PDF, AI đọc tự động và tạo bản nháp hóa đơn mua hàng.

### Input
- File hóa đơn PDF/JPG và thông tin bổ sung như nhà cung cấp, ngày, tiền tệ.
- Ví dụ:
  ```json
  {
    "file_base64":"...",
    "filename":"inv.jpg",
    "supplier":"Công ty ABC",
    "currency":"VND"
  }
  ```

### Output
- Dữ liệu hóa đơn đã trích xuất:
  ```json
  {
    "invoice_number":"HD001",
    "date":"2026-06-10",
    "amount":15000000,
    "tax":10,
    "lines":[{"description":"Phần mềm","qty":1,"unit_price":15000000}]
  }
  ```

### Quy trình giao diện
1. Trong module `Documents` hoặc từ email chứa file, người dùng click `Xử lý hóa đơn`.
2. Hệ thống gọi AI để đọc nội dung và chuyển đổi thành dữ liệu cấu trúc.
3. Người dùng kiểm tra lại các trường dữ liệu trên form `account.move` draft.
4. Khi xác nhận, nhấn `Lưu` để tạo hóa đơn chính thức.

### Gọi service
- `POST /api/ai/ocr_invoice`
- hoặc `agent_helper.ocr_invoice(file_bytes)`

### Module/Trigger
- `documents`, `account`, `purchase`, `smart_biz_services`

---

## 6) Phân tích cảm xúc khách hàng

- Mục đích: Đánh giá nội dung email, cuộc chat hoặc phản hồi để xác định mức độ hài lòng và mức độ khẩn cấp.

### Input
- Nội dung văn bản: email, chat, phản hồi khách hàng.
- Ví dụ:
  ```json
  {"text":"Tôi rất thất vọng vì đơn hàng giao chậm"}
  ```

### Output
- Kết quả phân tích tâm trạng:
  ```json
  {
    "sentiment":"negative",
    "score":0.15,
    "tags":["delay","complaint"]
  }
  ```

### Quy trình giao diện
1. Khi nhận email mới hoặc chat kết thúc, hệ thống tự động phân tích cảm xúc.
2. Trên giao diện message, hiển thị nhãn `Cảm xúc: Tiêu cực/Trung tính/Tích cực`.
3. Nếu tiêu cực, tạo cảnh báo và yêu cầu người quản lý xem xét.
4. Khi xử lý xong, trạng thái được cập nhật và ghi chú kết quả.

### Gọi service
- `POST /api/ai/sentiment`
- hoặc `agent_helper.analyze_sentiment(text)`

### Module/Trigger
- `mail`, `im_livechat`, `helpdesk`, `crm`, `smart_biz_services`

---

## 7) Chatbot trợ lý khách hàng qua Telegram và Web

- Mục đích: Tự động trả lời câu hỏi cơ bản, chuyển tiếp sang nhân viên khi cần và lưu lại hội thoại.

### Input
- Tin nhắn khách hàng, lịch sử hội thoại, thông tin ngữ cảnh.
- Ví dụ:
  ```json
  {
    "conversation_id":"abc123",
    "text":"Cho tôi biết giá gói Premium",
    "user_id":45
  }
  ```

### Output
- Phản hồi bot và gợi ý hành động:
  ```json
  {
    "reply":"Gói Premium có giá 10.000.000 VND/tháng...",
    "action":"create_ticket",
    "confidence":0.92
  }
  ```

### Quy trình giao diện
1. Khi khách gửi tin nhắn qua Telegram hoặc live chat, webhook gọi AI.
2. Hệ thống hiển thị trả lời tự động trong giao diện chat.
3. Nếu bot không giải quyết được, chọn `Chuyển agent` và tạo ticket/lead.
4. Khi hoàn thành, toàn bộ hội thoại được lưu trong `mail.thread` của khách.

### Gọi service
- `POST /api/ai/intent`
- `POST /api/ai/generate_reply`
- hoặc `agent_helper.chatbot.handle_message(payload)`

### Module/Trigger
- `im_livechat`, `customer_notification` (Telegram webhook), `helpdesk`, `smart_biz_services`

---

## 8) Tạo báo giá / proposal tự động từ lead

- Mục đích: Chuyển lead thành báo giá nhanh bằng cách AI tạo nội dung và đề xuất dòng hàng.

### Input
- Thông tin lead (yêu cầu sản phẩm, ngân sách, lịch trình), danh mục sản phẩm.
- Ví dụ:
  ```json
  {
    "lead_id":123,
    "request":"Muốn triển khai CRM cho 50 người",
    "budget":20000000
  }
  ```

### Output
- Bản nháp `sale.order` và nội dung proposal:
  ```json
  {
    "order_lines":[{"product":"Gói CRM","qty":1,"price":18000000}],
    "proposal_text":"<p>Đề xuất giải pháp CRM cho 50 người...</p>"
  }
  ```

### Quy trình giao diện
1. Trên form lead, bấm nút `Sinh báo giá tự động`.
2. AI trả về các dòng sản phẩm và nội dung proposal.
3. Áp dụng vào `sale.order` nháp, người dùng có thể chỉnh sửa.
4. Gửi proposal qua email hoặc Telegram cho khách.

### Gọi service
- `POST /api/ai/generate_proposal`
- hoặc `agent_helper.generate_proposal(lead, catalog)`

### Module/Trigger
- `crm`, `sale`, `smart_biz_services`

---

## 9) Phân tích điều khoản hợp đồng và đánh giá rủi ro

- Mục đích: Tự động nhận diện các điều khoản quan trọng trong hợp đồng và gợi ý rủi ro.

### Input
- Hợp đồng PDF/DOCX hoặc nội dung văn bản.
- Ví dụ:
  ```json
  {"document_id":"doc_456"}
  ```

### Output
- Danh sách điều khoản với thang đánh giá:
  ```json
  {
    "clauses":[
      {"type":"termination","risk":"Cao","note":"Điều khoản chấm dứt một chiều"}
    ]
  }
  ```

### Quy trình giao diện
1. Trong module Contracts/Document, click `Phân tích hợp đồng`.
2. Hệ thống hiển thị các điều khoản rủi ro, điều khoản cần thẩm định.
3. Người dùng có thể tạo task review cho bộ phận pháp lý.
4. Khi hoàn thành, thông tin đánh giá được ghi vào form hợp đồng.

### Gọi service
- `POST /api/ai/contract_analysis`
- hoặc `agent_helper.analyze_contract(file_bytes)`

### Module/Trigger
- `documents`, `sale`, `legal` (nếu có), `smart_biz_services`

---

## 10) Lên lịch họp tự động và tạo công việc follow-up

- Mục đích: Từ yêu cầu họp bằng ngôn ngữ tự nhiên, AI tạo event và danh sách công việc tiếp theo.

### Input
- Yêu cầu họp bằng câu tiếng Việt hoặc tiếng Anh.
- Ví dụ:
  ```json
  {
    "request":"Đặt lịch họp với khách hàng ACME vào thứ Hai 10h, 30 phút",
    "participants":["khachhang@acme.com"]
  }
  ```

### Output
- Event Google Calendar + Odoo event, follow-up item:
  ```json
  {
    "event_id":"evt_789",
    "meeting_link":"https://meet.google.com/...",
    "follow_ups":[{"task":"Chuẩn bị hợp đồng","owner":"Hà","due":"2026-06-12"}]
  }
  ```

### Quy trình giao diện
1. Người dùng nhấn `Lên lịch họp tự động` trong CRM hoặc chat.
2. AI phân tích thời gian và người tham gia.
3. Hệ thống kiểm tra lịch trống và tạo event trên Google Calendar.
4. Tự động sinh việc cần follow-up và hiển thị trên màn hình.
5. Khi hoàn thành, event và task được lưu vào Odoo.

### Gọi service
- `POST /api/ai/parse_schedule`
- hoặc `agent_helper.schedule_meeting(parsed_request)`

### Module/Trigger
- `google_calendar`, `crm`, `project`, `smart_biz_services`

---

## 11) Tổng hợp báo cáo KPI và phân tích dữ liệu tự động

- Mục đích: Từ dữ liệu bán hàng, khách hàng và công nợ, AI tạo báo cáo KPI và phân tích xu hướng.

### Input
- Khoảng thời gian, loại dữ liệu cần tổng hợp (doanh số, cơ hội, côn g nợ, khách hàng mới).
- Ví dụ:
  ```json
  {
    "period":"2026-06",
    "metrics":["revenue","new_leads","payment_delay"]
  }
  ```

### Output
- Báo cáo định lượng và nhận định:
  ```json
  {
    "summary":"Doanh số tăng 12% so với tháng trước",
    "kpis":[{"name":"Doanh thu","value":120000000}],
    "insights":["Cơ hội từ ngành xây dựng đang tăng","Nợ xấu cần xử lý"]
  }
  ```

### Quy trình giao diện
1. Trên dashboard báo cáo, chọn `Báo cáo AI`.
2. Chọn khoảng thời gian và loại chỉ số muốn tổng hợp.
3. Nhấn `Tạo báo cáo` để AI chạy và hiển thị biểu đồ, bảng số liệu.
4. Khi hoàn thành, có thể xuất ra Excel, Google Sheets hoặc gửi email.

### Gọi service
- `POST /api/ai/generate_insights`
- hoặc `agent_helper.generate_insights(aggregated_metrics)`

### Module/Trigger
- `google_spreadsheet`, `crm`, `sale`, `smart_biz_services`

---

## 12) Dự đoán doanh thu và tồn kho

- Mục đích: AI dự đoán doanh thu tương lai và cảnh báo tồn kho dựa trên dữ liệu lịch sử.

### Input
- Dữ liệu lịch sử bán hàng và tồn kho.
- Ví dụ:
  ```json
  {
    "history":[{"date":"2026-05-01","quantity":20}],
    "product":"Mã A",
    "warehouse":"Kho Hà Nội"
  }
  ```

### Output
- Dự báo và cảnh báo kho:
  ```json
  {
    "revenue_next_period":150000000,
    "stock_warning":[{"product":"Mã A","warning":"Tồn kho thấp"}]
  }
  ```

### Quy trình giao diện
1. Trong module tồn kho hoặc bán hàng, chọn `Dự báo AI`.
2. Chọn sản phẩm hoặc nhóm sản phẩm cần dự đoán.
3. Hệ thống hiển thị biểu đồ dự báo doanh thu và cảnh báo tồn kho.
4. Khi hoàn thành, người dùng có thể tạo lệnh đặt hàng bổ sung.

### Gọi service
- `POST /api/ai/forecast_revenue`
- hoặc `agent_helper.predict_revenue_stock(data)`

### Module/Trigger
- `stock`, `sale`, `smart_biz_services`

---

## 13) Phân tích rủi ro thanh toán và dự đoán khách hàng tiềm năng

- Mục đích: AI đánh giá khả năng trả nợ và dự đoán khách hàng có nguy cơ churn hoặc phù hợp với upsell.

### Input
- Lịch sử thanh toán, công nợ, tương tác khách hàng.
- Ví dụ:
  ```json
  {
    "partner_id":78,
    "payment_history":[{"date":"2026-05-01","delay_days":10}],
    "interaction_count":15
  }
  ```

### Output
- Phân tích rủi ro và gợi ý:
  ```json
  {
    "churn_probability":0.62,
    "credit_risk":"Trung bình",
    "upsell_opportunities":[{"product":"Gia hạn bảo trì","score":0.74}]
  }
  ```

### Quy trình giao diện
1. Trên form `res.partner`, click `Phân tích AI` hoặc `Đánh giá khách hàng`.
2. AI hiển thị mức rủi ro thanh toán, nguy cơ churn và đề xuất upsell.
3. Người dùng có thể gắn cảnh báo và tạo chiến dịch chăm sóc.
4. Khi hoàn thành, kết quả được lưu vào hồ sơ khách hàng.

### Gọi service
- `POST /api/ai/churn_predict`
- `POST /api/ai/upsell_recommendation`
- hoặc `agent_helper.predict_churn(partner)`

### Module/Trigger
- `crm`, `subscription`, `marketing`, `smart_biz_services`

---

## Phụ lục: Đề xuất tên API và payload mẫu

- `POST /api/ai/lead_score`
  - body: `{ "lead": { ... } }`
  - response: `{ "score":0.81, "priority":"Cao" }`

- `POST /api/ai/generate_message`
  - body: `{ "template":"order_confirmation", "context":{...} }`
  - response: `{ "subject":"...","body_html":"...","telegram_text":"..." }`

- `POST /api/ai/ocr_invoice`
  - body: `{ "file_base64": "....", "filename": "inv.pdf" }`
  - response: `{ "invoice_number":"INV-123","amount":1000.0, ... }`

- `POST /api/ai/summarize`
  - body: `{ "text":"...","max_tokens":250 }`
  - response: `{ "summary":"...","action_items":[...] }`

---

## Gợi ý bước tiếp theo
1. Triển khai wrapper trong `addons/smart_biz_services/agent_helper.py` cho các API chính.
2. Tạo controller REST `controllers/ai_controller.py` expose endpoint `/api/ai/*`.
3. Thiết kế giao diện nút/bảng điều khiển để gọi AI trong CRM, Sale, Documents, Stock.
4. Thử nghiệm với 3 use case đầu tiên: chấm điểm lead, gán nhân viên tự động, sinh nội dung thông báo.
