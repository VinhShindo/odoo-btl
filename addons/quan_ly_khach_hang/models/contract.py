from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class Contract(models.Model):
    _name = 'qlkh.contract'
    _description = 'Hợp đồng khách hàng'

    name = fields.Char('Số hợp đồng', required=True)
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    date_start = fields.Date('Ngày bắt đầu', required=True)
    date_end = fields.Date('Ngày kết thúc', required=True)
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('active', 'Đang hiệu lực'),
        ('expired', 'Hết hạn'),
        ('terminated', 'Đã thanh lý')
    ], string='Trạng thái', default='draft')
    iot_device = fields.Char('Thiết bị IoT bảo trì')
    file = fields.Binary('File hợp đồng')
    file_name = fields.Char('Tên file hợp đồng')
    note = fields.Text('Ghi chú')

    @api.model
    def create(self, vals):
        # Kiểm tra trùng lặp số hợp đồng
        if 'name' in vals and self.search([('name', '=', vals['name'])]):
            raise ValidationError('Số hợp đồng đã tồn tại!')
        return super().create(vals)

    def check_expiry(self):
        # Cảnh báo hợp đồng sắp hết hạn
        today = date.today()
        soon = today + timedelta(days=30)
        contracts = self.search([('date_end', '<=', soon), ('status', '=', 'active')])
        for contract in contracts:
            # Logic gửi cảnh báo (email, thông báo...)
            pass
