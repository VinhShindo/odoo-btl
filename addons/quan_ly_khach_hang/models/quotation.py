from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Quotation(models.Model):
    _name = 'qlkh.quotation'
    _description = 'Báo giá khách hàng'

    name = fields.Char('Số báo giá', required=True)
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    date = fields.Date('Ngày báo giá', required=True)
    status = fields.Selection([
        ('nhap', 'Nháp'),
        ('da_gui', 'Đã gửi'),
        ('da_xem', 'Đã xem'),
        ('dam_phan', 'Đàm phán'),
        ('chap_nhan', 'Chấp nhận'),
        ('tu_choi', 'Từ chối')
    ],
    string='Trạng thái',
    default='nhap')
    file = fields.Binary('File báo giá')
    file_name = fields.Char('Tên file báo giá')
    note = fields.Text('Ghi chú')
    contract_ids = fields.One2many(
        'qlkh.contract',
        'quotation_id',
        string='Hợp đồng'
    )
    line_ids = fields.One2many(
        'qlkh.quotation.line',
        'quotation_id',
        string='Chi tiết sản phẩm'
    )
    quotation_value = fields.Float(
        string='Giá trị báo giá',
        compute='_compute_quotation_value',
        store=True
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Số báo giá phải là duy nhất!')
    ]

    def _compute_quotation_value(self):
        for rec in self:
            rec.quotation_value = sum(
                rec.line_ids.mapped('price_total')
            ) if rec.line_ids else 0.0

    def action_send_email(self):
        # Logic gửi email báo giá cho khách hàng
        pass

    def action_accept_quotation(self):
        self.ensure_one()
        self.status = 'chap_nhan'
        self.customer_id.status = 'dam_phan'

        contract = self.env['qlkh.contract'].create({
            'name': f'HD-{self.name}',
            'customer_id': self.customer_id.id,
            'quotation_id': self.id,
            'contract_value': self.quotation_value,
            'status': 'nhap',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qlkh.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }
