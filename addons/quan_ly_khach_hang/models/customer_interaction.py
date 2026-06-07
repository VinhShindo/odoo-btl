from odoo import models, fields, api

class CustomerInteraction(models.Model):
    _name = 'qlkh.customer_interaction'
    _description = 'Lịch sử giao dịch, chăm sóc khách hàng'

    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    date = fields.Datetime('Thời gian')
    type = fields.Selection([
        ('goi_dien', 'Gọi điện'),
        ('gap_mat', 'Gặp mặt'),
        ('email', 'Email'),
        ('ho_tro', 'Hỗ trợ'),
        ('khieu_nai', 'Khiếu nại'),
        ('khac', 'Khác')
    ], string='Loại tương tác')
    status = fields.Selection([
        ('moi', 'Mới'),
        ('da_thuc_hien', 'Đã thực hiện'),
        ('huy', 'Hủy')
    ], string='Trạng thái',
    default='moi')
    content = fields.Text('Nội dung')
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên thực hiện')
    note = fields.Text('Ghi chú')
