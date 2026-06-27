# Hướng Dẫn Thao Tác CRUD và Kết Quả Mong Đợi

Tài liệu này mô tả chi tiết các thao tác CRUD (Create/Read/Update/Delete) và các kết quả mong đợi trên ba module chính: `nhan_su`, `quan_ly_khach_hang`, `quan_ly_van_ban`.

Nội dung bao gồm:
- Danh sách nghiệp vụ chính cần test
- Luồng tự động giữa các module
- Kiểm tra dữ liệu bằng SQL
- Kiểm tra API/JSON-RPC
- Kiểm tra AI/OCR

---

## 1. Module `nhan_su` (Quản lý nhân sự)

### 1.1 Tạo `don_vi` (Phòng ban)
- Hành động: Vào menu Danh mục → Tạo mới `don_vi` với các trường bắt buộc:
  - `ma_don_vi`
  - `ten_don_vi`
- Kết quả mong đợi:
  - Bản ghi xuất hiện trong bảng `don_vi`
  - Giá trị `ma_don_vi` và `ten_don_vi` lưu đúng

SQL kiểm tra:
```sql
SELECT id, ma_don_vi, ten_don_vi FROM don_vi WHERE ma_don_vi = 'DV-XXX';
```

### 1.2 Tạo `chuc_vu` (Chức vụ)
- Hành động: Tạo mới `chuc_vu` với:
  - `ma_chuc_vu`
  - `ten_chuc_vu`
- Kết quả mong đợi:
  - Bản ghi xuất hiện trong `chuc_vu`
  - `ma_chuc_vu` duy nhất trên cơ sở dữ liệu

SQL kiểm tra:
```sql
SELECT id, ma_chuc_vu, ten_chuc_vu FROM chuc_vu WHERE ma_chuc_vu = 'CV-001';
```

### 1.3 Tạo nhân viên (`hr.employee` mở rộng)
- Hành động: Tạo nhân viên mới trong giao diện `Nhân viên` hoặc qua API:
  - `name`
  - `ho_ten_dem` / `ten`
  - `don_vi_id`
  - `chuc_vu_id` (nếu có)
  - `work_email`
  - `date_of_birth` / `birthday` (nếu cần)
- Kết quả mong đợi:
  - Bản ghi tạo thành công trong `hr_employee`
  - Trường mở rộng như `ho_va_ten`, `don_vi_id`, `chuc_vu_id` lưu đúng
  - Hệ thống tự động tạo thư mục hồ sơ nhân viên trong `van_ban.folder`
  - Giá trị `folder_id` của nhân viên được liên kết đúng

QLVB tự động tạo thư mục theo cấu trúc:
- `Nhân viên` → `Phòng ban` → `Tên nhân viên`

SQL kiểm tra:
```sql
SELECT id, name, folder_id FROM hr_employee WHERE name = 'Nguyen Van A';
SELECT id, name, parent_id FROM van_ban_folder WHERE id = (SELECT folder_id FROM hr_employee WHERE name = 'Nguyen Van A');
```

### 1.4 Cập nhật nhân viên
- Hành động: Chỉnh sửa `don_vi_id`, `chuc_vu_id`, `work_email`, `phone`
- Kết quả mong đợi:
  - Giá trị mới được ghi nhận trong `hr_employee`
  - Nếu có automation, thay đổi `don_vi_id` sẽ kích hoạt tính toán lại thống kê hoặc tạo activity/notification không chặn
  - Nếu đổi phòng ban, folder hồ sơ có thể cần cập nhật tên đường dẫn hoặc ghi log thay đổi

SQL kiểm tra:
```sql
SELECT id, name, don_vi_id, chuc_vu_id, work_email FROM hr_employee WHERE name = 'Nguyen Van A';
```

### 1.5 Xóa nhân viên
- Hành động: Xóa bản ghi `hr.employee`
- Kết quả mong đợi:
  - Bản ghi không tồn tại trong `hr_employee`
  - Các ràng buộc foreign key được xử lý phù hợp
  - Folder hồ sơ có thể vẫn giữ lại hoặc xóa tùy cơ chế `ondelete` của module

