import logging
import sys
from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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
    meet_url = fields.Char('Link Google Meet')
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

    def write(self, vals):
        old_status = {rec.id: rec.status for rec in self}
        result = super().write(vals)

        if 'status' in vals and vals['status'] == 'dam_phan':
            for rec in self:
                if old_status.get(rec.id) != 'dam_phan':
                    try:
                        rec._schedule_negotiation_meeting()
                    except Exception as e:
                        _logger.exception('Lỗi lên lịch đàm phán cho báo giá %s: %s', rec.id, e)

        return result

    def _schedule_negotiation_meeting(self):
        self.ensure_one()
        if self.status != 'dam_phan' or self.meet_url:
            return

        if not self.customer_id or not self.customer_id.email:
            return

        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.google_helper import GoogleHelper
            from smart_biz_services.notif_helper import NotifHelper

            google = GoogleHelper()
            notif = NotifHelper()

            title = f'Cuộc họp đàm phán báo giá {self.name}'
            meeting_link = google.create_meeting(
                customer_email=self.customer_id.email,
                customer_name=self.customer_id.name,
                title=title,
                duration_minutes=30
            )

            if not meeting_link:
                return

            super(Quotation, self).write({'meet_url': meeting_link})

            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if activity_type:
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type.id,
                    'summary': 'Theo dõi đàm phán báo giá',
                    'note': f'{title}\nGoogle Meet: {meeting_link}',
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'res_id': self.id,
                    'user_id': self.customer_id.nhan_vien_phu_trach_id.user_id.id if (
                        self.customer_id.nhan_vien_phu_trach_id and self.customer_id.nhan_vien_phu_trach_id.user_id
                    ) else self.env.user.id,
                    'date_deadline': fields.Date.today() + timedelta(days=2),
                })

            notification_content = (
                f"Báo giá đang đàm phán: {self.name}\n"
                f"Khách hàng: {self.customer_id.name}\n"
                f"Link Google Meet: {meeting_link}"
            )

            notif.send_telegram(
                title=title,
                content=notification_content
            )
            notif.send_email(
                to_email=self.customer_id.email,
                subject=title,
                body=notification_content,
                is_html=False,
                use_default=False
            )
        except Exception as e:
            _logger.exception('Lỗi tạo cuộc họp đàm phán: %s', e)

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
