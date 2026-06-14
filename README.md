<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
    PLATFORM ERP
</h2>
<div align="center">
    <p align="center">
        <img src="docs/logo/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="docs/logo/fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="docs/logo/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>

## 📖 1. Giới thiệu
Platform ERP được áp dụng vào học phần Thực tập doanh nghiệp dựa trên mã nguồn mở Odoo.

Bộ code này tập trung triển khai ba module chính để phục vụ quản trị nội bộ và quan hệ khách hàng:
- `nhan_su`: quản lý nhân sự (phòng ban, chức vụ, hồ sơ nhân viên, phân công dự án IoT).
- `quan_ly_khach_hang`: quản lý khách hàng, báo giá, hợp đồng và lịch sử tương tác.
- `quan_ly_van_ban`: quản lý văn bản/tài liệu, phân loại, thư mục, phiên bản và quy trình phê duyệt.

File `insert_data.sql` kèm theo cung cấp tập dữ liệu mẫu để khởi tạo và kiểm thử các chức năng chính của ba module trên (nhân viên, khách hàng, báo giá/hợp đồng, văn bản). Các trường cần AI tổng hợp hoặc dữ liệu bổ sung được để trống hoặc có giá trị mẫu, bạn có thể điều chỉnh sau khi nạp dữ liệu vào cơ sở dữ liệu.

## 🔧 2. Các công nghệ được sử dụng
<div align="center">

### Hệ điều hành
[![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
### Công nghệ chính
[![Odoo](https://img.shields.io/badge/Odoo-714B67?style=for-the-badge&logo=odoo&logoColor=white)](https://www.odoo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![XML](https://img.shields.io/badge/XML-FF6600?style=for-the-badge&logo=codeforces&logoColor=white)](https://www.w3.org/XML/)
### Cơ sở dữ liệu
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
</div>

## 🚀 3. Các project đã thực hiện dựa trên Platform

Một số project sinh viên đã thực hiện:
- #### [Khoá 15](./docs/projects/K15/README.md)
- #### [Khoá 16](./docs/projects/K16/README.md)
- #### [Khoá 17](./docs/projects/K17/README.md)
## ⚙️ 4. Cài đặt

### 4.1. Cài đặt công cụ, môi trường và các thư viện cần thiết

#### 4.1.1. Tải project.
```
git clone https://github.com/FIT-DNU/Business-Internship.git
```
#### 4.1.2. Cài đặt các thư viện cần thiết
Người sử dụng thực thi các lệnh sau đề cài đặt các thư viện cần thiết

```
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev python3.10-distutils python3.10-dev build-essential libssl-dev libffi-dev zlib1g-dev python3.10-venv libpq-dev
```
#### 4.1.3. Khởi tạo môi trường ảo.
- Khởi tạo môi trường ảo
```
python3.10 -m venv ./venv
```
- Thay đổi trình thông dịch sang môi trường ảo
```
source venv/bin/activate
```
- Chạy requirements.txt để cài đặt tiếp các thư viện được yêu cầu
```
pip3 install -r requirements.txt
```
### 4.2. Setup database

Khởi tạo database trên docker bằng việc thực thi file dockercompose.yml.
```
sudo docker-compose up -d
```
### 4.3. Setup tham số chạy cho hệ thống
Tạo tệp **odoo.conf** có nội dung như sau:
```
[options]
addons_path = addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5431
xmlrpc_port = 8069
```
Có thể kế thừa từ file **odoo.conf.template**
### 4.4. Chạy hệ thống và cài đặt các ứng dụng cần thiết
Lệnh chạy
```
python3 odoo-bin.py -c odoo.conf -u all
```
Người sử dụng truy cập theo đường dẫn _http://localhost:8069/_ để đăng nhập vào hệ thống.

## 📝 5. License

© 2024 AIoTLab, Faculty of Information Technology, DaiNam University. All rights reserved.

---

## 🔍 6. Phân tích nghiệp vụ (Tóm tắt)

Mục tiêu hệ thống là cung cấp chức năng quản lý nội bộ và quan hệ khách hàng, bao gồm ba module chính sau:

- `nhan_su` (Quản lý nhân sự)
  - Mục tiêu: quản lý nhân viên, cấu trúc tổ chức, hồ sơ, phân công dự án IoT, và liên kết với hệ thống văn bản hồ sơ.
  - Các thực thể chính: `don_vi`, `chuc_vu`, `hr.employee` (mở rộng bởi `NhanVien`), `lich_su_cong_tac`, `iot_project_assignment`.
  - Luồng chính: tạo nhân viên → tự động tạo thư mục hồ sơ (`van_ban.folder`) → gán nhân viên cho khách hàng/khách hàng cho nhân viên → theo dõi lịch sử công tác và phân công dự án.

- `quan_ly_khach_hang` (CRM nhẹ)
  - Mục tiêu: quản lý khách hàng, báo giá, hợp đồng và lịch sử tương tác để hỗ trợ bán hàng và phân công nhân viên chăm sóc.
  - Các thực thể chính: `qlkh.customer`, `qlkh.quotation`, `qlkh.quotation_line`, `qlkh.contract`, `qlkh.customer_interaction`.
  - Luồng chính: tạo khách hàng → (tự động) tạo báo giá → tạo hợp đồng từ báo giá chấp nhận → ghi nhận tương tác và tính toán chỉ số (số báo giá, số hợp đồng, doanh thu).

- `quan_ly_van_ban` (Quản lý văn bản)
  - Mục tiêu: lưu trữ, phân loại, quản lý phiên bản và phê duyệt văn bản/tài liệu liên quan đến khách hàng và nhân sự.
  - Các thực thể chính: `van_ban.document`, `van_ban.version`, `van_ban.approval`, `van_ban.folder`, `loai_van_ban`.
  - Luồng chính: upload/khởi tạo document → gán folder/khách hàng/nhân viên → OCR/AI tóm tắt (tùy chọn) → duyệt/phê duyệt → tạo phiên bản.

Ghi chú: `insert_data.sql` cung cấp dữ liệu mẫu cho các luồng trên (nhân viên, khách hàng, báo giá, hợp đồng, văn bản). Các trường cần tổng hợp bởi AI hoặc thủ công được để trống hoặc điền giá trị mẫu để thuận tiện cho việc kiểm thử.


    
