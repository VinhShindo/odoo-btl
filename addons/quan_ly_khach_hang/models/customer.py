from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Customer(models.Model):
    _name = 'qlkh.customer'
    _description = 'Khách hàng'
    _rec_name = 'name'

    name = fields.Char('Tên khách hàng', required=True)
    code = fields.Char('Mã khách hàng', required=True)
    customer_type = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('doanh_nghiep', 'Doanh nghiệp')
    ], string='Loại khách hàng', required=True)
    status = fields.Selection([
        ('moi', 'Mới'),
        ('dang_cham_soc', 'Đang chăm sóc'),
        ('chinh_thuc', 'Chính thức'),
        ('ngung', 'Ngừng giao dịch')
    ], string='Trạng thái', default='moi')
    nhan_vien_phu_trach_id = fields.Many2one('hr.employee', string='Người phụ trách', required=True)
    iot_device = fields.Char('Thiết bị IoT sử dụng')
    email = fields.Char('Email')
    phone = fields.Char('Số điện thoại')
    address = fields.Char('Địa chỉ')
    note = fields.Text('Ghi chú')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã khách hàng phải là duy nhất!'),
        ('name_unique', 'unique(name)', 'Tên khách hàng phải là duy nhất!')
    ]

    @api.model
    def create(self, vals):
        # Kiểm tra trùng lặp khách hàng
        if 'name' in vals and self.search([('name', '=', vals['name'])]):
            raise ValidationError('Tên khách hàng đã tồn tại!')
        if 'code' in vals and self.search([('code', '=', vals['code'])]):
            raise ValidationError('Mã khách hàng đã tồn tại!')
        return super().create(vals)
