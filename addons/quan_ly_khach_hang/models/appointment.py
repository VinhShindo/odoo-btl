from odoo import models, fields
from datetime import timedelta


class Appointment(models.Model):
    _name = 'qlkh.appointment'
    _description = 'Lịch hẹn khách hàng'

    name = fields.Char(
        string='Tiêu đề',
        required=True
    )

    customer_id = fields.Many2one(
        'qlkh.customer',
        string='Khách hàng',
        required=True
    )

    nhan_vien_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên phụ trách'
    )

    appointment_date = fields.Datetime(
        string='Ngày hẹn',
        required=True
    )

    status = fields.Selection([
        ('moi', 'Mới'),
        ('da_xac_nhan', 'Đã xác nhận'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy')
    ],
    string='Trạng thái',
    default='moi')

    follow_up_id = fields.Many2one(
        'qlkh.appointment',
        string='Cuộc hẹn follow-up',
        copy=False
    )

    related_quotation_id = fields.Many2one(
        'qlkh.quotation',
        string='Báo giá tạo tự động',
        readonly=True
    )

    note = fields.Text(
        string='Ghi chú'
    )

    def write(self, vals):
        original_status = {rec.id: rec.status for rec in self}
        result = super().write(vals)
        for rec in self:
            if original_status.get(rec.id) != rec.status and rec.status == 'hoan_thanh':
                if not rec.follow_up_id:
                    follow_up = self.env['qlkh.appointment'].create({
                        'name': f'Follow-up: {rec.name}',
                        'customer_id': rec.customer_id.id,
                        'nhan_vien_id': rec.nhan_vien_id.id,
                        'appointment_date': fields.Datetime.to_string(fields.Datetime.from_string(fields.Datetime.now()) + timedelta(days=1)),
                        'status': 'moi',
                        'note': 'Tạo lịch hẹn follow-up tự động sau khi cuộc hẹn hoàn thành.',
                    })
                    rec.follow_up_id = follow_up.id

                if rec.customer_id and rec.customer_id.status in ('da_xac_thuc', 'khach_hang_tiem_nang'):
                    if not rec.customer_id.quotation_ids:
                        quotation = self.env['qlkh.quotation'].create({
                            'name': f'BQ-{rec.customer_id.code or rec.customer_id.id}-{fields.Date.today().replace("-", "")}',
                            'customer_id': rec.customer_id.id,
                            'date': fields.Date.today(),
                            'status': 'nhap',
                        })
                        rec.related_quotation_id = quotation.id
                        rec.customer_id.status = 'bao_gia'
        return result
