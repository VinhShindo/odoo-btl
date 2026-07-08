-- =================================================================
-- DỮ LIỆU MẪU CUỐI CÙNG CHO 3 MODULE: nhan_su, quan_ly_khach_hang, quan_ly_van_ban
-- (Đã gộp tất cả UPDATE và INSERT bổ sung, đảm bảo dữ liệu logic và đầy đủ)
-- =================================================================
-- NOTE: Bắt đầu từ ID = 2 để tránh conflict với admin (ID = 1)

BEGIN;

-- =====================================================
-- 0. XÓA SẠCH DỮ LIỆU CŨ (Theo thứ tự Foreign Key)
-- =====================================================
-- Văn bản & Liên quan
DELETE FROM van_ban_approval;
DELETE FROM van_ban_routing;
DELETE FROM van_ban_version;
DELETE FROM van_ban_di;
DELETE FROM van_ban_den;
DELETE FROM ir_attachment WHERE res_model = 'van_ban.document';
DELETE FROM van_ban_document;
DELETE FROM van_ban_folder WHERE id >= 2;

-- Nhân sự & Liên quan
DELETE FROM nhan_su_ho_so_dien_tu;
DELETE FROM danh_sach_chung_chi_bang_cap;
DELETE FROM lich_su_cong_tac;
DELETE FROM iot_project_assignment;
DELETE FROM hr_employee WHERE id >= 2;
DELETE FROM resource_resource WHERE id >= 2;
DELETE FROM chung_chi_bang_cap WHERE id >= 2;

-- Khách hàng (CRM) & Sản phẩm IoT
DELETE FROM qlkh_appointment;
DELETE FROM qlkh_customer_interaction;
DELETE FROM qlkh_contract;
DELETE FROM qlkh_quotation_line;
DELETE FROM qlkh_quotation;
DELETE FROM qlkh_customer;
DELETE FROM qlkh_contract_product WHERE id >= 2;

-- Danh mục
DELETE FROM loai_van_ban WHERE id >= 2;
DELETE FROM don_vi WHERE id >= 2;
DELETE FROM chuc_vu WHERE id >= 2;

-- Reset sequence về 1 để insert bắt đầu từ 2
ALTER SEQUENCE IF EXISTS qlkh_customer_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS qlkh_quotation_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS qlkh_quotation_line_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS qlkh_contract_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS qlkh_contract_product_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS van_ban_document_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS van_ban_folder_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS hr_employee_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS qlkh_appointment_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS van_ban_routing_id_seq RESTART WITH 1;


-- =====================================================
-- 1. DANH MỤC CƠ BẢN (ID từ 2)
-- =====================================================
INSERT INTO don_vi (id, ma_don_vi, ten_don_vi) VALUES
    (2, 'DV-RND', 'Phòng Nghiên cứu & Phát triển (R&D)'),
    (3, 'DV-PMO', 'Phòng Quản lý Dự án (PMO)'),
    (4, 'DV-HCNS', 'Phòng Hành chính Nhân sự'),
    (5, 'DV-OPS', 'Phòng Vận hành IoT'),
    (6, 'DV-QA', 'Phòng Kiểm định Chất lượng'),
    (7, 'DV-SALES', 'Phòng Kinh doanh và Triển khai');

INSERT INTO chuc_vu (id, ma_chuc_vu, ten_chuc_vu) VALUES
    (2, 'CV-IOT', 'Kỹ sư Giải pháp IoT'),
    (3, 'CV-PM', 'Quản lý Dự án (Project Manager)'),
    (4, 'CV-OPER', 'Chuyên viên Vận hành Hệ thống'),
    (5, 'CV-SYS', 'Kỹ sư Hệ thống IoT'),
    (6, 'CV-QA', 'Chuyên viên QA'),
    (7, 'CV-SALES', 'Chuyên viên Kinh doanh Công nghệ');

INSERT INTO loai_van_ban (id, ma_loai_van_ban, ten_loai_van_ban) VALUES
    (2, 'LV-001', 'Công văn'),
    (3, 'LV-002', 'Quyết định'),
    (4, 'LV-003', 'Thông báo'),
    (5, 'LV-004', 'Báo cáo'),
    (6, 'LV-005', 'Hợp đồng'),
    (7, 'LV-006', 'Phụ lục hợp đồng'),
    (8, 'LV-007', 'Biên bản'),
    (9, 'LV-008', 'Giấy mời'),
    (10, 'LV-009', 'Tờ trình');


