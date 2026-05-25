from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Quotation(models.Model):
    _name = 'qlkh.quotation'
    _description = 'Báo giá khách hàng'

    name = fields.Char('Số báo giá', required=True)
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    date = fields.Date('Ngày báo giá', required=True)
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('sent', 'Đã gửi'),
        ('accepted', 'Khách hàng đồng ý'),
        ('rejected', 'Khách hàng từ chối')
    ], string='Trạng thái', default='draft')
    file = fields.Binary('File báo giá')
    file_name = fields.Char('Tên file báo giá')
    note = fields.Text('Ghi chú')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Số báo giá phải là duy nhất!')
    ]

    def action_send_email(self):
        # Logic gửi email báo giá cho khách hàng
        pass
