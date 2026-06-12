import logging
import os
import sys
from datetime import date, timedelta, datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class Contract(models.Model):
    _name = 'qlkh.contract'
    _description = 'Hợp đồng khách hàng'

    name = fields.Char('Số hợp đồng', required=True)
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    date_start = fields.Date('Ngày bắt đầu', required=True)
    date_end = fields.Date('Ngày kết thúc', required=True)
    contract_value = fields.Float(
        string='Giá trị hợp đồng',
        default=0
    )
    status = fields.Selection([
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('hieu_luc', 'Hiệu lực'),
        ('sap_het_han', 'Sắp hết hạn'),
        ('het_han', 'Hết hạn')
    ],
    string='Trạng thái',
    default='nhap')
    iot_device = fields.Char('Thiết bị IoT bảo trì')
    file = fields.Binary('File hợp đồng')
    file_name = fields.Char('Tên file hợp đồng')
    note = fields.Text('Ghi chú')
    quotation_id = fields.Many2one(
        'qlkh.quotation',
        string='Báo giá nguồn'
    )
    ai_summary = fields.Text('Tóm tắt AI')
    ai_processed_at = fields.Datetime('Thời điểm xử lý AI')
    ai_processed_by = fields.Many2one('res.users', string='AI xử lý bởi')
    
    document_count = fields.Integer(
        compute='_compute_document_count'
    )

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = self.env['van_ban.document'].search_count([
                ('related_contract_id', '=', rec.id)
            ])

    def check_expiry(self):
        # Cảnh báo hợp đồng sắp hết hạn
        today = date.today()
        soon = today + timedelta(days=30)
        contracts = self.search([
        ('date_end', '<=', soon),
        ('status', '=', 'hieu_luc')
    ])
        for contract in contracts:
            if not contract.date_end:
                continue
            days_left = (
                contract.date_end - today
            ).days

            if days_left <= 0:
                contract.status = 'het_han'

            elif days_left <= 30:
                contract.status = 'sap_het_han'
                document = self.env[
                    'van_ban.document'
                ].search([
                    ('related_contract_id', '=', contract.id)
                ], limit=1)

                if document:

                    self.env['mail.activity'].create({

                        'res_model_id':
                            self.env['ir.model']._get_id(
                                'van_ban.document'
                            ),

                        'res_id': document.id,

                        'summary':
                            'Hợp đồng sắp hết hạn',

                        'note':
                            f'Hợp đồng {contract.name} '
                            f'còn {days_left} ngày',

                        'user_id':
                            self.env.user.id
                    })

    def cron_archive_expired_contracts(self):
        contracts = self.env[
            'qlkh.contract'
        ].search([
            ('status', '=', 'het_han')
        ])

        for contract in contracts:

            docs = self.env[
                'van_ban.document'
            ].search([
                ('related_contract_id', '=', contract.id)
            ])

            docs.write({
                'status': 'archived'
            })

    @api.constrains(
        'date_start',
        'date_end'
    )
    def _check_date(self):
        for rec in self:
            if rec.date_end < rec.date_start:
                raise ValidationError(
                    'Ngày kết thúc phải lớn hơn ngày bắt đầu'
                )
    def action_submit(self):
        for rec in self:
            rec.status = 'cho_duyet'


    def action_approve(self):
        for rec in self:
            if rec.status == 'da_duyet':
                continue

            rec.status = 'da_duyet'

            document_exist = self.env[
                'van_ban.document'
            ].search([
                ('related_contract_id', '=', rec.id)
            ], limit=1)

            if not document_exist:
                document = self.env[
                    'van_ban.document'
                ].create({
                    'name': f'Hồ sơ hợp đồng {rec.name}',
                    'doc_type': 'hop_dong',
                    'customer_id': rec.customer_id.id,
                    'related_contract_id': rec.id,
                    'status': 'draft',
                    'file': rec.file,
                    'file_name': rec.file_name,
                })

                if document.file:
                    try:
                        document.action_scan_ocr()
                    except Exception:
                        pass

            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.ai_helper import AIHelper
                from smart_biz_services.notif_helper import NotifHelper

                ai = AIHelper()
                notif = NotifHelper()

                summary = ''
                if rec.file:
                    try:
                        summary = ai.summarize_document(rec.file_name or 'Nội dung hợp đồng', max_length=200)
                    except Exception as e:
                        _logger.warning('Summarize contract failed: %s', e)
                        summary = f'Hợp đồng: {rec.name}'

                rec.ai_summary = summary
                rec.ai_processed_at = fields.Datetime.now()
                rec.ai_processed_by = self.env.user

                notification_content = (
                    f"Hợp đồng phê duyệt: {rec.name}\n"
                    f"Khách hàng: {rec.customer_id.name if rec.customer_id else 'N/A'}\n"
                    f"Giá trị: {rec.contract_value:,.0f} VNĐ\n"
                    f"Từ: {rec.date_start} đến {rec.date_end}\n"
                    f"Tóm tắt: {summary}"
                )

                try:
                    notif.send_telegram(
                        title=f'Hợp đồng phê duyệt: {rec.name}',
                        content=notification_content
                    )
                except Exception as e:
                    _logger.error('Gửi Telegram cho hợp đồng thất bại: %s', e, exc_info=True)

                if rec.customer_id and rec.customer_id.email:
                    try:
                        notif.send_email(
                            to_email=rec.customer_id.email,
                            subject=f'Hợp đồng {rec.name} đã được phê duyệt',
                            body=notification_content,
                            is_html=False,
                            use_default=False
                        )
                    except Exception as e:
                        _logger.error('Gửi email khách hàng thất bại: %s', e, exc_info=True)

                activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                if activity_type:
                    self.env['mail.activity'].create({
                        'activity_type_id': activity_type.id,
                        'summary': f'Theo dõi triển khai hợp đồng {rec.name}',
                        'note': notification_content,
                        'res_model_id': self.env['ir.model']._get(self._name).id,
                        'res_id': rec.id,
                        'user_id': rec.customer_id.nhan_vien_phu_trach_id.user_id.id if (
                            rec.customer_id and rec.customer_id.nhan_vien_phu_trach_id and rec.customer_id.nhan_vien_phu_trach_id.user_id
                        ) else self.env.user.id,
                        'date_deadline': date.today() + timedelta(days=7),
                    })

            except Exception as e:
                _logger.error('Lỗi trong quá trình phê duyệt hợp đồng: %s', e, exc_info=True)


    def action_activate(self):
        for rec in self:
            rec.status = 'hieu_luc'

            if rec.customer_id:
                rec.customer_id.status = 'thanh_cong'

    _sql_constraints = [
    (
        'contract_name_unique',
        'unique(name)',
        'Số hợp đồng phải là duy nhất!'
    )
]