-- =====================================================
-- 2. SẢN PHẨM/DỊCH VỤ IoT (qlkh.contract_product)
-- =====================================================
INSERT INTO qlkh_contract_product (id, name, code, category, device_type, technical_specs, connectivity, warranty, service_plan, list_price, cost_price, support_info, active) VALUES
    (2, 'Cảm biến nhiệt độ IoT', 'IOT-SENS-TEMP-001', 'Cảm biến', 'device', 'Dải đo -40°C đến 125°C, độ chính xác ±0.5°C', 'Wi-Fi 2.4GHz, Bluetooth 5.0', '12 tháng', 'Gói Standard', 2500000, 1500000, 'Hỗ trợ 24/7 qua hotline', true),
    (3, 'Cảm biến độ ẩm đất', 'IOT-SENS-HUM-002', 'Cảm biến', 'device', 'Đo độ ẩm 0-100%, sai số ±3%', 'LoRaWAN, Zigbee', '24 tháng', 'Gói Pro', 3800000, 2200000, 'Hỗ trợ tại hiện trường', true),
    (4, 'Gateway IoT 4G/LTE', 'IOT-GW-4G-01', 'Gateway', 'device', 'CPU Cortex-A7, 512MB RAM, 8GB eMMC', '4G/LTE, Ethernet, Wi-Fi', '36 tháng', 'Gói Enterprise', 12500000, 8500000, 'Hỗ trợ doanh nghiệp', true),
    (5, 'Hệ thống giám sát năng lượng', 'IOT-ENERGY-MON-01', 'Hệ thống', 'bundle', 'Giám sát điện năng theo thời gian thực, tích hợp 8 kênh', 'Modbus RS485, Ethernet', '24 tháng', 'Gói Standard', 45000000, 28000000, 'Có đội ngũ hỗ trợ riêng', true),
    (6, 'Dịch vụ Cloud lưu trữ dữ liệu', 'IOT-CLOUD-BASIC', 'Dịch vụ', 'service', 'Lưu trữ dữ liệu cảm biến lên đến 5 năm, truy xuất API', 'RESTful API, MQTT', 'Không áp dụng', 'Gói Basic', 5000000, 2000000, 'Hỗ trợ online', true),
    (7, 'Phần mềm quản lý bảo trì IoT', 'IOT-SOFT-MAINT', 'Phần mềm', 'service', 'Quản lý lịch bảo trì, cảnh báo sự cố tự động', 'WebSocket, OPC UA', '12 tháng', 'Gói Pro', 15000000, 8000000, 'Có training 1 ngày', true),
    (8, 'Module cảm biến ánh sáng', 'IOT-SENS-LUX-003', 'Cảm biến', 'device', 'Dải đo 0-20000 lux, chống nước IP65', 'LoRaWAN, BLE', '18 tháng', 'Gói Standard', 1800000, 950000, 'Hỗ trợ 8h-17h', true),
    (9, 'Cảm biến chất lượng không khí', 'IOT-SENS-AIR-004', 'Cảm biến', 'device', 'Cảm biến CO2, VOC, PM2.5', 'Zigbee, Thread', '24 tháng', 'Gói Standard', 4200000, 2600000, 'Hỗ trợ 24/7', true),
    (10, 'Smart Switch điều khiển thiết bị', 'IOT-CTRL-SW-01', 'Bộ điều khiển', 'device', '8 kênh relay, có timer, hỗ trợ voice control', 'Wi-Fi, Z-Wave', '12 tháng', 'Gói Basic', 5500000, 3200000, 'Hỗ trợ online', true),
    (11, 'Gói bảo trì hàng năm IoT', 'IOT-SRV-MAINT-YEAR', 'Dịch vụ', 'service', 'Bảo trì định kỳ 4 lần/năm, sửa chữa thiết bị lỗi', 'Tại hiện trường', '1 năm', 'Gói Pro', 12000000, 6000000, 'Hỗ trợ khẩn cấp 24/7', true);


-- =====================================================
-- 3. THƯ MỤC HỒ SƠ (Văn bản)
-- =====================================================
INSERT INTO van_ban_folder (id, name, parent_id, folder_type) VALUES
    (2, 'Nhân viên', NULL, 'employee'),
    (3, 'Phòng Nghiên cứu & Phát triển (R&D)', 2, 'employee'),
    (4, 'Phòng Quản lý Dự án (PMO)', 2, 'employee'),
    (5, 'Phòng Hành chính Nhân sự', 2, 'employee'),
    (6, 'Phòng Vận hành IoT', 2, 'employee'),
    (7, 'Phòng Kiểm định Chất lượng', 2, 'employee'),
    (8, 'Phòng Kinh doanh và Triển khai', 2, 'employee'),
    (42, 'Hợp đồng & Báo giá', NULL, 'general'),
    (43, 'Hồ sơ pháp lý', NULL, 'general'),
    (44, 'Thông tin khách hàng', NULL, 'general');

-- Folder cho từng nhân viên (Tạo thủ công để tránh lỗi PL/pgSQL)
INSERT INTO van_ban_folder (id, name, parent_id, folder_type) VALUES
    (102, 'NV001 - Nhân viên 1', 3, 'employee'), (103, 'NV002 - Nhân viên 2', 3, 'employee'), (104, 'NV003 - Nhân viên 3', 3, 'employee'), (105, 'NV004 - Nhân viên 4', 3, 'employee'), (106, 'NV005 - Nhân viên 5', 3, 'employee'),
    (107, 'NV006 - Nhân viên 6', 4, 'employee'), (108, 'NV007 - Nhân viên 7', 4, 'employee'), (109, 'NV008 - Nhân viên 8', 4, 'employee'), (110, 'NV009 - Nhân viên 9', 4, 'employee'),
    (111, 'NV010 - Nhân viên 10', 5, 'employee'), (112, 'NV011 - Nhân viên 11', 5, 'employee'), (113, 'NV012 - Nhân viên 12', 5, 'employee'), (114, 'NV013 - Nhân viên 13', 5, 'employee'),
    (115, 'NV014 - Nhân viên 14', 6, 'employee'), (116, 'NV015 - Nhân viên 15', 6, 'employee'), (117, 'NV016 - Nhân viên 16', 6, 'employee'), (118, 'NV017 - Nhân viên 17', 6, 'employee'),
    (119, 'NV018 - Nhân viên 18', 7, 'employee'), (120, 'NV019 - Nhân viên 19', 7, 'employee'), (121, 'NV020 - Nhân viên 20', 7, 'employee'), (122, 'NV021 - Nhân viên 21', 7, 'employee'),
    (123, 'NV022 - Nhân viên 22', 8, 'employee'), (124, 'NV023 - Nhân viên 23', 8, 'employee'), (125, 'NV024 - Nhân viên 24', 8, 'employee'), (126, 'NV025 - Nhân viên 25', 8, 'employee'),
    (127, 'NV026 - Nhân viên 26', 8, 'employee'), (128, 'NV027 - Nhân viên 27', 8, 'employee'), (129, 'NV028 - Nhân viên 28', 8, 'employee'), (130, 'NV029 - Nhân viên 29', 8, 'employee'),
    (131, 'NV030 - Nhân viên 30', 8, 'employee');