SQL kiểm tra:
```sql
SELECT id FROM hr_employee WHERE name = 'Nguyen Van A';
```

### 1.6 Các nghiệp vụ phụ trợ trong `nhan_su`
- Lịch sử công tác (`lich_su_cong_tac`): ghi lại quá trình thay đổi chức vụ và phòng ban
- Chứng chỉ / bằng cấp (`chung_chi_bang_cap`, `danh_sach_chung_chi_bang_cap`): tạo, cập nhật, xóa chứng chỉ nhân viên
- Phân công dự án IoT (`iot_project_assignment`): tạo, cập nhật `date_start`, `date_end`, `role`
- Nhật ký thiết bị IoT (`iot_device_log`): theo dõi sử dụng/bảo trì/lỗi thiết bị

---

## 2. Module `quan_ly_khach_hang` (CRM)

### 2.1 Tạo khách hàng (`qlkh.customer`)
- Hành động: Tạo mới khách hàng với thông tin:
  - `name`
  - `code`
  - `customer_type` (cá nhân/doanh nghiệp)
  - `nhan_vien_phu_trach_id`
  - `status` (ví dụ: `moi`, `da_xac_thuc`, `da_huy`)
  - `email`, `phone`, `address`, `note`
- Kết quả mong đợi:
  - Bản ghi tồn tại trong `qlkh_customer`
  - Nếu `status` = `da_xac_thuc`, hệ thống tự động tạo `qlkh_appointment`
  - Nếu `status` = `da_gui_bao_gia` và chưa có báo giá, hệ thống tự động tạo báo giá nháp
  - Trạng thái khách hàng được chuyển đúng

### 2.1.1 Triggers AI / mail / Telegram / agent routing
- Khi tạo khách hàng mới, module gọi các service bên ngoài qua `smart_biz_services`:
  - `AIHelper.evaluate_customer_profile(...)` để tính `ai_score` và `ai_reason`
  - `AgentHelper.route_lead(...)` để gợi ý hoặc tự động gán nhân viên nếu confidence >= 0.75 và chưa có `nhan_vien_phu_trach_id`
  - `NotifHelper.send_telegram(...)` để gửi thông báo Telegram nội bộ
  - `NotifHelper.send_email(...)` để gửi email thông báo tới `customer.email` nếu có
- Nếu cấu hình email/Telegram không đầy đủ, thao tác vẫn tiếp tục; chỉ log lỗi / cảnh báo.
- Không có API gọi điện thoại trực tiếp trong repo; cuộc gọi được xử lý như một loại tương tác (`type = goi_dien`) trong `qlkh.customer_interaction`.
- Email gửi bằng SMTP theo cấu hình trong `addons/smart_biz_services/notif_helper.py`.

SQL kiểm tra:
```sql
SELECT id, name, code, status, nhan_vien_phu_trach_id, ai_score, ai_reason FROM qlkh_customer WHERE code = 'KH0001';
```

### 2.2 Tạo báo giá (`qlkh.quotation`) và chi tiết
- Hành động: Tạo báo giá liên kết:
  - `customer_id`
  - `nhan_vien_id` (có thể lấy từ `customer.nhan_vien_phu_trach_id`)
  - `quotation_line_ids`: các dòng báo giá với `product_name`, `quantity`, `unit_price`
- Kết quả mong đợi:
  - Bản ghi `qlkh_quotation` xuất hiện
  - Các dòng `qlkh_quotation_line` được liên kết chính xác
  - `total_amount` hoặc `amount_total` tính toán đúng
  - Trạng thái báo giá được cập nhật theo workflow

SQL kiểm tra:
```sql
SELECT id, customer_id, state, amount_total FROM qlkh_quotation WHERE customer_id = (SELECT id FROM qlkh_customer WHERE code = 'KH0001');
SELECT id, quotation_id, product_name, quantity, unit_price FROM qlkh_quotation_line WHERE quotation_id = <quotation_id>;
```

