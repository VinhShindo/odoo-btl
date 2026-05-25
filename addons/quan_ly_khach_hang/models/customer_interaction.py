from odoo import models, fields, api

class CustomerInteraction(models.Model):
    _name = 'qlkh.customer_interaction'
    _description = 'Lịch sử giao dịch, chăm sóc khách hàng'

    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    date = fields.Datetime('Thời gian')
    type = fields.Selection([
        ('call', 'Gọi điện'),
        ('meeting', 'Gặp mặt'),
        ('email', 'Email'),
        ('support', 'Hỗ trợ'),
        ('complaint', 'Khiếu nại'),
        ('other', 'Khác')
    ], string='Loại tương tác')
    content = fields.Text('Nội dung')
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên thực hiện')
    note = fields.Text('Ghi chú')