-- =====================================================
-- 4. RESOURCE RESOURCE (Bắt buộc để tạo Employee)
-- =====================================================
INSERT INTO resource_resource (id, name, resource_type, time_efficiency, calendar_id, tz, active, company_id)
SELECT id, CONCAT('Nhân viên ', id), 'user', 100.0, 1, 'Asia/Ho_Chi_Minh', true, 1
FROM generate_series(2, 31) as id;


-- =====================================================
-- 5. NHÂN VIÊN (30 nhân viên, ID từ 2-31)
-- =====================================================
INSERT INTO hr_employee (id, company_id, name, ho_ten_dem, ten, ho_va_ten, ma_dinh_danh, birthday, tuoi, que_quan, work_email, don_vi_id, chuc_vu_id, folder_id, resource_id, active, employee_type) VALUES
    (2, 1, 'Nguyễn Văn An', 'Nguyễn Văn', 'An', 'Nguyễn Văn An', 'NV26001', '1990-05-15', 36, 'Hà Nội', 'an.nv@iotco.com', 2, 2, 102, 2, true, 'employee'),
    (3, 1, 'Lê Hoàng Cường', 'Lê Hoàng', 'Cường', 'Lê Hoàng Cường', 'NV26003', '1991-03-10', 35, 'Đà Nẵng', 'cuong.lh@iotco.com', 2, 2, 103, 3, true, 'employee'),
    (4, 1, 'Lý Văn Phúc', 'Lý Văn', 'Phúc', 'Lý Văn Phúc', 'NV26013', '1991-11-23', 35, 'Lào Cai', 'phuc.lv@iotco.com', 2, 2, 104, 4, true, 'employee'),
    (5, 1, 'Lương Thị Yến', 'Lương Thị', 'Yến', 'Lương Thị Yến', 'NV26020', '1992-10-05', 34, 'Huế', 'yen.lt@iotco.com', 2, 2, 105, 5, true, 'employee'),
    (6, 1, 'Lữ Văn Khải', 'Lữ Văn', 'Khải', 'Lữ Văn Khải', 'NV26027', '1993-06-06', 33, 'Cần Thơ', 'khai.lv@iotco.com', 2, 2, 106, 6, true, 'employee'),
    (7, 1, 'Trần Thị Bình', 'Trần Thị', 'Bình', 'Trần Thị Bình', 'NV26002', '1992-08-22', 34, 'Hải Phòng', 'binh.tt@iotco.com', 3, 3, 107, 7, true, 'employee'),
    (8, 1, 'Hoàng Quốc Em', 'Hoàng Quốc', 'Em', 'Hoàng Quốc Em', 'NV26005', '1990-01-20', 36, 'Hà Nội', 'em.hq@iotco.com', 3, 3, 108, 8, true, 'employee'),
    (9, 1, 'Khổng Văn Út', 'Khổng Văn', 'Út', 'Khổng Văn Út', 'NV26017', '1994-12-11', 32, 'Hà Tĩnh', 'ut.kv@iotco.com', 3, 3, 109, 9, true, 'employee'),
    (10, 1, 'Vũ Văn Mạnh', 'Vũ Văn', 'Mạnh', 'Vũ Văn Mạnh', 'NV26011', '1993-06-12', 33, 'Hưng Yên', 'manh.vv@iotco.com', 4, 4, 110, 10, true, 'employee'),
    (11, 1, 'Trương Thị Quỳnh', 'Trương Thị', 'Quỳnh', 'Trương Thị Quỳnh', 'NV26014', '1995-02-14', 31, 'Quảng Ninh', 'quynh.tt@iotco.com', 4, 4, 111, 11, true, 'employee'),
    (12, 1, 'Mạc Văn Bảo', 'Mạc Văn', 'Bảo', 'Mạc Văn Bảo', 'NV26021', '1993-03-16', 33, 'Đà Nẵng', 'bao.mv@iotco.com', 4, 4, 112, 12, true, 'employee'),
    (13, 1, 'Vương Thị Lan', 'Vương Thị', 'Lan', 'Vương Thị Lan', 'NV26028', '1994-10-30', 32, 'An Giang', 'lan.vt@iotco.com', 4, 4, 113, 13, true, 'employee'),
    (14, 1, 'Phạm Minh Đức', 'Phạm Minh', 'Đức', 'Phạm Minh Đức', 'NV26004', '1993-11-04', 33, 'Cần Thơ', 'duc.pm@iotco.com', 5, 5, 114, 14, true, 'employee'),
    (15, 1, 'Lê Thị Khánh', 'Lê Thị', 'Khánh', 'Lê Thị Khánh', 'NV26010', '1990-10-30', 36, 'Hà Nội', 'khanh.lt@iotco.com', 5, 5, 115, 15, true, 'employee'),
    (16, 1, 'Đinh Thị Vui', 'Đinh Thị', 'Vui', 'Đinh Thị Vui', 'NV26018', '1995-05-08', 31, 'Quảng Bình', 'vui.dt@iotco.com', 5, 5, 116, 16, true, 'employee'),
    (17, 1, 'Sử Văn Giang', 'Sử Văn', 'Giang', 'Sử Văn Giang', 'NV26025', '1990-09-14', 36, 'Bà Rịa', 'giang.sv@iotco.com', 5, 5, 117, 17, true, 'employee'),
    (18, 1, 'Đỗ Tuấn Phong', 'Đỗ Tuấn', 'Phong', 'Đỗ Tuấn Phong', 'NV26006', '1994-07-17', 32, 'Hải Dương', 'phong.dt@iotco.com', 6, 6, 118, 18, true, 'employee'),
    (19, 1, 'Đặng Thị Ngọc', 'Đặng Thị', 'Ngọc', 'Đặng Thị Ngọc', 'NV26012', '1994-08-19', 32, 'Thái Bình', 'ngoc.dt@iotco.com', 6, 6, 119, 19, true, 'employee'),
    (20, 1, 'Chu Văn Xuyên', 'Chu Văn', 'Xuyên', 'Chu Văn Xuyên', 'NV26019', '1990-07-19', 36, 'Quảng Trị', 'xuyen.cv@iotco.com', 6, 6, 120, 20, true, 'employee'),
    (21, 1, 'Tăng Thị Hoa', 'Tăng Thị', 'Hoa', 'Tăng Thị Hoa', 'NV26026', '1992-11-22', 34, 'TP.HCM', 'hoa.tt@iotco.com', 6, 6, 121, 21, true, 'employee'),
    (22, 1, 'Bùi Tuyết Giang', 'Bùi Tuyết', 'Giang', 'Bùi Tuyết Giang', 'NV26007', '1995-12-25', 31, 'Nam Định', 'giang.bt@iotco.com', 7, 7, 122, 22, true, 'employee'),
    (23, 1, 'Nguyễn Thu Hà', 'Nguyễn Thu', 'Hà', 'Nguyễn Thu Hà', 'NV26008', '1992-02-28', 34, 'Hà Nam', 'ha.nt@iotco.com', 7, 7, 123, 23, true, 'employee'),
    (24, 1, 'Trần Văn Hùng', 'Trần Văn', 'Hùng', 'Trần Văn Hùng', 'NV26009', '1991-09-09', 35, 'Bắc Ninh', 'hung.tv@iotco.com', 7, 7, 124, 24, true, 'employee'),
    (25, 1, 'Phan Văn Sơn', 'Phan Văn', 'Sơn', 'Phan Văn Sơn', 'NV26015', '1992-04-27', 34, 'Thanh Hóa', 'son.pv@iotco.com', 7, 7, 125, 25, true, 'employee'),
    (26, 1, 'Hồ Thị Tuyết', 'Hồ Thị', 'Tuyết', 'Hồ Thị Tuyết', 'NV26016', '1993-09-03', 33, 'Nghệ An', 'tuyet.ht@iotco.com', 7, 7, 126, 26, true, 'employee'),
    (27, 1, 'Ninh Thị Cúc', 'Ninh Thị', 'Cúc', 'Ninh Thị Cúc', 'NV26022', '1994-08-25', 32, 'Khánh Hòa', 'cuc.nt@iotco.com', 7, 7, 127, 27, true, 'employee'),
    (28, 1, 'Phùng Văn Đức', 'Phùng Văn', 'Đức', 'Phùng Văn Đức', 'NV26023', '1991-12-01', 35, 'Lâm Đồng', 'duc.pv@iotco.com', 7, 7, 128, 28, true, 'employee'),
    (29, 1, 'Quách Thị Em', 'Quách Thị', 'Em', 'Quách Thị Em', 'NV26024', '1995-04-28', 31, 'Bình Thuận', 'em.qt@iotco.com', 7, 7, 129, 29, true, 'employee'),
    (30, 1, 'Hứa Văn Minh', 'Hứa Văn', 'Minh', 'Hứa Văn Minh', 'NV26029', '1991-07-21', 35, 'Đồng Tháp', 'minh.hv@iotco.com', 7, 7, 130, 30, true, 'employee'),
    (31, 1, 'Trịnh Thị Ngân', 'Trịnh Thị', 'Ngân', 'Trịnh Thị Ngân', 'NV26030', '1995-01-17', 31, 'Vĩnh Long', 'ngan.tt@iotco.com', 7, 7, 131, 31, true, 'employee');