### 2.3 Chuyển trạng thái báo giá
- Hành động: Cập nhật trạng thái báo giá từ `nhap` → `da_gui` → `da_xem` → `dam_phan` → `chap_nhan` → `tu_choi`
- Kết quả mong đợi:
  - Trạng thái thay đổi đúng
  - Nếu chuyển sang `dam_phan`, hệ thống có thể tự động tạo cuộc họp Google Meet và gửi thông báo qua email/Telegram
  - Nếu `chap_nhan`, tự động tạo `qlkh.contract`
  - Nếu `tu_choi`, trạng thái báo giá được lưu lại

Kiểm tra thêm cho trạng thái `dam_phan`:
- `meet_url` được tạo và lưu vào `qlkh.quotation`
- Một `mail.activity` được tạo để theo dõi đàm phán
- Email và Telegram được gửi đến khách hàng/nội bộ nếu cấu hình đầy đủ

SQL kiểm tra:
```sql
SELECT id, status, meet_url FROM qlkh_quotation WHERE id = <quotation_id>;
```

### 2.4 Tạo hợp đồng (`qlkh.contract`)
- Hành động: Tạo hợp đồng liên kết:
  - `customer_id`
  - `quotation_id` (nếu có)
  - `contract_value`
  - `start_date`, `end_date`
  - `status`
- Kết quả mong đợi:
  - Bản ghi `qlkh_contract` xuất hiện
  - `contract_value` đúng với tổng báo giá hoặc giá nhập tay
  - Có liên kết đến `quotation_id` nếu workflow hợp đồng tự động
  - Khi gọi `action_approve()`, nếu hợp đồng chưa có văn bản liên quan thì tự động tạo `van_ban.document`, thực hiện OCR nếu có file và ghi `ai_summary`
  - Khi `contract.status` = `da_duyet`, gửi thông báo Telegram/Email và tạo `mail.activity`

SQL kiểm tra:
```sql
SELECT id, customer_id, quotation_id, contract_value, status, ai_summary, ai_processed_at FROM qlkh_contract WHERE customer_id = (SELECT id FROM qlkh_customer WHERE code = 'KH0001');
```

### 2.5 Tương tác khách hàng (`qlkh.customer_interaction`)
- Hành động: Tạo tương tác với:
  - `customer_id`
  - `type` (gọi điện, gặp mặt, email, hỗ trợ, khiếu nại, khác)
  - `content`
  - `nhan_vien_id`
- Kết quả mong đợi:
  - Bản ghi trong `qlkh_customer_interaction`
  - `type = goi_dien` là ghi nhận cuộc gọi, không có VOIP/sms API mặc định trong repo
  - Nếu có `content`, hệ thống gọi `AIHelper.analyze_sentiment(...)` để phân tích cảm xúc
  - Nếu `sentiment` là `negative` và độ tin cậy >= 0.6, tạo `mail.activity` để quản lý theo dõi
- Lưu ý:
  - `phone` trong `qlkh.customer` chỉ là dữ liệu liên hệ
  - `email` trong `qlkh.customer` dùng cho gửi thông báo email tự động

SQL kiểm tra:
```sql
SELECT id, customer_id, type, sentiment_label, sentiment_score, sentiment_summary FROM qlkh_customer_interaction WHERE customer_id = (SELECT id FROM qlkh_customer WHERE code = 'KH0001');
```

### 2.6 Lịch hẹn khách hàng (`qlkh.appointment`)
- Hành động: Tạo lịch hẹn liên kết `customer_id` với:
  - `appointment_date`
  - `assigned_to`
  - `note`
  - `status`
- Kết quả mong đợi:
  - Bản ghi xuất hiện trong `qlkh_appointment`
  - Trạng thái được cập nhật theo workflow

SQL kiểm tra:
```sql
SELECT id, customer_id, appointment_date, status FROM qlkh_appointment WHERE customer_id = (SELECT id FROM qlkh_customer WHERE code = 'KH0001');
```

