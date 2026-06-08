from odoo import models, fields, api
from datetime import date, datetime

from odoo.exceptions import ValidationError


class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Bảng chứa thông tin văn bản đi'
    _rec_name = 'ten_van_ban'
    _order = 'ngay_di DESC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    document_id = fields.Many2one('van_ban.document', string='Văn bản gốc', required=True, ondelete='cascade')

    so_van_ban_di = fields.Char("Số văn bản đi", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_nhan = fields.Char("Nơi nhận")
    
    # === Các trường bổ sung ===
    ngay_di = fields.Date("Ngày đi", default=fields.Date.today, required=True)
    ngay_ban_hanh = fields.Date("Ngày ban hành")
    
    # Liên kết với các đối tượng khác
    loai_van_ban_id = fields.Many2one('loai_van_ban', string="Loại văn bản")
    customer_id = fields.Many2one('qlkh.customer', string="Khách hàng nhận")
    nhan_vien_tao_id = fields.Many2one('hr.employee', string="Nhân viên tạo")
    nhan_vien_ky_id = fields.Many2one('hr.employee', string="Người ký")
    
    # Các trường thông tin khác
    nguoi_ky = fields.Char("Người ký (Tên)")
    so_ban = fields.Integer("Số bản", default=1)
    trich_yeu = fields.Text("Trích yếu nội dung")
    ghi_chu = fields.Text("Ghi chú")
    file_dinh_kem = fields.Binary("File đính kèm")
    
    # Trạng thái xử lý
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('da_ky', 'Đã ký'),
        ('da_gui', 'Đã gửi'),
        ('hoan_thanh', 'Hoàn thành')
    ], string="Trạng thái", default='draft')
    
    # SỬA LẠI METHOD COMPUTE NÀY
    lich_su_gui = fields.Text("Lịch sử gửi", compute='_compute_lich_su_gui', store=False)
    
    def _compute_lich_su_gui(self):
        for record in self:
            history = []
            try:
                if record.create_date:
                    create_name = record.create_uid.name if record.create_uid and hasattr(record.create_uid, 'name') else 'Hệ thống'
                    history.append(f"[{record.create_date}] Tạo văn bản bởi {create_name}")
                
                if record.trang_thai == 'da_ky':
                    ky_name = record.nhan_vien_ky_id.name if record.nhan_vien_ky_id else record.nguoi_ky or 'Chưa xác định'
                    history.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Đã ký bởi {ky_name}")
                elif record.trang_thai == 'da_gui':
                    history.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Đã gửi đến {record.noi_nhan or 'Chưa xác định'}")
                elif record.trang_thai == 'hoan_thanh':
                    history.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Hoàn thành xử lý")
            except Exception as e:
                history.append(f"Lỗi khi tạo lịch sử: {str(e)}")
            
            record.lich_su_gui = "\n".join(history) if history else "Chưa có lịch sử gửi"

    def action_trinh_ky(self):
        """Trình ký văn bản"""
        for record in self:
            if record.trang_thai == 'draft':
                record.trang_thai = 'da_ky'
    
    def action_xac_nhan_gui(self):
        """Xác nhận đã gửi"""
        for record in self:
            if record.trang_thai == 'da_ky':
                record.trang_thai = 'da_gui'
    
    def action_hoan_thanh(self):
        """Hoàn thành văn bản"""
        for record in self:
            if record.trang_thai == 'da_gui':
                record.trang_thai = 'hoan_thanh'