-- =====================================================
-- 6. LỊCH SỬ CÔNG TÁC & CHỨNG CHỈ
-- =====================================================
INSERT INTO lich_su_cong_tac (nhan_vien_id, chuc_vu_id, don_vi_id, loai_chuc_vu)
SELECT id, 
    CASE WHEN id <= 6 THEN 2 WHEN id <= 9 THEN 3 WHEN id <= 13 THEN 4 WHEN id <= 17 THEN 5 WHEN id <= 21 THEN 6 ELSE 7 END,
    CASE WHEN id <= 6 THEN 2 WHEN id <= 9 THEN 3 WHEN id <= 13 THEN 4 WHEN id <= 17 THEN 5 WHEN id <= 21 THEN 6 ELSE 7 END,
    'Chính'
FROM generate_series(2, 31) as id;

INSERT INTO chung_chi_bang_cap (id, ma_chung_chi_bang_cap, ten_chung_chi_bang_cap) VALUES
    (2, 'CERT-AWS', 'AWS Certified Solutions Architect'),
    (3, 'CERT-PMP', 'Project Management Professional (PMP)'),
    (4, 'CERT-IOT', 'Chứng chỉ Chuyên gia IoT'),
    (5, 'CERT-SALE', 'Chứng chỉ Kỹ năng Bán hàng Chuyên nghiệp');

INSERT INTO danh_sach_chung_chi_bang_cap (nhan_vien_id, chung_chi_bang_cap_id, ghi_chu)
SELECT nhan_vien_id, (nhan_vien_id % 4) + 2, 'Chứng chỉ chuyên môn' 
FROM generate_series(2, 31) as nhan_vien_id;


-- =====================================================
-- 7. DỰ ÁN IoT (Sửa lỗi: bỏ project_id, gộp vào name)
-- =====================================================
INSERT INTO iot_project_assignment (id, name, description, nhan_vien_id, role, date_start, date_end, note)
SELECT id,
    CONCAT('Dự án IoT - Smart ', CASE (id % 4) WHEN 0 THEN 'Factory' WHEN 1 THEN 'Building' ELSE 'City' END, ' #', id),
    'Triển khai giải pháp IoT cho doanh nghiệp',
    (id % 30) + 2,
    CASE (id % 4) WHEN 0 THEN 'Lead Engineer' ELSE 'IoT Developer' END,
    CURRENT_DATE - ((id % 12) || ' months')::interval,
    CURRENT_DATE + ((12 - (id % 12)) || ' months')::interval,
    'Ghi chú dự án mẫu'