---

## 3. Module `quan_ly_van_ban` (Document Management)

### 3.1 Tạo thư mục (`van_ban.folder`)
- Hành động: Tạo folder root hoặc folder con với:
  - `name`
  - `folder_type`
  - `parent_id` (nếu là thư mục con)
- Kết quả mong đợi:
  - Bản ghi `van_ban_folder` xuất hiện
  - Cấu trúc cây folder đúng

SQL kiểm tra:
```sql
SELECT id, name, parent_id, folder_type FROM van_ban_folder WHERE name = 'Hồ sơ nhân viên';
```

### 3.2 Tạo văn bản (`van_ban.document`)
- Hành động: Tạo document với:
  - `name`
  - `folder_id`
  - `loai_van_ban_id`
  - `customer_id` hoặc `related_contract_id` (nếu liên quan)
  - `file` (nếu upload tài liệu)
  - `status`
- Kết quả mong đợi:
  - Bản ghi `van_ban_document` xuất hiện
  - `code` được sinh tự động nếu không cung cấp
  - Nếu có file đính kèm và OCR/AI cấu hình, `ocr_text` và `ai_summary` được điền sau khi xử lý

SQL kiểm tra:
```sql
SELECT id, name, code, folder_id, status, ocr_text, ai_summary FROM van_ban_document WHERE name = 'Hợp đồng KH0001';
```

### 3.3 Quản lý phiên bản (`van_ban.version`)
- Hành động: Thêm version với:
  - `document_id`
  - `version_no`
  - `file`
- Kết quả mong đợi:
  - Bản ghi `van_ban_version` xuất hiện
  - Version được liên kết chính xác tới document

SQL kiểm tra:
```sql
SELECT id, document_id, version_no FROM van_ban_version WHERE document_id = <document_id>;
```

### 3.4 Phê duyệt (`van_ban.approval`)
- Hành động: Tạo approval với:
  - `document_id`
  - `approver_id`
  - `status` (`pending`, `approved`, `rejected`)
  - `note`
- Kết quả mong đợi:
  - Bản ghi `van_ban_approval` xuất hiện
  - Document có thể được cập nhật trạng thái `approved`

SQL kiểm tra:
```sql
SELECT id, document_id, approver_id, status FROM van_ban_approval WHERE document_id = <document_id>;
```

### 3.5 OCR và AI Summary
- Hành động: Upload file văn bản để hệ thống thực hiện:
  - OCR (trích text từ file ảnh/PDF) bằng `pytesseract` và `pdf2image`
  - Tóm tắt nội dung bằng AI qua `AIHelper.summarize_document(...)`
- Kết quả mong đợi:
  - Trường `ocr_text` chứa nội dung nhận dạng
  - Trường `ocr_status` chuyển sang `completed`
  - Trường `ai_summary` chứa tóm tắt ngắn gọn khi văn bản được phê duyệt
  - Khi `van_ban.document.status` đổi thành `approved`, hệ thống gọi `_on_document_approved()` để:
    - tóm tắt nội dung bằng AI
    - gửi thông báo Telegram
    - gửi email cho `customer.email` nếu có
- Nếu service AI/OCR không cấu hình, thao tác vẫn lưu nhưng chỉ log lỗi

SQL kiểm tra:
```sql
SELECT id, ocr_text, ai_summary, ocr_status FROM van_ban_document WHERE id = <document_id>;
```

---

## 4. Luồng tự động giữa các module

### 4.1 Kết nối `nhan_su` → `quan_ly_van_ban`
- Khi tạo nhân viên:
  - Tự động tạo `van_ban.folder` hồ sơ
  - Gán `hr_employee.folder_id`
- Khi thay đổi phòng ban/chức vụ:
  - Cập nhật metadata hồ sơ
  - Có thể tạo activity ghi nhận

