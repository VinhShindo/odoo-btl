from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _inherit = 'hr.employee'  # Kế thừa từ model chuẩn Odoo
    _description = 'Bảng chứa thông tin nhân viên mở rộng'

    ma_dinh_danh = fields.Char("Mã định danh", required=False)
    ho_ten_dem = fields.Char("Họ tên đệm")
    ten = fields.Char("Tên")
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    que_quan = fields.Char("Quê quán")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    so_nguoi_bang_tuoi = fields.Integer("Số người bằng tuổi", compute="_compute_so_nguoi_bang_tuoi", store=True)
    don_vi_id = fields.Many2one('don_vi', string='Phòng ban / Đơn vị')
    so_khach_hang_phu_trach = fields.Integer('Số khách hàng phụ trách', compute='_compute_quan_ly_khach_hang', store=False)
    so_bao_gia = fields.Integer('Số báo giá', compute='_compute_quan_ly_khach_hang', store=False)
    so_hop_dong = fields.Integer('Số hợp đồng', compute='_compute_quan_ly_khach_hang', store=False)
    so_van_ban_xu_ly = fields.Integer('Số văn bản xử lý', compute='_compute_quan_ly_khach_hang', store=False)
    diem_kpi = fields.Float('Điểm KPI', compute='_compute_quan_ly_khach_hang', store=False)
    muc_tieu_doanh_so = fields.Float('Mục tiêu doanh số', compute='_compute_quan_ly_khach_hang', store=False)
    tien_do_kpi = fields.Float('Tiến độ KPI', compute='_compute_quan_ly_khach_hang', store=False)
    ghi_chu_nhan_su = fields.Text('Ghi chú nhân sự', compute='_compute_quan_ly_khach_hang', store=False)
    lich_su_cong_tac_ids = fields.One2many('lich_su_cong_tac', 'nhan_vien_id', string='Lịch sử công tác')
    danh_sach_chung_chi_bang_cap_ids = fields.One2many('danh_sach_chung_chi_bang_cap', 'nhan_vien_id', string='Danh sách chứng chỉ bằng cấp')
    document_ids = fields.One2many(
        'van_ban.document',
        'nhan_vien_id'
    )
    folder_id = fields.Many2one('van_ban.folder', string='Thư mục hồ sơ nhân viên', readonly=True)

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten
            elif record.ten:
                record.ho_va_ten = record.ten
            else:
                record.ho_va_ten = record.ho_ten_dem or ''

    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                records = self.env['hr.employee'].search([
                    ('tuoi', '=', record.tuoi),
                    ('id', '!=', record.id)
                ])
                record.so_nguoi_bang_tuoi = len(records)
            else:
                record.so_nguoi_bang_tuoi = 0

    @api.depends("birthday")
    def _compute_tuoi(self):
        for record in self:
            if record.birthday:
                year_now = date.today().year
                record.tuoi = year_now - record.birthday.year
            else:
                record.tuoi = 0

    @api.depends()
    def _compute_quan_ly_khach_hang(self):
        for record in self:
            customers = self.env['qlkh.customer'].search([('nhan_vien_phu_trach_id', '=', record.id)])
            record.so_khach_hang_phu_trach = len(customers)
            record.so_bao_gia = self.env['qlkh.quotation'].search_count([('customer_id.nhan_vien_phu_trach_id', '=', record.id)])
            record.so_hop_dong = self.env['qlkh.contract'].search_count([('customer_id.nhan_vien_phu_trach_id', '=', record.id)])
            docs = self.env['van_ban.document'].search([
                '|',
                ('nhan_vien_id', '=', record.id),
                ('customer_id', 'in', customers.ids)
            ])
            record.so_van_ban_xu_ly = len(docs)
            record.diem_kpi = record.so_hop_dong * 10.0 + record.so_bao_gia * 2.0
            record.muc_tieu_doanh_so = record.so_hop_dong * 1000000.0 + record.so_khach_hang_phu_trach * 500000.0
            record.tien_do_kpi = record.diem_kpi * 100.0 if record.diem_kpi else 0.0
            record.ghi_chu_nhan_su = (
                f"Tổng số khách hàng: {record.so_khach_hang_phu_trach}. "
                f"Báo giá: {record.so_bao_gia}. "
                f"Hợp đồng: {record.so_hop_dong}. "
                f"Văn bản xử lý: {record.so_van_ban_xu_ly}."
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_employee_folder()
        return records

    def _create_employee_folder(self):
        """Tự động tạo thư mục hồ sơ nhân viên khi tạo nhân viên mới"""
        self.ensure_one()
        
        # Tìm hoặc tạo folder "Nhân viên" gốc
        employee_root = self.env['van_ban.folder'].search([
            ('name', '=', 'Nhân viên'),
            ('parent_id', '=', False)
        ], limit=1)
        
        if not employee_root:
            employee_root = self.env['van_ban.folder'].create({
                'name': 'Nhân viên',
                'folder_type': 'employee'
            })
        
        # Tìm hoặc tạo folder phòng ban
        don_vi_name = self.don_vi_id.ten_don_vi if self.don_vi_id else 'Không xác định'
        don_vi_folder = self.env['van_ban.folder'].search([
            ('name', '=', don_vi_name),
            ('parent_id', '=', employee_root.id)
        ], limit=1)
        
        if not don_vi_folder:
            don_vi_folder = self.env['van_ban.folder'].create({
                'name': don_vi_name,
                'parent_id': employee_root.id,
                'folder_type': 'employee'
            })
        
        # Tạo folder nhân viên
        employee_name = self.ho_va_ten or self.name or f"Nhân viên {self.id}"
        employee_folder = self.env['van_ban.folder'].create({
            'name': employee_name,
            'parent_id': don_vi_folder.id,
            'folder_type': 'employee'
        })
        
        # Lưu reference - dùng write để chắc chắn save vào database
        self.write({'folder_id': employee_folder.id})