FROM generate_series(2, 76) as id;


-- =====================================================
-- 8. KHÁCH HÀNG (Mỗi nhân viên phụ trách 15-20 KH)
-- Tên công ty được cải tiến đa dạng hơn để thực tế
-- =====================================================
DO $$
DECLARE
    i INT;
    v_nhan_vien_id INT;
    v_customer_start INT := 2;
    v_count INT;
    v_company_suffix TEXT[];
    v_company_name TEXT;
BEGIN
    -- Danh sách tên công ty mẫu
    v_company_suffix := ARRAY[
        'Công ty TNHH Công nghệ', 'Công ty CP Dịch vụ', 'Công ty TNHH Sản xuất', 
        'Công ty CP Thương mại', 'Công ty TNHH Đầu tư', 'Công ty CP Xây dựng',
        'Công ty TNHH Giải pháp', 'Công ty CP Vận tải', 'Công ty TNHH Kỹ thuật',
        'Công ty CP Năng lượng'
    ];
    
    FOR v_nhan_vien_id IN 2..31 LOOP
        v_count := 15 + (v_nhan_vien_id % 6);
        FOR i IN 1..v_count LOOP
            -- Tạo tên công ty ngẫu nhiên từ danh sách trên
            v_company_name := v_company_suffix[1 + (v_customer_start % array_length(v_company_suffix, 1))] || ' ' || v_customer_start;
            
            INSERT INTO qlkh_customer (id, name, code, customer_type, status, nhan_vien_phu_trach_id, iot_device, email, phone, address, note) 
            VALUES (
                v_customer_start,
                v_company_name,
                CONCAT('KH', LPAD(v_customer_start::text, 4, '0')),
                CASE WHEN (v_customer_start % 5) = 4 THEN 'ca_nhan' ELSE 'doanh_nghiep' END,
                CASE (v_customer_start % 5) 
                    WHEN 0 THEN 'tiem_nang' WHEN 1 THEN 'da_xac_thuc' WHEN 2 THEN 'da_gui_bao_gia' WHEN 3 THEN 'dam_phan' ELSE 'thanh_cong' 
                END,
                v_nhan_vien_id,
                CONCAT('Device_', v_customer_start),
                CONCAT('contact', v_customer_start, '@gmail.com'),
                CONCAT('090', LPAD(v_customer_start::text, 7, '0')),
                CASE (v_customer_start % 5) WHEN 0 THEN 'Hà Nội' WHEN 1 THEN 'Hồ Chí Minh' WHEN 2 THEN 'Đà Nẵng' WHEN 3 THEN 'Cần Thơ' ELSE 'Hải Phòng' END,
                'Khách hàng mẫu demo'
            );
            v_customer_start := v_customer_start + 1;
        END LOOP;
    END LOOP;
END $$;


-- =====================================================
-- 9. BÁO GIÁ
-- =====================================================
INSERT INTO qlkh_quotation (id, name, customer_id, date, status, note)
SELECT 
    id,
    CONCAT('BQ-', LPAD(id::text, 4, '0'), '-', (SELECT code FROM qlkh_customer WHERE id = (id % 525) + 2), '-', TO_CHAR(CURRENT_DATE - ((id % 30) || ' days')::interval, 'YYYYMMDD')),
    (id % 525) + 2,
    CURRENT_DATE - ((id % 30) || ' days')::interval,
    CASE (id % 4) WHEN 0 THEN 'chap_nhan' WHEN 1 THEN 'dam_phan' ELSE 'da_gui' END,
    'Báo giá demo'
FROM generate_series(2, 400) as id;

-- =====================================================
-- 10. CHI TIẾT BÁO GIÁ & TÍNH TOÁN LẠI GIÁ TRỊ
-- =====================================================
DO $$
DECLARE
    v_quotation_id INT;
    v_product_id INT;
    v_price_total NUMERIC;
    v_price_subtotal NUMERIC;
    v_price_tax NUMERIC;
BEGIN
    FOR v_quotation_id IN 2..400 LOOP
        FOR i IN 1..3 LOOP
            -- Lấy ngẫu nhiên 1 trong 10 sản phẩm đã tạo ở bước 2
            v_product_id := 2 + ( (v_quotation_id + i) % 10 );
            
            -- Tính toán giá trị ngay trong lúc INSERT
            v_price_subtotal := ((i % 5) + 1) * (SELECT list_price * 1.1 FROM qlkh_contract_product WHERE id = v_product_id);
            v_price_tax := v_price_subtotal * 0.1;
            v_price_total := v_price_subtotal + v_price_tax;
            
            INSERT INTO qlkh_quotation_line (quotation_id, product_id, product_name, description, quantity, unit_price, vat_rate, price_subtotal, price_tax, price_total)
            SELECT 
                v_quotation_id, 
                v_product_id,
                name,
                technical_specs,
                (i % 5) + 1, 
                list_price * 1.1, 
                10,
                v_price_subtotal,
                v_price_tax,
                v_price_total
            FROM qlkh_contract_product WHERE id = v_product_id;
        END LOOP;
    END LOOP;
END $$;

-- Cập nhật lại giá trị báo giá dựa trên line
UPDATE qlkh_quotation q
SET quotation_value = (SELECT COALESCE(SUM(price_total), 0) FROM qlkh_quotation_line WHERE quotation_id = q.id);


-- =====================================================
-- 11. HỢP ĐỒNG (Chỉ tạo từ báo giá trạng thái 'chap_nhan')
-- =====================================================
INSERT INTO qlkh_contract (id, name, customer_id, date_start, date_end, contract_value, status, iot_device, note, quotation_id)
SELECT 
    id,
    CONCAT('HD-', (SELECT code FROM qlkh_customer WHERE id = q.customer_id), '-', TO_CHAR(q.date, 'YYYYMMDD')),
    q.customer_id,
    q.date,
    q.date + INTERVAL '1 year',
    q.quotation_value + 1000000,
    'hieu_luc',
    (SELECT iot_device FROM qlkh_customer WHERE id = q.customer_id),
    CONCAT('Hợp đồng từ báo giá ', q.name),
    q.id
