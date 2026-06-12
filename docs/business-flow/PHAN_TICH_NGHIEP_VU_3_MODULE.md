# PHÂN TÍCH NGHIỆP VỤ CHI TIẾT 3 MODULE QUẢN LÝ
**Dùng cho doanh nghiệp IoT**

---

## Mục lục
1. [Module Quản Lý Nhân Sự (nhan_su)](#1-module-quản-lý-nhân-sự-nhan_su)
2. [Module Quản Lý Khách Hàng (qlkh)](#2-module-quản-lý-khách-hàng-qlkh)
3. [Module Quản Lý Văn Bản (qlvb)](#3-module-quản-lý-văn-bản-qlvb)
4. [Tương Tác Giữa Các Module](#4-tương-tác-giữa-các-module)

---

# 1. MODULE QUẢN LÝ NHÂN SỰ (nhan_su)

## 1.1 Mô Tả Chung
Module **Quản Lý Nhân Sự** là hệ thống quản lý toàn diện thông tin nhân viên của công ty, bao gồm:
- Hồ sơ nhân viên mở rộng (kế thừa từ `hr.employee`)
- Lịch sử công tác và thay đổi vị trí
- Quản lý chứng chỉ, bằng cấp
- Phân công dự án IoT
- Ghi nhận sử dụng thiết bị IoT

## 1.2 Các Bảng Dữ Liệu (Models)

### 1.2.1 **Nhân Viên (nhan_vien)**
**Model**: `hr.employee` (mở rộng)

#### Các Trường Thông Tin:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `ma_dinh_danh` | Char | Mã định danh nhân viên |
| `ho_ten_dem` | Char | Họ tên đệm |
| `ten` | Char | Tên riêng |
| `ho_va_ten` (computed) | Char | Họ và tên đầy đủ (tính toán từ ho_ten_dem + ten) |
| `que_quan` | Char | Quê quán |
| `tuoi` (computed) | Int | Tuổi (tính từ ngày sinh) |
| `so_nguoi_bang_tuoi` (computed) | Int | Số người cùng tuổi trong công ty |
| `don_vi_id` | Many2one | Phòng ban/Đơn vị làm việc |
| `so_khach_hang_phu_trach` (computed) | Int | Số khách hàng đang quản lý |
| `so_bao_gia` (computed) | Int | Số báo giá đã tạo |
| `so_hop_dong` (computed) | Int | Số hợp đồng đã ký |
| `so_van_ban_xu_ly` (computed) | Int | Số văn bản đang xử lý |
| `diem_kpi` (computed) | Float | Điểm KPI (hợp đồng × 10 + báo giá × 2) |
| `muc_tieu_doanh_so` (computed) | Float | Mục tiêu doanh số (hợp đồng × 1M + khách hàng × 500K) |
| `tien_do_kpi` (computed) | Float | % tiến độ KPI |
| `folder_id` | Many2one | Thư mục hồ sơ trong văn bản (tự động tạo) |

#### Quy Trình Khi Tạo Nhân Viên Mới:
1. **Tạo Nhân Viên** → Hệ thống **tự động tạo thư mục hồ sơ** trong module Quản Lý Văn Bản:
   - Folder gốc: "Nhân viên"
   - Folder cấp 2: Tên phòng ban (don_vi)
   - Folder cấp 3: Tên nhân viên

#### Tính Năng Tính Toán:
- **Tuổi**: Lấy năm hiện tại - năm sinh
- **KPI**: Dựa trên số hợp đồng và báo giá
- **Thống Kê**: Liên kết tự động với module QLKH

---

### 1.2.2 **Lịch Sử Công Tác (lich_su_cong_tac)**
**Mục Đích**: Ghi nhận quá trình thay đổi chức vụ, phòng ban của nhân viên

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `chuc_vu_id` | Many2one | Chức vụ chiếm dụng |
| `don_vi_id` | Many2one | Phòng ban công tác |
| `loai_chuc_vu` | Selection | Chính / Kiêm nhiệm |
| `nhan_vien_id` | Many2one | Liên kết nhân viên |

#### Trạng Thái:
- Không có trạng thái cố định, chỉ là lịch sử ghi chép
- Mỗi dòng là một kỳ công tác riêng

---

### 1.2.3 **Chứng Chỉ, Bằng Cấp (chung_chi_bang_cap + danh_sach_chung_chi_bang_cap)**

**Mục Đích**: Ghi nhận trình độ học vấn, chứng chỉ của nhân viên

#### Loại Chứng Chỉ (chung_chi_bang_cap):
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `ma_chung_chi_bang_cap` | Char | Mã chứng chỉ (bắt buộc) |
| `ten_chung_chi_bang_cap` | Char | Tên chứng chỉ (bắt buộc) |

#### Danh Sách Chứng Chỉ Của Nhân Viên (danh_sach_chung_chi_bang_cap):
- Liên kết với nhân viên cụ thể
- Lưu giữ loại chứng chỉ mà nhân viên sở hữu
- Cho phép theo dõi năng lực của từng nhân viên

---

### 1.2.4 **Phân Công Dự Án IoT (iot_project_assignment)**
**Mục Đích**: Quản lý phân công nhân viên vào các dự án IoT

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Tên dự án (bắt buộc) |
| `description` | Text | Mô tả dự án |
| `nhan_vien_id` | Many2one | Nhân viên được phân công (bắt buộc) |
| `role` | Char | Vai trò trong dự án |
| `date_start` | Date | Ngày bắt đầu |
| `date_end` | Date | Ngày kết thúc |
| `note` | Text | Ghi chú |

#### Trạng Thái:
- Không có trạng thái, nhưng `date_start` và `date_end` cho biết dự án đang hoạt động hay đã kết thúc

---

### 1.2.5 **Nhật Ký Thiết Bị IoT (iot_device_log)**
**Mục Đích**: Ghi nhận lịch sử sử dụng, bảo trì, lỗi của thiết bị IoT

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `device_name` | Char | Tên thiết bị (bắt buộc) |
| `device_code` | Char | Mã thiết bị |
| `nhan_vien_id` | Many2one | Nhân viên liên quan (bắt buộc) |
| `event_type` | Selection | Loại sự kiện |
| `event_date` | Datetime | Thời gian sự kiện |
| `note` | Text | Ghi chú |

#### Loại Sự Kiện:
| Giá Trị | Mô Tả |
|--------|-------|
| `use` | Sử dụng thiết bị |
| `maintenance` | Bảo trì định kỳ |
| `error` | Phát hiện sự cố/lỗi |
| `return` | Thu hồi thiết bị |

#### Quy Trình Ghi Nhận:
1. **Khi sử dụng thiết bị** → Tạo bản ghi loại `use`
2. **Khi bảo trì** → Tạo bản ghi loại `maintenance`
3. **Khi lỗi** → Tạo bản ghi loại `error` + note
4. **Khi thu hồi** → Tạo bản ghi loại `return`

---

### 1.2.6 **Đơn Vị / Phòng Ban (don_vi)**
**Mục Đích**: Danh mục các phòng ban, đơn vị trong công ty

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `ma_don_vi` | Char | Mã phòng ban (bắt buộc) |
| `ten_don_vi` | Char | Tên phòng ban (bắt buộc) |

#### Ví Dụ:
- Phòng Kinh Doanh
- Phòng Kỹ Thuật
- Phòng Hành Chính

---

### 1.2.7 **Chức Vụ (chuc_vu)**
**Mục Đích**: Danh mục các chức vụ trong công ty

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `ma_chuc_vu` | Char | Mã chức vụ (bắt buộc) |
| `ten_chuc_vu` | Char | Tên chức vụ (bắt buộc) |

#### Ví Dụ:
- Giám Đốc
- Trưởng Phòng
- Nhân Viên Kinh Doanh
- Kỹ Sư Phần Mềm

---

## 1.3 Luồng Công Việc & Trạng Thái

### Luồng Tạo Nhân Viên Mới:
```
1. Tạo hồ sơ nhân viên mới
   ↓
2. Hệ thống tự động:
   - Tạo thư mục hồ sơ
   - Tính toán KPI
   ↓
3. Gán chức vụ ban đầu → Lưu vào "Lịch sử công tác"
   ↓
4. Có thể phân công dự án IoT
   ↓
5. Khi sử dụng thiết bị → Ghi nhận nhật ký
```

### Luồng Thay Đổi Chức Vụ:
```
1. Nhân viên X có chức vụ A, phòng ban P1
   ↓
2. Cần thay đổi → Tạo mới dòng "Lịch sử công tác"
   - Chức vụ mới: B
   - Phòng ban mới: P2
   ↓
3. Dữ liệu cũ vẫn lưu trữ để theo dõi quá trình
```

---

## 1.4 Tính Năng Tính Toán & KPI

### KPI của Nhân Viên:
```
Điểm KPI = (Số hợp đồng × 10) + (Số báo giá × 2)

Mục tiêu doanh số = (Số hợp đồng × 1,000,000) + (Số khách hàng × 500,000)

Tiến độ KPI = (Điểm KPI / 100) × 100%
```

### Ghi Chú Nhân Sự:
```
"Tổng số khách hàng: X. Báo giá: Y. Hợp đồng: Z. Văn bản xử lý: W."
```

### Thống Kê Liên Quan:
- **Số khách hàng phụ trách**: Lấy từ QLKH (customer.nhan_vien_phu_trach_id)
- **Số báo giá**: Lấy từ QLKH (quotation)
- **Số hợp đồng**: Lấy từ QLKH (contract)
- **Số văn bản**: Lấy từ QLVB (document)

---

---

# 2. MODULE QUẢN LÝ KHÁCH HÀNG (qlkh)

## 2.1 Mô Tả Chung
Module **Quản Lý Khách Hàng** là hệ thống quản lý toàn vòng đời khách hàng từ tiềm năng đến thành công:
- Hồ sơ khách hàng
- Báo giá
- Hợp đồng
- Lịch sử giao dịch & chăm sóc khách hàng
- Lịch hẹn (appointment)

## 2.2 Các Bảng Dữ Liệu (Models)

### 2.2.1 **Khách Hàng (customer)**
**Model**: `qlkh.customer`

#### Các Trường Thông Tin:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Tên khách hàng (bắt buộc, duy nhất) |
| `code` | Char | Mã khách hàng (bắt buộc, duy nhất) |
| `customer_type` | Selection | Cá nhân / Doanh nghiệp |
| `status` | Selection | **[Xem chi tiết dưới]** |
| `nhan_vien_phu_trach_id` | Many2one | Nhân viên phụ trách (bắt buộc) |
| `iot_device` | Char | Thiết bị IoT sử dụng |
| `email` | Char | Email liên hệ |
| `phone` | Char | Số điện thoại |
| `address` | Char | Địa chỉ |
| `note` | Text | Ghi chú |
| `interaction_count` (computed) | Int | Số lần tương tác |
| `quotation_count` (computed) | Int | Số báo giá |
| `contract_count` (computed) | Int | Số hợp đồng |
| `revenue_total` (computed) | Float | Tổng doanh thu từ hợp đồng |
| `customer_score` (computed) | Float | Điểm khách hàng (0-100) |

#### Công Thức Tính Customer Score:
```
Score = (interaction_count × 2) 
       + (quotation_count × 5) 
       + (contract_count × 10) 
       + (revenue_total / 10,000,000)

Min: 0, Max: 100
```

---

### 2.2.2 **Trạng Thái Khách Hàng (Status Flow)**

```
┌─────────────────────────────────────────────────────────────┐
│                 TRẠNG THÁI KHÁCH HÀNG                        │
└─────────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════════╗
║ 1. KHÁCH HÀNG TIỀM NĂNG (khach_hang_tiem_nang) [Trạng thái ban đầu] ║
╠════════════════════════════════════════════════════════════════════╣
║ • Khách hàng mới được tìm kiếm, chưa có xác nhận                   ║
║ • Chưa có báo giá nào                                              ║
║ • Hoạt động: Lịch hẹn chăm sóc → Tương tác theo dõi               ║
║ • Chuyển sang: Lịch hẹn hoàn thành → Đã xác thực                  ║
╚════════════════════════════════════════════════════════════════════╝

                           ↓
                    
╔════════════════════════════════════════════════════════════════════╗
║ 2. ĐÃ XÁC THỰC (da_xac_thuc)                                      ║
╠════════════════════════════════════════════════════════════════════╣
║ • Khách hàng xác nhận quan tâm, đã ghi danh                        ║
║ • Hệ thống tự động tạo: Lịch hẹn chăm sóc "Mới"                   ║
║ • Hoạt động: Gửi báo giá, tương tác sâu                           ║
║ • Chuyển sang: Cần báo giá → Báo giá                              ║
║              hoặc Lịch hẹn hoàn thành + không có báo giá → Báo giá║
╚════════════════════════════════════════════════════════════════════╝

                           ↓
                    
╔════════════════════════════════════════════════════════════════════╗
║ 3. BÁO GIÁ (bao_gia)                                               ║
╠════════════════════════════════════════════════════════════════════╣
║ • Khách hàng đã nhận báo giá                                        ║
║ • Hệ thống tự động tạo báo giá đầu tiên (nếu chưa có)             ║
║ • Báo giá ở trạng thái "Nháp" (nhap)                               ║
║ • Hoạt động: Gửi email báo giá, đàm phán                          ║
║ • Chuyển sang: Báo giá được chấp nhận → Đàm phán                  ║
║              hoặc Từ chối → Thất bại                              ║
╚════════════════════════════════════════════════════════════════════╝

                    /                       \
                   /                         \
                  ↙                           ↙
                  
╔══════════════════════════╗      ╔══════════════════════════════════════════╗
║ 4. ĐÀM PHÁN (dam_phan)   ║      ║ 5. THẤT BẠI (that_bai)                  ║
╠══════════════════════════╣      ╠══════════════════════════════════════════╣
║ • Khách hàng chấp nhận   ║      ║ • Khách hàng từ chối báo giá             ║
║   báo giá                ║      ║ • Hoặc không tiếp tục đàm phán           ║
║ • Hợp đồng được tạo     ║      ║ • Không có tương tác thêm                 ║
║ • Chuẩn bị ký kết       ║      ║ • Có thể được kích hoạt lại với báo giá  ║
║ • Chuyển sang:          ║      ║   mới                                      ║
║   Hợp đồng được duyệt  ║      ║                                            ║
║   → Thành công          ║      ║                                            ║
╚══════════════════════════╝      ╚══════════════════════════════════════════╝

                  ↓
                  
╔════════════════════════════════════════════════════════════════════╗
║ 6. THÀNH CÔNG (thanh_cong) [Trạng thái cuối cùng]                 ║
╠════════════════════════════════════════════════════════════════════╣
║ • Hợp đồng được kích hoạt (hieu_luc)                               ║
║ • Khách hàng là khách hàng thực sự                                 ║
║ • Tiếp tục chăm sóc và hỗ trợ                                      ║
║ • Theo dõi tình trạng hợp đồng                                     ║
╚════════════════════════════════════════════════════════════════════╝
```

#### Bảng Tóm Tắt Trạng Thái:
| Trạng Thái | Code | Mô Tả | Điểm Kích Hoạt |
|------------|------|-------|---|
| Khách Hàng Tiềm Năng | `khach_hang_tiem_nang` | Ban đầu | Tạo khách hàng |
| Đã Xác Thực | `da_xac_thuc` | Xác nhận quan tâm | Lịch hẹn hoàn thành |
| Báo Giá | `bao_gia` | Đang gửi báo giá | Thay đổi status |
| Đàm Phán | `dam_phan` | Chấp nhận báo giá | Báo giá.action_accept |
| Thành Công | `thanh_cong` | Hợp đồng hoạt động | Hợp đồng.action_activate |
| Thất Bại | `that_bai` | Không thành công | Từ chối báo giá |

---

### 2.2.3 **Báo Giá (quotation)**
**Model**: `qlkh.quotation`

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Số báo giá (bắt buộc, duy nhất) |
| `customer_id` | Many2one | Khách hàng (bắt buộc) |
| `date` | Date | Ngày báo giá (bắt buộc) |
| `status` | Selection | **[Xem dưới]** |
| `file` | Binary | File báo giá |
| `file_name` | Char | Tên file |
| `note` | Text | Ghi chú |
| `quotation_value` (computed) | Float | Tổng giá trị = SUM(line.price_total) |
| `line_ids` | One2many | Chi tiết sản phẩm |
| `contract_ids` | One2many | Hợp đồng tạo từ báo giá |

#### Trạng Thái Báo Giá:
```
┌─────────────────────────────────────────────────────────┐
│           TRẠNG THÁI BÁO GIÁ                           │
└─────────────────────────────────────────────────────────┘

NHÁP (nhap) [Bắt đầu]
  ↓ (Gửi email)
ĐÃ GỬI (da_gui)
  ↓ (Khách hàng xem)
ĐÃ XEM (da_xem)
  ↓ (Đàm phán, yêu cầu sửa)
ĐÀM PHÁN (dam_phan)
  ↙                       ↘
CHẤP NHẬN (chap_nhan)    TỪ CHỐI (tu_choi)
  ↓
TẠO HỢP ĐỒNG
```

#### Chi Tiết Dòng Báo Giá (quotation_line):
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `quotation_id` | Many2one | Báo giá |
| `product_name` | Char | Tên sản phẩm |
| `description` | Text | Mô tả |
| `quantity` | Float | Số lượng |
| `unit_price` | Float | Đơn giá |
| `vat_rate` | Float | Tỷ lệ VAT (%) |
| `price_subtotal` | Float | Thành tiền = quantity × unit_price |
| `price_tax` | Float | Tiền thuế = price_subtotal × vat_rate |
| `price_total` | Float | Tổng = price_subtotal + price_tax |

#### Hành Động Chính:
- **Gửi Email**: Gửi báo giá cho khách hàng
- **Chấp Nhận**: Khách hàng chấp nhận → Tạo hợp đồng mới

---

### 2.2.4 **Hợp Đồng (contract)**
**Model**: `qlkh.contract`

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Số hợp đồng (bắt buộc, duy nhất) |
| `customer_id` | Many2one | Khách hàng (bắt buộc) |
| `quotation_id` | Many2one | Báo giá nguồn |
| `date_start` | Date | Ngày bắt đầu (bắt buộc) |
| `date_end` | Date | Ngày kết thúc (bắt buộc) |
| `contract_value` | Float | Giá trị hợp đồng |
| `status` | Selection | **[Xem dưới]** |
| `iot_device` | Char | Thiết bị IoT bảo trì |
| `file` | Binary | File hợp đồng |
| `file_name` | Char | Tên file |
| `note` | Text | Ghi chú |

#### Trạng Thái Hợp Đồng:
```
┌──────────────────────────────────────────────────────┐
│         TRẠNG THÁI HỢP ĐỒNG                         │
└──────────────────────────────────────────────────────┘

NHÁP (nhap) [Bắt đầu]
  ↓ (Gửi duyệt)
CHỜ DUYỆT (cho_duyet)
  ↓ (Phê duyệt)
ĐÃ DUYỆT (da_duyet)
  ↓ (Tạo văn bản + Kích hoạt)
HIỆU LỰC (hieu_luc) [Đang hoạt động]
  ↓ (Cron Job kiểm tra hạn)
  
  ├─ SẮP HẾT HẠN (sap_het_han) [<= 30 ngày]
  │   ↓
  │   HẾT HẠN (het_han)
  │
  └─ HẾT HẠN (het_han) [> 30 ngày]
```

#### Quy Trình Hợp Đồng Chi Tiết:

**1. Tạo từ Báo Giá (Nháp)**
- Khi báo giá được chấp nhận → Hợp đồng tạo với trạng thái "Nháp"
- Số HD: `HD-{SoBaoGia}`
- Giá trị HD: = Giá trị báo giá

**2. Gửi Duyệt**
```
Nháp → Chờ Duyệt
```

**3. Phê Duyệt** 
```
Chờ Duyệt → Đã Duyệt
- Tự động tạo văn bản (document) liên kết
- Loại: "Hồ sơ hợp đồng"
- Quét OCR nếu file có sẵn
```

**4. Kích Hoạt**
```
Đã Duyệt → Hiệu Lực
- Cập nhật trạng thái khách hàng → Thành Công
- Hợp đồng bắt đầu hiệu lực
```

**5. Giám Sát Hạn**
- Hệ thống chạy cron job kiểm tra hằng ngày
- Nếu `date_end <= 30 ngày từ hôm nay` → `sap_het_han`
- Nếu `date_end < hôm nay` → `het_han`
- Tạo mail activity cảnh báo

**6. Lưu Trữ**
```
Hết Hạn → Lưu Trữ (cron job)
- Văn bản liên kết → Trạng thái "Lưu trữ"
```

#### Ràng Buộc:
- `date_end` phải > `date_start`

---

### 2.2.5 **Lịch Sử Giao Dịch, Chăm Sóc KH (customer_interaction)**
**Model**: `qlkh.customer_interaction`

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `customer_id` | Many2one | Khách hàng (bắt buộc) |
| `date` | Datetime | Thời gian tương tác |
| `type` | Selection | Loại tương tác |
| `status` | Selection | Trạng thái |
| `content` | Text | Nội dung |
| `nhan_vien_id` | Many2one | Nhân viên thực hiện |
| `note` | Text | Ghi chú |

#### Loại Tương Tác:
- `goi_dien` - Gọi điện
- `gap_mat` - Gặp mặt
- `email` - Email
- `ho_tro` - Hỗ trợ
- `khieu_nai` - Khiếu nại
- `khac` - Khác

#### Trạng Thái Tương Tác:
- `moi` - Mới
- `da_thuc_hien` - Đã thực hiện
- `huy` - Hủy

---

### 2.2.6 **Lịch Hẹn (appointment)**
**Model**: `qlkh.appointment`

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Tiêu đề lịch hẹn (bắt buộc) |
| `customer_id` | Many2one | Khách hàng (bắt buộc) |
| `nhan_vien_id` | Many2one | Nhân viên phụ trách |
| `appointment_date` | Datetime | Ngày hẹn (bắt buộc) |
| `status` | Selection | Trạng thái |
| `follow_up_id` | Many2one | Lịch hẹn follow-up (readonly) |
| `related_quotation_id` | Many2one | Báo giá tạo tự động (readonly) |
| `note` | Text | Ghi chú |

#### Trạng Thái Lịch Hẹn:
```
┌────────────────────────────────────────────────────┐
│       TRẠNG THÁI LỊCH HẸN (APPOINTMENT)           │
└────────────────────────────────────────────────────┘

MỚI (moi) [Bắt đầu]
  ↓ (Xác nhận)
ĐÃ XÁC NHẬN (da_xac_nhan)
  ↓ (Thực hiện cuộc hẹn)
HOÀN THÀNH (hoan_thanh)
  ↓ Hệ thống tự động:
  ├─ Tạo follow-up (1 ngày sau)
  ├─ Nếu khách hàng ở trạng thái 
  │  "Đã xác thực" hoặc "Tiềm năng" 
  │  → Tạo báo giá mới
  │  → Cập nhật KH → Báo giá
  └─ Báo giá đó ở trạng thái "Nháp"

    hoặc
    
HỦY (huy) [Hủy bỏ]
```

#### Tự Động Tạo:
1. Khi khách hàng ở trạng thái `da_xac_thuc` → Tạo lịch hẹn "Mới"
2. Khi lịch hẹn hoàn thành:
   - Tạo follow-up 1 ngày sau
   - Tạo báo giá mới (nếu chưa có)
   - Cập nhật trạng thái KH → `bao_gia`

---

## 2.3 Tương Tác Giữa Các Module QLKH

### Luồng Chính:
```
┌─────────────────────────────────────────────────────┐
│        LUỒNG QUẢN LÝ KHÁCH HÀNG TỪ ĐẦU ĐẾN CUỐI     │
└─────────────────────────────────────────────────────┘

1. TẠO KHÁCH HÀNG
   - Gán nhân viên phụ trách
   - Loại: Cá nhân / Doanh nghiệp
   - Trạng thái: Tiềm năng
   
   ↓
   
2. TẠO LỊCH HẸN (Tự động hoặc thủ công)
   - Loại: Chăm sóc KH
   - Trạng thái: Mới
   
   ↓
   
3. THỰC HIỆN LỊCH HẹN
   - Ghi nhận tương tác
   - Hoàn thành lịch hẹn
   
   ↓
   
4. KHÁCH HÀNG → ĐÃ XÁC THỰC
   (Nếu lịch hẹn hoàn thành)
   
   ↓
   
5. TẠO BÁO GIÁ (Tự động hoặc thủ công)
   - Trạng thái: Nháp
   - Thêm chi tiết sản phẩm
   - Tính toán giá trị
   
   ↓
   
6. GỬI BÁO GIÁ CHO KHÁCH HÀNG
   - Trạng thái: Đã gửi
   - Gửi email + file
   
   ↓
   
7. KHÁCH HÀNG PHẢN HỒI
   - Đã xem (Trạng thái: Đã xem)
   - Đàm phán (Trạng thái: Đàm phán)
   - Từ chối (Trạng thái: Từ chối)
     → Khách hàng: Thất bại
   
   ↓ (Nếu chấp nhận)
   
8. CHẤP NHẬN BÁO GIÁ
   - Báo giá → Chấp nhận
   - Hợp đồng được tạo (Nháp)
   - Khách hàng → Đàm phán
   
   ↓
   
9. GỬI HỢP ĐỒNG DUYỆT
   - Hợp đồng → Chờ duyệt
   
   ↓
   
10. PHÊ DUYỆT HỢP ĐỒNG
    - Hợp đồng → Đã duyệt
    - Tự động tạo văn bản (QLVB)
    
    ↓
    
11. KÍCH HOẠT HỢP ĐỒNG
    - Hợp đồng → Hiệu lực
    - Khách hàng → Thành công
    
    ↓
    
12. THEO DÕI & BẢO TRÌ
    - Cron job: Kiểm tra hạn
    - Cảnh báo sắp hết hạn
    - Tương tác chăm sóc
    
    ↓
    
13. HẾT HẠN & LƯU TRỮ
    - Hợp đồng → Hết hạn
    - Văn bản → Lưu trữ
```

---

---

# 3. MODULE QUẢN LÝ VĂN BẢN (qlvb)

## 3.1 Mô Tả Chung
Module **Quản Lý Văn Bản Điện Tử** là hệ thống quản lý tài liệu với các tính năng:
- Lưu trữ và quản lý văn bản điện tử
- Quét OCR tự động (PDF, hình ảnh)
- Tổ chức thư mục
- Quản lý công văn (văn bản đến, đi)
- Quy trình phê duyệt & xử lý
- Lịch sử phiên bản

## 3.2 Các Bảng Dữ Liệu (Models)

### 3.2.1 **Văn Bản / Tài Liệu (van_ban.document)**
**Model**: `van_ban.document` (kế thừa mail.thread, mail.activity.mixin)

#### Các Trường Thông Tin:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Tiêu đề (bắt buộc) |
| `code` | Char | Mã văn bản (tự động, readonly) |
| `doc_type` | Selection | Loại văn bản tạm |
| `loai_van_ban_id` | Many2one | Loại văn bản từ danh mục |
| `customer_id` | Many2one | Khách hàng liên quan |
| `folder_id` | Many2one | Thư mục chứa |
| `nhan_vien_id` | Many2one | Nhân viên chịu trách nhiệm |
| `related_contract_id` | Many2one | Hợp đồng liên quan |
| `related_quotation_id` | Many2one | Báo giá liên quan |
| `file` | Binary | File tài liệu |
| `file_name` | Char | Tên file |
| `file_size` (computed) | Int | Kích thước (bytes) |
| `file_type` (computed) | Char | Loại file (pdf, jpg, ...) |
| `status` | Selection | Trạng thái |
| `date` | Date | Ngày tạo |
| `date_upload` | Datetime | Ngày upload |
| `note` | Text | Ghi chú |

#### Loại Văn Bản (doc_type):
- `bao_gia` - Báo giá
- `hop_dong` - Hợp đồng
- `phu_luc` - Phụ lục
- `phap_ly` - Hồ sơ pháp lý
- `khac` - Khác

---

### 3.2.2 **OCR & Quét Tài Liệu**

#### Các Trường OCR:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `ocr_text` | Text | Nội dung quét (readonly) |
| `ocr_date` | Datetime | Ngày quét (readonly) |
| `ocr_status` | Selection | Trạng thái quét |

#### Trạng Thái OCR:
```
┌──────────────────────────────────────────────────┐
│     TRẠNG THÁI QUÉ OCR TÀI LIỆU                  │
└──────────────────────────────────────────────────┘

CHƯA QUÉT (not_started) [Ban đầu]
  ↓ (Nhấn nút "Quét OCR")
ĐANG XỬ LÝ (processing)
  ↓ (Hoàn thành)
  
  ├─ HOÀN THÀNH (completed) [Thành công]
  │    - Nội dung OCR được lưu
  │    - Có thể xem nội dung
  │
  └─ THẤT BẠI (failed) [Lỗi]
       - Có thể thử lại
```

#### Hành Động OCR:
1. **Quét OCR** (`action_scan_ocr`):
   - Cần có file
   - Hỗ trợ PDF, JPG, PNG, BMP, GIF
   - PDF: Quét từng trang, nối lại
   - Ảnh: Quét trực tiếp
   - Lưu kết quả vào `ocr_text`, `ocr_date`

2. **Xem OCR** (`action_view_ocr`):
   - Hiển thị nội dung đã quét

3. **Tải OCR** (`action_download_ocr_text`):
   - Tải file text từ nội dung OCR

#### PDF Pages:
| Trường | Mô Tả |
|--------|-------|
| `total_pages` (computed) | Số trang PDF |
| `current_page` | Trang hiện tại đang xem |
| `page_images` | Base64 của các trang |

---

### 3.2.3 **Trạng Thái Văn Bản (Status)**
```
┌────────────────────────────────────────────────────┐
│      TRẠNG THÁI TÀI LIỆU                          │
└────────────────────────────────────────────────────┘

NHÁP (draft) [Bắt đầu]
  ↓ (Gửi duyệt)
CHỜ DUYỆT (to_approve)
  ↓ (Quy trình phê duyệt)
ĐÃ DUYỆT (approved)
  ↓ (Theo thời gian)
LƯU TRỮ (archived)
```

#### Thông Tin Phê Duyệt:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `is_locked` | Boolean | Khóa chỉnh sửa |
| `approved_date` | Datetime | Ngày duyệt |
| `approved_by` | Many2one | Người duyệt |
| `current_version` | Char | Phiên bản hiện tại (v1, v2, ...) |

---

### 3.2.4 **Thư Mục Văn Bản (van_ban.folder)**
**Model**: `van_ban.folder` (Cấu trúc cây)

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Tên thư mục (bắt buộc) |
| `parent_id` | Many2one | Thư mục cha |
| `child_ids` | One2many | Thư mục con |
| `document_ids` | One2many | Tài liệu trong thư mục |
| `document_count` (computed) | Int | Số tài liệu |
| `complete_name` (computed) | Char | Đường dẫn đầy đủ |
| `folder_type` | Selection | Loại thư mục |

#### Loại Thư Mục:
- `customer` - Khách hàng
- `employee` - Nhân viên (tạo tự động)
- `general` - Chung

#### Cấu Trúc Thư Mục Tự Động:
```
Nhân viên/
  ├─ Phòng Ban 1/
  │   ├─ Nhân Viên A/
  │   ├─ Nhân Viên B/
  │   └─ ...
  ├─ Phòng Ban 2/
  │   └─ ...
  └─ ...
```

**Tạo tự động khi**:
- Tạo nhân viên mới trong nhan_su module
- Khi hợp đồng được phê duyệt (tạo văn bản hồ sơ)

---

### 3.2.5 **Quy Trình Phê Duyệt (van_ban.routing)**
**Mục Đích**: Quản lý luồng xử lý tài liệu

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `name` | Char | Tiêu đề quy trình (bắt buộc) |
| `document_id` | Many2one | Tài liệu (bắt buộc) |
| `assigned_to` | Many2one | Người xử lý |
| `stage` | Selection | Trạng thái |
| `date_deadline` | Date | Hạn xử lý |
| `note` | Text | Ghi chú |

#### Trạng Thái Quy Trình:
```
┌─────────────────────────────────────┐
│    TRẠNG THÁI QUY TRÌNH ROUTING     │
└─────────────────────────────────────┘

CHỜ XỬ LÝ (to_process) [Mới]
  ↓ (Bắt đầu)
ĐANG XỬ LÝ (in_progress)
  ↓ (Hoàn thành xử lý)
HOÀN TẤT (done)
  ↓ Cập nhật Văn Bản:
  ├─ status → approved
  ├─ is_locked → True
  ├─ approved_date → Hôm nay
  ├─ approved_by → assigned_to
  └─ Tạo bản ghi van_ban.approval

    hoặc
    
TỪ CHỐI (rejected)
  ↓
Văn Bản → Draft (chỉnh sửa lại)
```

---

### 3.2.6 **Phiên Bản Tài Liệu (van_ban.version)**
**Mục Đích**: Lưu trữ các phiên bản cũ của tài liệu

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `document_id` | Many2one | Tài liệu (bắt buộc) |
| `version_no` | Char | Số phiên bản (v1, v2, ...) |
| `file` | Binary | File phiên bản |
| `file_name` | Char | Tên file |
| `created_by` | Many2one | Người tạo |
| `created_date` | Datetime | Ngày tạo |
| `note` | Text | Ghi chú |

#### Cách Sử Dụng:
- Khi cập nhật file → Tạo version mới
- Có thể khôi phục phiên bản cũ
- Lưu lịch sử thay đổi

---

### 3.2.7 **Phê Duyệt (van_ban.approval)**
**Mục Đích**: Ghi nhận người đã phê duyệt

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `document_id` | Many2one | Tài liệu (bắt buộc) |
| `approver_id` | Many2one | Người phê duyệt |
| `status` | Selection | Trạng thái |

---

### 3.2.8 **Văn Bản Đến (van_ban_den)**
**Mục Đích**: Ghi nhận công văn nhận từ bên ngoài

#### Các Trường Chính:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `document_id` | Many2one | Văn bản gốc (bắt buộc) |
| `so_van_ban_den` | Char | Số văn bản đến (bắt buộc) |
| `ten_van_ban` | Char | Tên văn bản (bắt buộc) |
| `so_hieu_van_ban` | Char | Số hiệu (bắt buộc) |
| `loai_van_ban_id` | Many2one | Loại văn bản |
| `customer_id` | Many2one | Khách hàng gửi |
| `ngay_den` | Date | Ngày đến (bắt buộc) |
| `ngay_ban_hanh` | Date | Ngày ban hành |
| `nhan_vien_nhan_id` | Many2one | Nhân viên tiếp nhận |
| `nhan_vien_chuyen_id` | Many2one | Nhân viên chuyển xử lý |
| `trich_yeu` | Text | Trích yếu nội dung |
| `ghi_chu` | Text | Ghi chú |
| `trang_thai` | Selection | Trạng thái xử lý |
| `lich_su_xu_ly` (computed) | Text | Lịch sử xử lý (readonly) |

#### Trạng Thái Văn Bản Đến:
```
┌────────────────────────────────────┐
│   TRẠNG THÁI VĂN BẢN ĐẾN           │
└────────────────────────────────────┘

MỚI NHẬN (moi) [Bắt đầu]
  ↓ (Giao việc, bắt đầu xử lý)
ĐANG XỬ LÝ (dang_xu_ly)
  ↓ (Xử lý xong)
ĐÃ XỬ LÝ (da_xu_ly)
  ↓ (Lưu trữ)
LƯU TRỮ (luu_tru)
```

#### Hành Động:
- `action_xac_nhan_xu_ly()`: Chuyển Mới → Đang xử lý → Đã xử lý
- `action_luu_tru()`: Chuyển sang Lưu trữ

---

### 3.2.9 **Văn Bản Đi (van_ban_di)**
**Mục Đích**: Ghi nhận công văn gửi đi cho khách hàng/đối tác

#### Các Trường Chính:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `document_id` | Many2one | Văn bản gốc (bắt buộc) |
| `so_van_ban_di` | Char | Số văn bản đi (bắt buộc) |
| `ten_van_ban` | Char | Tên văn bản (bắt buộc) |
| `so_hieu_van_ban` | Char | Số hiệu (bắt buộc) |
| `loai_van_ban_id` | Many2one | Loại văn bản |
| `customer_id` | Many2one | Khách hàng nhận |
| `ngay_di` | Date | Ngày đi (bắt buộc) |
| `ngay_ban_hanh` | Date | Ngày ban hành |
| `nhan_vien_tao_id` | Many2one | Nhân viên tạo |
| `nhan_vien_ky_id` | Many2one | Người ký |
| `noi_nhan` | Char | Nơi nhận |
| `trich_yeu` | Text | Trích yếu nội dung |
| `ghi_chu` | Text | Ghi chú |
| `trang_thai` | Selection | Trạng thái xử lý |
| `lich_su_gui` (computed) | Text | Lịch sử gửi (readonly) |

#### Trạng Thái Văn Bản Đi:
```
┌────────────────────────────────────┐
│   TRẠNG THÁI VĂN BẢN ĐI            │
└────────────────────────────────────┘

NHÁP (draft) [Bắt đầu]
  ↓ (Trình ký)
ĐÃ KÝ (da_ky)
  ↓ (Xác nhận gửi)
ĐÃ GỬI (da_gui)
  ↓ (Hoàn thành xử lý)
HOÀN THÀNH (hoan_thanh)
```

#### Hành Động:
- `action_trinh_ky()`: Draft → Đã ký
- `action_xac_nhan_gui()`: Đã ký → Đã gửi
- `action_hoan_thanh()`: Đã gửi → Hoàn thành

---

### 3.2.10 **Loại Văn Bản (loai_van_ban)**
**Mục Đích**: Danh mục các loại văn bản

#### Các Trường:
| Trường | Kiểu | Mô Tả |
|--------|------|-------|
| `ma_loai_van_ban` | Char | Mã loại (bắt buộc) |
| `ten_loai_van_ban` | Char | Tên loại (bắt buộc) |

#### Ví Dụ:
- HD001 - Hợp Đồng Dịch Vụ
- BG001 - Báo Giá Dịch Vụ
- CV001 - Công Văn Hành Chính
- ...

---

## 3.3 Luồng Công Việc Quản Lý Văn Bản

### Luồng 1: Tạo & Quét Văn Bản Thông Thường
```
1. TẠO TÀI LIỆU
   - Nhập tiêu đề
   - Chọn loại
   - Upload file
   - Liên kết khách hàng/hợp đồng
   → Trạng thái: NHÁP

   ↓

2. QUÉT OCR
   - Nhấn nút "Quét OCR"
   - Hệ thống xử lý
   → OCR Status: Processing
   
   ↓ (Hoàn thành)
   
3. OCR HOÀN THÀNH
   - Nội dung OCR được lưu
   - Có thể xem nội dung
   → OCR Status: Completed

   ↓

4. GỬI DUYỆT (Tùy chọn)
   - Chuyển sang "Chờ duyệt"
   → Status: TO_APPROVE

   ↓

5. PHÊ DUYỆT
   - Tạo quy trình routing
   - Phân công cho người duyệt
   → Status: APPROVED

   ↓

6. LƯU TRỮ
   → Status: ARCHIVED
```

### Luồng 2: Hợp Đồng Tạo Tự Động Từ QLKH
```
(Từ Module Quản Lý Khách Hàng)

1. HỢP ĐỒNG ĐƯỢC PHÊ DUYỆT (action_approve)
   
   ↓
   
2. QLVB TỰ ĐỘNG TẠO:
   - name: "Hồ sơ hợp đồng {contract.name}"
   - doc_type: "hop_dong"
   - related_contract_id: Liên kết
   - Status: DRAFT
   - File: Sao chép từ hợp đồng (nếu có)
   
   ↓
   
3. NẾU CÓ FILE:
   - Tự động quét OCR
   - OCR Status: PROCESSING → COMPLETED
   
   ↓
   
4. GỬI DUYỆT:
   - Tạo quy trình routing
   → Status: APPROVED
   
   ↓
   
5. KHÓA & LƯU TRỮ:
   - is_locked: True
   - Khi hợp đồng hết hạn
   → Status: ARCHIVED
```

### Luồng 3: Công Văn Đến
```
1. NHẬN CÔNG VĂN
   - Ghi nhận số văn bản đến
   - Loại văn bản
   - Khách hàng gửi
   → Trạng thái: MỚI NHẬN

   ↓

2. XỬ LÝ
   - Gán nhân viên xử lý
   - Thêm ghi chú
   → Trạng thái: ĐANG XỬ LÝ

   ↓

3. HOÀN THÀNH XỬ LÝ
   - Cập nhật ghi chú kết quả
   → Trạng thái: ĐÃ XỬ LÝ

   ↓

4. LƯU TRỮ
   → Trạng thái: LƯU TRỮ
```

### Luồng 4: Công Văn Đi
```
1. TẠO CÔNG VĂN
   - Nhập tên, số hiệu
   - Loại văn bản
   - Nơi nhận
   → Trạng thái: NHÁP

   ↓

2. TRÌNH KÝ
   - Giao cho người ký
   → Trạng thái: ĐÃ KÝ

   ↓

3. XÁC NHẬN GỬI
   - Cập nhật ngày gửi
   → Trạng thái: ĐÃ GỬI

   ↓

4. HOÀN THÀNH
   - Công văn được gửi thành công
   → Trạng thái: HOÀN THÀNH
```

---

---

# 4. TƯƠNG TÁC GIỮA CÁC MODULE

## 4.1 Mối Liên Kết Giữa 3 Module

```
┌──────────────────────────────────────────────────────────────┐
│                   TƯƠNG TÁC 3 MODULE                          │
└──────────────────────────────────────────────────────────────┘

                      NHAN_SU (Nhân Sự)
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
        ├─ Nhân viên phụ trách KH
        ├─ Quản lý dự án IoT
        ├─ Ghi nhật ký thiết bị
        └─ Tự động tạo thư mục hồ sơ → QLVB
        │
        │ (Giao việc)
        │
        ↓
        
      QLKH (Quản Lý Khách Hàng)
          │
          ├─ Khách hàng
          │   ├─ nhan_vien_phu_trach_id → NHAN_SU
          │   └─ interaction_ids, quotation_ids, contract_ids
          │       (Tính KPI nhân viên)
          │
          ├─ Báo giá
          │   └─ Tạo hợp đồng khi chấp nhận
          │
          ├─ Hợp đồng
          │   ├─ related_contract_id (QLVB)
          │   ├─ Tự động tạo document (hồ sơ) → QLVB
          │   ├─ Tự động scan OCR
          │   └─ Cron job: Kiểm tra hạn → Mail activity
          │
          └─ Lịch hẹn
              ├─ Tự động tạo sau hoàn thành
              └─ Tự động tạo báo giá mới
              │
              │ (Tạo tài liệu liên quan)
              │
              ↓
              
            QLVB (Quản Lý Văn Bản)
                │
                ├─ Thư mục:
                │  ├─ Thư mục Nhân viên (tạo từ NHAN_SU)
                │  ├─ Thư mục Khách hàng
                │  └─ Thư mục Hợp đồng
                │
                ├─ Tài liệu:
                │  ├─ Hồ sơ hợp đồng (từ QLKH)
                │  ├─ Công văn đến/đi
                │  └─ Tài liệu khác
                │
                ├─ Quét OCR
                │  └─ Trích xuất nội dung từ file
                │
                ├─ Quy trình phê duyệt
                │  └─ Giao việc cho nhân viên (NHAN_SU)
                │
                └─ Phiên bản & Lưu trữ
```

---

## 4.2 Các Điểm Tương Tác Chi Tiết

### 4.2.1 Khi Tạo Nhân Viên (NHAN_SU → QLVB)
```
CREATE hr.employee
  ↓
_create_employee_folder()
  ↓
CREATE van_ban.folder:
  - Tạo folder "Nhân viên" (gốc)
  - Tạo folder phòng ban
  - Tạo folder nhân viên
  ↓
nhan_vien.folder_id = folder_id
```

### 4.2.2 Khi Tạo/Cập Nhật Khách Hàng (QLKH)
```
CREATE qlkh.customer
  ├─ nhan_vien_phu_trach_id = NHAN_SU employee
  └─ status = khach_hang_tiem_nang (mặc định)
  
  Nếu status = da_xac_thuc:
    ├─ Tạo qlkh.appointment (Mới)
    └─ Nhân viên được gán công việc chăm sóc

  Nếu status = bao_gia:
    └─ Tạo qlkh.quotation (Nháp) tự động
```

### 4.2.3 Khi Chấp Nhận Báo Giá (QLKH → QLKH)
```
quotation.action_accept_quotation()
  ├─ quotation.status = chap_nhan
  ├─ customer.status = dam_phan
  └─ CREATE qlkh.contract:
      - name = HD-{BaoGiaCode}
      - contract_value = quotation_value
      - status = nhap
```

### 4.2.4 Khi Phê Duyệt Hợp Đồng (QLKH → QLVB)
```
contract.action_approve()
  ├─ contract.status = da_duyet
  └─ CREATE van_ban.document:
      - name = "Hồ sơ hợp đồng {contract.name}"
      - doc_type = hop_dong
      - related_contract_id = contract.id
      - status = draft
      - file = contract.file (nếu có)
      ↓
      Nếu file có:
        └─ Tự động action_scan_ocr()
```

### 4.2.5 Khi Kích Hoạt Hợp Đồng (QLKH)
```
contract.action_activate()
  ├─ contract.status = hieu_luc
  ├─ customer.status = thanh_cong
  └─ mail.activity: Theo dõi hạn hợp đồng
```

### 4.2.6 Khi Hợp Đồng Hết Hạn (QLKH → QLVB)
```
cron_job: check_expiry()
  ├─ Nếu 0 < days_left <= 30:
  │   ├─ contract.status = sap_het_han
  │   └─ Tạo mail.activity cảnh báo
  │
  └─ Nếu days_left <= 0:
      ├─ contract.status = het_han
      └─ cron_archive_expired_contracts():
          └─ document.status = archived (QLVB)
```

### 4.2.7 Khi Lịch Hẹn Hoàn Thành (QLKH)
```
appointment.write(status = hoan_thanh)
  ├─ Tạo follow-up lịch hẹn (1 ngày sau)
  │
  └─ Nếu khách hàng ở trạng thái tiềm năng/xác thực:
      ├─ CREATE qlkh.quotation (Nháp)
      ├─ customer.status = bao_gia
      └─ related_quotation_id = quotation.id
```

### 4.2.8 Khi Tính KPI Nhân Viên (NHAN_SU ← QLKH)
```
nhan_vien._compute_quan_ly_khach_hang()
  │
  ├─ so_khach_hang_phu_trach = 
  │   COUNT(qlkh.customer WHERE nhan_vien_phu_trach_id = id)
  │
  ├─ so_bao_gia = 
  │   COUNT(qlkh.quotation WHERE customer.nhan_vien_phu_trach_id = id)
  │
  ├─ so_hop_dong = 
  │   COUNT(qlkh.contract WHERE customer.nhan_vien_phu_trach_id = id)
  │
  ├─ so_van_ban_xu_ly = 
  │   COUNT(van_ban.document WHERE nhan_vien_id = id OR
  │                                   customer.nhan_vien_phu_trach_id = id)
  │
  ├─ diem_kpi = (so_hop_dong × 10) + (so_bao_gia × 2)
  │
  ├─ muc_tieu_doanh_so = 
  │   (so_hop_dong × 1,000,000) + (so_khach_hang × 500,000)
  │
  └─ tien_do_kpi = (diem_kpi / 100) × 100%
```

### 4.2.9 Công Văn Liên Kết (QLVB)
```
van_ban_den.customer_id = qlkh.customer
  └─ Theo dõi công văn từ khách hàng cụ thể

van_ban_di.customer_id = qlkh.customer
  └─ Theo dõi công văn gửi đến khách hàng

van_ban_routing.assigned_to = nhan_vien
  └─ Giao việc cho nhân viên xử lý (NHAN_SU)
```

---

## 4.3 Bảng Tóm Tắt Luồng Tổng Thể

| Bước | Mô Tả | Module | Trạng Thái |
|------|-------|--------|-----------|
| 1 | Tạo nhân viên | NHAN_SU | - |
| 2 | Tạo thư mục hồ sơ tự động | NHAN_SU → QLVB | draft |
| 3 | Tạo khách hàng, gán NV | QLKH | khach_hang_tiem_nang |
| 4 | Tạo lịch hẹn chăm sóc | QLKH | moi |
| 5 | Hoàn thành lịch hẹn | QLKH | hoan_thanh |
| 6 | Cập nhật KH → Xác thực | QLKH | da_xac_thuc |
| 7 | Tạo báo giá | QLKH | nhap |
| 8 | Gửi báo giá | QLKH | da_gui |
| 9 | Khách hàng chấp nhận | QLKH | chap_nhan |
| 10 | Tạo hợp đồng | QLKH | nhap |
| 11 | Gửi hợp đồng duyệt | QLKH | cho_duyet |
| 12 | Phê duyệt hợp đồng | QLKH | da_duyet |
| 13 | Tạo văn bản hồ sơ | QLKH → QLVB | draft |
| 14 | Quét OCR | QLVB | processing → completed |
| 15 | Phê duyệt văn bản | QLVB | to_approve → approved |
| 16 | Kích hoạt hợp đồng | QLKH | hieu_luc |
| 17 | Cập nhật KH | QLKH | thanh_cong |
| 18 | Cron: Kiểm tra hạn | QLKH | sap_het_han / het_han |
| 19 | Lưu trữ văn bản | QLVB | archived |

---

## 4.4 Mục Đích Liên Kết

### Tại Sao Các Module Phải Tương Tác?

1. **NHAN_SU ← QLKH**:
   - Tính KPI, thống kê hiệu suất nhân viên
   - Quản lý công việc được giao
   - Theo dõi mục tiêu doanh số

2. **QLKH → QLVB**:
   - Lưu trữ tài liệu hợp đồng, báo giá
   - Quét OCR để trích xuất thông tin
   - Lịch sử giao dịch, công văn
   - Phê duyệt tài liệu pháp lý

3. **NHAN_SU → QLVB**:
   - Tổ chức thư mục hồ sơ nhân viên
   - Giao việc phê duyệt văn bản
   - Quản lý quy trình xử lý

---

## 4.5 Dữ Liệu Tính Toán Tự Động

### Nhân Viên (NHAN_SU):
```
tuoi = Năm hiện tại - Năm sinh
so_nguoi_bang_tuoi = COUNT(hr.employee WHERE birthday.year = id.birthday.year)
so_khach_hang_phu_trach = COUNT(qlkh.customer WHERE nhan_vien_phu_trach_id = id)
diem_kpi = (so_hop_dong × 10) + (so_bao_gia × 2)
tien_do_kpi = (diem_kpi / 100) × 100%
```

### Khách Hàng (QLKH):
```
interaction_count = COUNT(qlkh.customer_interaction WHERE customer_id = id)
quotation_count = COUNT(qlkh.quotation WHERE customer_id = id)
contract_count = COUNT(qlkh.contract WHERE customer_id = id)
revenue_total = SUM(qlkh.contract.contract_value WHERE customer_id = id)
customer_score = MIN(
  (interaction_count × 2) + (quotation_count × 5) 
  + (contract_count × 10) + (revenue_total / 10,000,000),
  100
)
```

### Báo Giá (QLKH):
```
quotation_value = SUM(qlkh.quotation_line.price_total WHERE quotation_id = id)
price_total = (quantity × unit_price) + (quantity × unit_price × vat_rate)
```

### Hợp Đồng (QLKH):
```
days_left = date_end - today
nếu days_left <= 0 → het_han
nếu 0 < days_left <= 30 → sap_het_han
nếu days_left > 30 → hieu_luc (không thay đổi)
```

### Văn Bản (QLVB):
```
file_size = LEN(file in bytes)
file_type = file_name.extension
total_pages = COUNT pages trong PDF
complete_name (folder) = parent.complete_name + "/" + name
```

---

## 4.6 Cron Jobs & Automated Tasks

### Trong Module QLKH:

1. **check_expiry()**:
   - Kiểm tra ngày kết thúc hợp đồng
   - Cập nhật trạng thái (sap_het_han, het_han)
   - Tạo mail.activity cảnh báo

2. **cron_archive_expired_contracts()**:
   - Lưu trữ hợp đồng hết hạn
   - Cập nhật trạng thái văn bản liên quan → archived

### Trong Module QLVB:

- **Tự động tạo thư mục** khi nhân viên mới được tạo
- **Tự động quét OCR** khi hợp đồng được phê duyệt
- **Tự động khóa tài liệu** khi phê duyệt hoàn tất

---

# KẾT LUẬN

Ba module này tạo thành một hệ thống hoàn chỉnh:

- **NHAN_SU**: Quản lý nhân lực, KPI, dự án
- **QLKH**: Quản lý chu kỳ khách hàng từ tiềm năng → thành công
- **QLVB**: Lưu trữ, quản lý tài liệu, quy trình phê duyệt

Mỗi trạng thái thay đổi trong một module có thể trigger tự động hành động trong module khác, tạo ra một luồng công việc liên tục, tự động hóa tối đa.

