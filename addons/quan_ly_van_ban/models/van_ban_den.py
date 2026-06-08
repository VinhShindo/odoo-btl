from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import ValidationError

class VanBanDen(models.Model):
    _name = 'van_ban_den'
    _description = 'Bảng chứa thông tin văn bản đến'
    _rec_name = 'ten_van_ban'
    _order = 'ngay_den DESC'

    document_id = fields.Many2one('van_ban.document', string='Văn bản gốc', required=True, ondelete='cascade')

    so_van_ban_den = fields.Char("Số văn bản đến", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_gui_den = fields.Char("Nơi gửi đến")
    
    # === Các trường bổ sung ===
    ngay_den = fields.Date("Ngày đến", default=fields.Date.today, required=True)
    ngay_ban_hanh = fields.Date("Ngày ban hành")
    
    # Liên kết với các đối tượng khác
    loai_van_ban_id = fields.Many2one('loai_van_ban', string="Loại văn bản")
    customer_id = fields.Many2one('qlkh.customer', string="Khách hàng gửi")
    nhan_vien_nhan_id = fields.Many2one('hr.employee', string="Nhân viên tiếp nhận")
    nhan_vien_chuyen_id = fields.Many2one('hr.employee', string="Nhân viên chuyển xử lý")
    
    # Các trường thông tin khác
    nguoi_ky = fields.Char("Người ký")
    so_ban = fields.Integer("Số bản", default=1)
    trich_yeu = fields.Text("Trích yếu nội dung")
    ghi_chu = fields.Text("Ghi chú")
    file_dinh_kem = fields.Binary("File đính kèm")
    
    # Trạng thái xử lý
    trang_thai = fields.Selection([
        ('moi', 'Mới nhận'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('da_xu_ly', 'Đã xử lý'),
        ('luu_tru', 'Lưu trữ')
    ], string="Trạng thái", default='moi')

    # SỬA LẠI METHOD COMPUTE NÀY
    lich_su_xu_ly = fields.Text("Lịch sử xử lý", compute='_compute_lich_su_xu_ly', store=False)
    
    def _compute_lich_su_xu_ly(self):
        for record in self:
            history = []
            try:
                if record.create_date:
                    # Lấy tên người tạo an toàn
                    create_name = record.create_uid.name if record.create_uid and hasattr(record.create_uid, 'name') else 'Hệ thống'
                    history.append(f"[{record.create_date}] Tạo văn bản bởi {create_name}")
                
                if record.write_date and record.write_date != record.create_date:
                    # Lấy tên người cập nhật an toàn
                    write_name = record.write_uid.name if record.write_uid and hasattr(record.write_uid, 'name') else 'Hệ thống'
                    history.append(f"[{record.write_date}] Cập nhật lần cuối bởi {write_name}")
                
                if record.trang_thai == 'dang_xu_ly':
                    nhan_vien_name = record.nhan_vien_nhan_id.name if record.nhan_vien_nhan_id else 'Chưa phân công'
                    history.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Đang xử lý bởi {nhan_vien_name}")
                elif record.trang_thai == 'da_xu_ly':
                    history.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Đã xử lý hoàn tất")
            except Exception as e:
                history.append(f"Lỗi khi tạo lịch sử: {str(e)}")
            
            record.lich_su_xu_ly = "\n".join(history) if history else "Chưa có lịch sử xử lý"

    def action_xac_nhan_xu_ly(self):
        """Xác nhận chuyển trạng thái xử lý"""
        for record in self:
            if record.trang_thai == 'moi':
                record.trang_thai = 'dang_xu_ly'
            elif record.trang_thai == 'dang_xu_ly':
                record.trang_thai = 'da_xu_ly'

    def action_luu_tru(self):
        """Chuyển sang lưu trữ"""
        for record in self:
            if record.trang_thai == 'da_xu_ly':
                record.trang_thai = 'luu_tru'