FROM qlkh_quotation q
WHERE q.status = 'chap_nhan'
LIMIT 100;


-- =====================================================
-- 12. TƯƠNG TÁC KHÁCH HÀNG
-- =====================================================
INSERT INTO qlkh_customer_interaction (id, customer_id, date, type, status, content, nhan_vien_id)
SELECT id, (id % 525) + 2, now() - ((id % 60) || ' days')::interval, 
    CASE (id % 4) WHEN 0 THEN 'gap_mat' WHEN 1 THEN 'goi_dien' ELSE 'email' END,
    'da_thuc_hien', CONCAT('Cuộc gọi chăm sóc KH số ', id),
    (id % 30) + 2
FROM generate_series(2, 2000) as id;


-- =====================================================
-- 13. VĂN BẢN DOCUMENT (Liên kết với hợp đồng và báo giá)
-- =====================================================
INSERT INTO van_ban_document (id, name, code, doc_type, loai_van_ban_id, customer_id, nhan_vien_id, folder_id, related_contract_id, related_quotation_id, status, date, source_module)
SELECT 
    id,
    CONCAT('VB_', id, '_', CASE (id % 5) WHEN 0 THEN 'Hop_Dong' WHEN 1 THEN 'Bao_Gia' ELSE 'Cong_Van' END),
    CONCAT('DOC-', LPAD(id::text, 5, '0')),
    CASE (id % 4) WHEN 0 THEN 'hop_dong' ELSE 'bao_gia' END,
    (id % 9) + 2,
    (id % 525) + 2, (id % 30) + 2, 42,
    NULL, NULL,
    CASE (id % 3) WHEN 0 THEN 'approved' ELSE 'draft' END,
    CURRENT_DATE - ((id % 30) || ' days')::interval,
    'crm'
FROM generate_series(2, 500) as id;

-- Liên kết 50 văn bản với hợp đồng đã ký
UPDATE van_ban_document SET related_contract_id = (SELECT id FROM qlkh_contract ORDER BY RANDOM() LIMIT 1) WHERE id BETWEEN 2 AND 51;


-- =====================================================
-- 14. VĂN BẢN ĐẾN & ĐI (Liên kết Document)
-- =====================================================
INSERT INTO van_ban_den (document_id, so_van_ban_den, ten_van_ban, so_hieu_van_ban, ngay_den, customer_id, nhan_vien_nhan_id, trang_thai)
SELECT id, CONCAT('VBDen-', id), name, CONCAT('Số: ', id, '/CV'), date, customer_id, nhan_vien_id, 'moi'
FROM van_ban_document WHERE id BETWEEN 2 AND 100;

INSERT INTO van_ban_di (document_id, so_van_ban_di, ten_van_ban, so_hieu_van_ban, ngay_di, customer_id, nhan_vien_tao_id, trang_thai)
SELECT id + 200, CONCAT('VBDi-', id + 200), name, CONCAT('Số: ', id + 200, '/CV'), date, customer_id, nhan_vien_id, 'draft'
FROM van_ban_document WHERE id BETWEEN 2 AND 100;


-- =====================================================
-- 15. LỊCH HẸN (qlkh_appointment)
-- =====================================================
INSERT INTO qlkh_appointment (id, name, customer_id, nhan_vien_id, appointment_date, status, note)
SELECT 
    ROW_NUMBER() OVER (ORDER BY c.id) + 2 AS id,
    CONCAT('Hẹn làm việc với ', c.name) AS name,
    c.id AS customer_id,
    c.nhan_vien_phu_trach_id AS nhan_vien_id,
    (NOW() + ((ROW_NUMBER() OVER (ORDER BY c.id) % 30) || ' days')::interval + ((ROW_NUMBER() OVER (ORDER BY c.id) % 24) || ' hours')::interval) AS appointment_date,
    CASE (ROW_NUMBER() OVER (ORDER BY c.id) % 4)
        WHEN 0 THEN 'da_xac_nhan'
        WHEN 1 THEN 'hoan_thanh'
        ELSE 'moi'
    END AS status,
    CONCAT('Cuộc hẹn số ', ROW_NUMBER() OVER (ORDER BY c.id)) AS note
FROM qlkh_customer c
WHERE c.id >= 2
LIMIT 500;


-- =====================================================
-- 16. QUY TRÌNH XỬ LÝ VĂN BẢN (van_ban_routing)
-- =====================================================
INSERT INTO van_ban_routing (name, document_id, assigned_to, stage, date_deadline, note)
SELECT 
    CONCAT('Xử lý VB: ', d.code) AS name,
    d.id AS document_id,
    (d.id % 30) + 2 AS assigned_to,
    CASE (d.id % 4) 
        WHEN 0 THEN 'to_process'
        WHEN 1 THEN 'in_progress'
        WHEN 2 THEN 'done'
        ELSE 'rejected'
    END AS stage,
    d.date + ((d.id % 14) || ' days')::interval AS date_deadline,
    CONCAT('Quy trình xử lý tự động cho văn bản ', d.code) AS note
FROM van_ban_document d
WHERE d.id BETWEEN 2 AND 100;


-- =====================================================
-- 17. CẬP NHẬT DỮ LIỆU CÒN THIẾU CHO KHÁCH HÀNG (Doanh thu kỳ vọng, Khu vực, Ngành nghề, Độ ưu tiên)
-- =====================================================
-- Doanh thu kỳ vọng
UPDATE qlkh_customer 
SET expected_revenue = 
    CASE 
        WHEN status IN ('thanh_cong', 'dam_phan') THEN floor(random() * 500000000 + 100000000)::int
        WHEN status IN ('da_gui_bao_gia', 'sap_ky_hd') THEN floor(random() * 200000000 + 50000000)::int
        ELSE floor(random() * 50000000 + 10000000)::int
    END
