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
    lich_su_cong_tac_ids = fields.One2many('lich_su_cong_tac', 'nhan_vien_id', string='Lịch sử công tác')
    danh_sach_chung_chi_bang_cap_ids = fields.One2many('danh_sach_chung_chi_bang_cap', 'nhan_vien_id', string='Danh sách chứng chỉ bằng cấp')

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten

    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                records = self.env['hr.employee'].search([
                    ('tuoi', '=', record.tuoi),
                    ('id', '!=', record.id)
                ])
                record.so_nguoi_bang_tuoi = len(records)

    @api.depends("birthday")
    def _compute_tuoi(self):
        for record in self:
            if record.birthday:
                year_now = date.today().year
                record.tuoi = year_now - record.birthday.year
            else:
                record.tuoi = 0