### 4.2 Kết nối `qlkh` → `quan_ly_van_ban`
- Khi khách hàng được xác thực (`status = da_xac_thuc`): tạo `qlkh.appointment`
- Khi hợp đồng được phê duyệt: tạo `van_ban.document` hồ sơ hợp đồng
- Khi một hợp đồng hết hạn hoặc cần tái ký: tạo văn bản mới và version mới

### 4.3 Kết nối `qlkh` ← `nhan_su`
- Nhân viên phụ trách được chọn từ `nhan_vien_phu_trach_id`
- KPI nhân viên tính dựa trên số khách hàng, báo giá, hợp đồng
- Nhân viên có thể nhận lịch hẹn và tương tác

### 4.4 Kết nối `qlkh` → `qlkh`
- Báo giá chấp nhận có thể tự động tạo hợp đồng
- Hợp đồng phê duyệt có thể kích hoạt workflow đóng/mở trạng thái

---

## 5. Kiểm tra API / JSON-RPC / SQL

### 5.1 Khi test bằng API Odoo JSON-RPC
#### 5.1.1 Đăng nhập
```bash
curl -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"login","args":["<db>","<username>","<password>"]}}' \
  http://localhost:8069/jsonrpc
```

#### 5.1.2 Tạo bản ghi `don_vi`
```bash
curl -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["<db>", <uid>, "<password>", "don_vi", "create", [[{"ma_don_vi":"DV-001","ten_don_vi":"Kinh doanh"}]]]}}' \
  http://localhost:8069/jsonrpc
```

#### 5.1.3 Tạo nhân viên
```bash
curl -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["<db>", <uid>, "<password>", "hr.employee", "create", [[{"name":"Nguyen Van A","don_vi_id":<don_vi_id>,"work_email":"nva@example.com"}]]]}}' \
  http://localhost:8069/jsonrpc
```