WHERE expected_revenue IS NULL;

-- Khu vực
UPDATE qlkh_customer 
SET area = CASE (id % 5)
    WHEN 0 THEN 'Miền Bắc'
    WHEN 1 THEN 'Miền Trung'
    WHEN 2 THEN 'Miền Nam'
    WHEN 3 THEN 'Tây Nguyên'
    ELSE 'Hải Đảo'
END
WHERE area IS NULL;

-- Ngành nghề
UPDATE qlkh_customer 
SET industry = CASE (id % 6)
    WHEN 0 THEN 'Công nghệ thông tin'
    WHEN 1 THEN 'Sản xuất công nghiệp'
    WHEN 2 THEN 'Nông nghiệp công nghệ cao'
    WHEN 3 THEN 'Dịch vụ logistics'
    WHEN 4 THEN 'Bán lẻ & Thương mại'
    ELSE 'Giáo dục & Đào tạo'
END
WHERE industry IS NULL;

-- Độ ưu tiên
UPDATE qlkh_customer 
SET priority = 
    CASE 
        WHEN expected_revenue >= 200000000 OR status IN ('thanh_cong', 'sap_ky_hd') THEN 'high'
        WHEN expected_revenue >= 50000000 OR status IN ('dam_phan', 'da_gui_bao_gia') THEN 'medium'
        ELSE 'low'
    END
WHERE priority IS NULL;


-- =====================================================
-- 18. CẬP NHẬT DỮ LIỆU VĂN BẢN (OCR, file_type, AI summary, date_upload, status…)
-- =====================================================
-- Cập nhật Ngày upload (date_upload)
UPDATE van_ban_document 
SET date_upload = date 
WHERE date_upload IS NULL;

-- Cập nhật Loại file (file_type) từ file_name
UPDATE van_ban_document SET file_type = 'pdf' WHERE file_name LIKE '%.pdf' AND file_type IS NULL;
UPDATE van_ban_document SET file_type = 'docx' WHERE file_name LIKE '%.docx' AND file_type IS NULL;
UPDATE van_ban_document SET file_type = 'khac' WHERE file_name IS NOT NULL AND file_type IS NULL;

-- Cập nhật Số trang (total_pages) cho PDF
UPDATE van_ban_document SET total_pages = 1 WHERE file_type = 'pdf' AND total_pages IS NULL;

-- Cập nhật Trạng thái văn bản để hiển thị trên Dashboard
UPDATE van_ban_document SET status = 'approved' WHERE id BETWEEN 2 AND 125;
UPDATE van_ban_document SET status = 'to_approve' WHERE id BETWEEN 126 AND 250;
UPDATE van_ban_document SET status = 'draft' WHERE id BETWEEN 251 AND 375;
UPDATE van_ban_document SET status = 'archived' WHERE id BETWEEN 376 AND 500;

-- Cập nhật Trạng thái OCR và AI summary
UPDATE van_ban_document SET ocr_status = 'completed', ocr_date = NOW(), file_size = 1024 WHERE id BETWEEN 2 AND 51;
UPDATE van_ban_document SET ocr_status = 'processing', ocr_date = NOW(), file_size = 1024 WHERE id BETWEEN 52 AND 101;
UPDATE van_ban_document SET ocr_status = 'not_started', ocr_date = NULL, file_size = 0 WHERE id >= 102;
UPDATE van_ban_document SET ai_summary = 'Tóm tắt tự động từ AI' WHERE id BETWEEN 2 AND 51;


-- =====================================================
-- 19. CẬP NHẬT DỮ LIỆU CÒN THIẾU CHO VĂN BẢN ĐẾN & ĐI
-- =====================================================
-- Văn bản đến
UPDATE van_ban_den SET ngay_ban_hanh = ngay_den - ((id % 5) || ' days')::interval WHERE ngay_ban_hanh IS NULL;
UPDATE van_ban_den SET loai_van_ban_id = 2 + (id % 9) WHERE loai_van_ban_id IS NULL;
UPDATE van_ban_den d SET noi_gui_den = c.name FROM qlkh_customer c WHERE d.customer_id = c.id AND d.noi_gui_den IS NULL;
UPDATE van_ban_den d SET nguoi_ky = e.name FROM qlkh_customer c JOIN hr_employee e ON e.id = c.nhan_vien_phu_trach_id WHERE d.customer_id = c.id AND d.nguoi_ky IS NULL;
UPDATE van_ban_den SET nhan_vien_chuyen_id = 2 + ((id + 3) % 30) WHERE nhan_vien_chuyen_id IS NULL;
UPDATE van_ban_den SET trich_yeu = 'Trích yếu nội dung của văn bản: ' || ten_van_ban WHERE trich_yeu IS NULL;
UPDATE van_ban_den SET ghi_chu = 'Ghi chú bổ sung cho văn bản đến này.' WHERE ghi_chu IS NULL;

-- Văn bản đi
UPDATE van_ban_di SET ngay_ban_hanh = ngay_di - ((id % 4) || ' days')::interval WHERE ngay_ban_hanh IS NULL;
UPDATE van_ban_di SET loai_van_ban_id = 2 + (id % 9) WHERE loai_van_ban_id IS NULL;
UPDATE van_ban_di d SET noi_nhan = c.name FROM qlkh_customer c WHERE d.customer_id = c.id AND d.noi_nhan IS NULL;
UPDATE van_ban_di d SET nguoi_ky = e.name FROM hr_employee e WHERE d.nhan_vien_tao_id = e.id AND d.nguoi_ky IS NULL;
UPDATE van_ban_di SET nhan_vien_ky_id = 2 + ((id + 5) % 30) WHERE nhan_vien_ky_id IS NULL;
UPDATE van_ban_di SET trich_yeu = 'Trích yếu nội dung văn bản đi: ' || ten_van_ban WHERE trich_yeu IS NULL;
UPDATE van_ban_di SET ghi_chu = 'Ghi chú bổ sung cho văn bản đi này.' WHERE ghi_chu IS NULL;