#### 5.1.4 Tạo khách hàng và báo giá
```bash
curl -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["<db>", <uid>, "<password>", "qlkh.customer", "create", [[{"name":"Khách hàng A","code":"KH0001","customer_type":"doanh_nghiep","nhan_vien_phu_trach_id":<employee_id>,"status":"da_xac_thuc"}]]]}}' \
  http://localhost:8069/jsonrpc
```
```
- Sau khi tạo khách hàng `da_xac_thuc`, kiểm tra lịch hẹn mới trong `qlkh.appointment`

### 5.2 Khi test bằng SQL trực tiếp
- Dùng SQL kiểm tra dữ liệu tạo / cập nhật / xóa
- Dùng `SELECT`, `JOIN` và `COUNT` để xác nhận kết quả tự động

Ví dụ:
```sql
SELECT c.id, c.name, c.status, a.id AS appointment_id
FROM qlkh_customer c
LEFT JOIN qlkh_appointment a ON a.customer_id = c.id
WHERE c.code = 'KH0001';
```

### 5.3 Kiểm tra AI/OCR
- Sau khi upload file document, kiểm tra:
  - `ocr_text` khác null
  - `ai_summary` khác null
- Nếu service ngoại trừ không cấu hình, chỉ cần đảm bảo file vẫn lưu được và không gây lỗi blocking

SQL kiểm tra:
```sql
SELECT id, ocr_text IS NOT NULL AS has_ocr, ai_summary IS NOT NULL AS has_ai_summary FROM van_ban_document WHERE id = <document_id>;
```

#### 5.3.1 Kiểm tra sentiment interaction
- Tạo `qlkh.customer_interaction`
- Kiểm tra trường `sentiment`

```sql
SELECT id, sentiment_label, sentiment_score, sentiment_summary, content FROM qlkh_customer_interaction WHERE id = <interaction_id>;
```

#### 5.3.2 Kiểm tra email/Telegram/Google Meet
- Kiểm tra email được gửi khi tạo khách hàng, khi báo giá chuyển trạng thái `dam_phan`, khi hợp đồng/phê duyệt văn bản
- Kiểm tra `customer.email` đã đúng và cấu hình SMTP trong `addons/smart_biz_services/notif_helper.py`
- Kiểm tra trường `meet_url` trong `qlkh_quotation` khi trạng thái = `dam_phan`
- Kiểm tra mail activity trong `mail.activity` nếu automation được kích hoạt

```sql
SELECT id, res_model, res_id, summary, date_deadline FROM mail_activity WHERE res_model IN ('qlkh.quotation','qlkh.contract','qlkh.customer_interaction') ORDER BY id DESC LIMIT 20;
```

### 5.4 Kiểm tra API bằng Python
```python
import xmlrpc.client
url = 'http://localhost:8069'
db = '<db>'
username = '<user>'
password = '<pass>'
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
new_customer = models.execute_kw(db, uid, password, 'qlkh.customer', 'create', [{
    'name': 'Khách hàng API',
    'code': 'KH9999',
    'customer_type': 'doanh_nghiep',
    'nhan_vien_phu_trach_id': <employee_id>,
    'status': 'da_xac_thuc',
}])
print('Created customer', new_customer)
```

### 5.5 Kiểm tra bằng UI
- Tạo, sửa, xóa từng danh mục và nghiệp vụ
- Kiểm tra dữ liệu liên quan tự động xuất hiện
- Kiểm tra trạng thái, mã định danh, liên kết document và appointment

---

## 6. Danh sách test case chi tiết

### 6.1 Nhân sự
1. Tạo `don_vi` và `chuc_vu`
2. Tạo nhân viên mới, kiểm tra `folder_id`
3. Cập nhật `don_vi_id` và `chuc_vu_id`
4. Xóa nhân viên và kiểm tra ràng buộc
5. Tạo chứng chỉ và phân công dự án IoT

### 6.2 CRM
1. Tạo khách hàng mới với `status=moi`
2. Cập nhật `status=da_xac_thuc`, kiểm tra appointment tạo tự động
3. Tạo báo giá, thêm dòng, kiểm tra tổng tiền
4. Đổi trạng thái báo giá, kiểm tra workflow
5. Tạo hợp đồng từ báo giá chấp nhận
6. Tạo tương tác và kiểm tra sentiment AI

### 6.3 Văn bản
1. Tạo `van_ban.folder` thủ công
2. Tạo `van_ban.document` liên kết khách hàng/hợp đồng
3. Upload file, kiểm tra `ocr_text` và `ai_summary`
4. Tạo `van_ban.version`
5. Tạo `van_ban.approval`, phê duyệt và kiểm tra trạng thái

### 6.4 Luồng tích hợp
1. Tạo nhân viên → kiểm tra folder tự động
2. Tạo khách hàng `da_xac_thuc` → kiểm tra appointment
3. Tạo hợp đồng → kiểm tra tạo document/văn bản hồ sơ
4. Tạo khách hàng tương tác → kiểm tra sentiment

---

## 7. Ghi chú kỹ thuật
- Các automation AI/OCR/Notification phụ thuộc service ngoài: nếu chưa cấu hình, hệ thống chỉ ghi log và không chặn CRUD
- Dùng `sudo()` nếu test record cần vượt qua hạn chế quyền
- Trước khi chạy cleanup/xóa dữ liệu, backup database
- Nếu có custom controller API, kiểm tra trong thư mục `controllers/` để biết endpoint cụ thể
- Kiểm tra dữ liệu điền tự động bằng SQL, không chỉ UI

---

## 8. Mẫu kiểm tra API cuối cùng
- `don_vi`, `chuc_vu`, `hr.employee` bằng JSON-RPC
- `qlkh.customer`, `qlkh.quotation`, `qlkh.contract`, `qlkh.customer_interaction` bằng API
- `van_ban.document`, `van_ban.version`, `van_ban.approval` bằng API
- `ocr_text`, `ai_summary`, `sentiment` bằng SQL kiểm tra sau khi upload

> Kết luận: tài liệu này đủ để test toàn bộ luồng nghiệp vụ chính và các cơ chế AI/API trong hệ thống.

---