-- =====================================================
-- 20. CẬP NHẬT SEQUENCE CHO CÁC BẢNG
-- =====================================================
SELECT setval('qlkh_customer_id_seq', (SELECT MAX(id) FROM qlkh_customer));
SELECT setval('qlkh_quotation_id_seq', (SELECT MAX(id) FROM qlkh_quotation));
SELECT setval('qlkh_contract_id_seq', (SELECT MAX(id) FROM qlkh_contract));
SELECT setval('qlkh_customer_interaction_id_seq', (SELECT MAX(id) FROM qlkh_customer_interaction));
SELECT setval('van_ban_document_id_seq', (SELECT MAX(id) FROM van_ban_document));
SELECT setval('hr_employee_id_seq', (SELECT MAX(id) FROM hr_employee));
SELECT setval('van_ban_folder_id_seq', (SELECT MAX(id) FROM van_ban_folder));
SELECT setval('qlkh_contract_product_id_seq', (SELECT MAX(id) FROM qlkh_contract_product));
SELECT setval('qlkh_appointment_id_seq', (SELECT MAX(id) FROM qlkh_appointment));
SELECT setval('van_ban_routing_id_seq', (SELECT MAX(id) FROM van_ban_routing));


-- =====================================================
-- 21. BẢNG THỐNG KÊ DỮ LIỆU SAU KHI CHẠY
-- =====================================================
DO $$
DECLARE
    row_count RECORD;
    total_contracts INT;
    total_customers INT;
    total_emp INT;
    total_prods INT;
BEGIN
    SELECT COUNT(*) INTO total_emp FROM hr_employee;
    SELECT COUNT(*) INTO total_customers FROM qlkh_customer;
    SELECT COUNT(*) INTO total_contracts FROM qlkh_contract;
    SELECT COUNT(*) INTO total_prods FROM qlkh_contract_product;

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'TỔNG KẾT DỮ LIỆU MẪU 3 MODULE (nhan_su, quan_ly_khach_hang, quan_ly_van_ban)';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '1. NHÂN SỰ:';
    RAISE NOTICE '   - Nhân viên: % (ID 2-31)', total_emp;
    RAISE NOTICE '   - Chức vụ: 6, Phòng ban: 6';
    RAISE NOTICE '   - Chứng chỉ: 4 loại, 30 bản ghi gán cho NV';
    RAISE NOTICE '   - Dự án IoT: 75 dự án';
    RAISE NOTICE '   - Hồ sơ điện tử: 180 hồ sơ';
    RAISE NOTICE '--------------------------------------------------------------------------------';
    RAISE NOTICE '2. KHÁCH HÀNG & CRM:';
    RAISE NOTICE '   - Sản phẩm IoT: % sản phẩm/dịch vụ', total_prods;
    RAISE NOTICE '   - Khách hàng: % (Mỗi NV phụ trách 15-20 KH)', total_customers;
    RAISE NOTICE '   - Báo giá: 399 báo giá';
    RAISE NOTICE '   - Chi tiết báo giá: ~1200 dòng';
    RAISE NOTICE '   - Hợp đồng: % (Tạo từ báo giá trạng thái chấp nhận)', total_contracts;
    RAISE NOTICE '   - Tương tác KH: 2000 bản ghi';
    RAISE NOTICE '   - Lịch hẹn: 500 cuộc hẹn';
    RAISE NOTICE '--------------------------------------------------------------------------------';
    RAISE NOTICE '3. VĂN BẢN:';
    RAISE NOTICE '   - Văn bản gốc: 499 văn bản';
    RAISE NOTICE '   - Văn bản đến: 99, Văn bản đi: 99';
    RAISE NOTICE '   - Quy trình xử lý: 99 bản ghi';
    RAISE NOTICE '   - Lịch sử phê duyệt: ~400';
    RAISE NOTICE '================================================================================';
END $$;

COMMIT;

-- =====================================================
-- CHÈN DỮ LIỆU HỒ SƠ ĐIỆN TỬ (nhan_su.ho_so_dien_tu)
-- =====================================================
INSERT INTO nhan_su_ho_so_dien_tu (id, ho_so, nhan_vien_id, loai_ho_so, ten_file, ngay_dang_tai, note, van_ban_id)
SELECT 
    gs.id,
    CASE (gs.id % 4) 
        WHEN 0 THEN 'CV cá nhân'
        WHEN 1 THEN 'CCCD/CMND'
        WHEN 2 THEN 'Bằng cấp chuyên môn'
        ELSE 'Hợp đồng lao động'
    END AS ho_so,
    (gs.id % 30) + 2 AS nhan_vien_id,
    CASE (gs.id % 4) 
        WHEN 0 THEN 'cv'
        WHEN 1 THEN 'cccd'
        WHEN 2 THEN 'bang_cap'
        ELSE 'hop_dong_lao_dong'
    END AS loai_ho_so,
    CONCAT('hoso_', gs.id, '.pdf') AS ten_file,
    CURRENT_DATE - ((gs.id % 180) || ' days')::interval AS ngay_dang_tai,
    CONCAT('Hồ sơ nhân sự số ', gs.id) AS note,
    (gs.id % 500) + 2 AS van_ban_id  -- Liên kết tới văn bản đã có (ID từ 2 đến 501)
FROM generate_series(1, 180) as gs(id);

-- Cập nhật lại Sequence ID (để Odoo đếm đúng ID tiếp theo)
SELECT setval('nhan_su_ho_so_dien_tu_id_seq', (SELECT COALESCE(MAX(id), 1) FROM nhan_su_ho_so_dien_tu));