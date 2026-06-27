import logging
import sys
import os
from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class Quotation(models.Model):
    _name = 'qlkh.quotation'
    _description = 'Báo giá khách hàng'

    name = fields.Char('Số báo giá', required=True)
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    source = fields.Selection([
        ('system', 'Hệ thống'),
        ('customer', 'Khách hàng')
    ], string='Nguồn báo giá', default='system')
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

    @api.model
    def create(self, vals):
        quotation = super().create(vals)
        # ensure there is a linked document and outgoing record
        try:
            quotation._ensure_linked_document()
        except Exception as e:
            _logger.exception('Không thể tạo document cho báo giá: %s', e)
        return quotation

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
            notif.send_telegram_template(
                'quotation_negotiation',
                quotation_name=self.name,
                customer_name=self.customer_id.name,
                meeting_link=meeting_link
            )
            if self.customer_id and self.customer_id.email:
                notif.send_email_template(
                    'quotation_negotiation',
                    to_email=self.customer_id.email,
                    recipient_name=self.customer_id.name.split()[0] if self.customer_id.name else self.customer_id.name,
                    quotation_name=self.name,
                    customer_name=self.customer_id.name,
                    meeting_link=meeting_link
                )
        except Exception as e:
            _logger.exception('Lỗi tạo cuộc họp đàm phán: %s', e)

    def action_send_email(self):
        # Logic gửi email báo giá cho khách hàng
        for rec in self:
            rec.status = 'da_gui'
            try:
                rec._ensure_linked_document()
                # set document status to 'to_approve' when sent
                if rec._get_linked_document():
                    doc = rec._get_linked_document()
                    doc.write({'status': 'to_approve'})
            except Exception:
                _logger.exception('Lỗi khi cập nhật document khi gửi báo giá %s', rec.id)
        return True

    def action_mark_viewed(self):
        for rec in self:
            if rec.status == 'da_gui':
                rec.status = 'da_xem'
        return True

    def action_set_negotiation(self):
        for rec in self:
            rec.status = 'dam_phan'
        return True

    def action_reject(self):
        for rec in self:
            rec.status = 'tu_choi'
        return True

    def _get_linked_document(self):
        self.ensure_one()
        return self.env['van_ban.document'].search([('related_quotation_id', '=', self.id)], limit=1)

    def _ensure_linked_document(self):
        """Create or update a van_ban.document and van_ban_di record linked to this quotation."""
        self.ensure_one()
        doc = self._get_linked_document()
        if not doc:
            # create document
            doc_vals = {
                'name': f'Báo giá {self.name}',
                'doc_type': 'bao_gia',
                'customer_id': self.customer_id.id if self.customer_id else False,
                'related_quotation_id': self.id,
                'status': 'draft',
            }
            doc = self.env['van_ban.document'].create(doc_vals)
        # decide incoming vs outgoing based on `source`
        if self.source == 'customer':
            incoming = self.env['van_ban_den'].search([('document_id', '=', doc.id)], limit=1)
            if not incoming:
                try:
                    self.env['van_ban_den'].create({
                        'document_id': doc.id,
                        'so_van_ban_den': doc.code or doc.name,
                        'so_hieu_van_ban': doc.code or doc.name,
                        'ten_van_ban': doc.name,
                        'customer_id': self.customer_id.id if self.customer_id else False,
                        'nhan_vien_nhan_id': self.customer_id.nhan_vien_phu_trach_id.id if self.customer_id and self.customer_id.nhan_vien_phu_trach_id else False,
                        'trang_thai': 'moi'
                    })
                except Exception:
                    _logger.exception('Không thể tạo van_ban_den cho báo giá %s', self.id)
        else:
            # ensure outgoing record exists
            outgoing = self.env['van_ban_di'].search([('document_id', '=', doc.id)], limit=1)
            if not outgoing:
                try:
                    self.env['van_ban_di'].create({
                        'document_id': doc.id,
                        'so_van_ban_di': doc.code or doc.name,
                        'so_hieu_van_ban': doc.code or doc.name,
                        'ten_van_ban': doc.name,
                        'customer_id': self.customer_id.id if self.customer_id else False,
                        'nhan_vien_tao_id': self.customer_id.nhan_vien_phu_trach_id.id if self.customer_id and self.customer_id.nhan_vien_phu_trach_id else False,
                        'trang_thai': 'draft'
                    })
                except Exception:
                    _logger.exception('Không thể tạo van_ban_di cho báo giá %s', self.id)

    def write(self, vals):
        old_status = {rec.id: rec.status for rec in self}
        result = super().write(vals)

        if 'status' in vals:
            for rec in self:
                try:
                    rec._ensure_linked_document()
                    doc = rec._get_linked_document()
                    if doc:
                        # map quotation status to document.status
                        mapping = {
                            'nhap': 'draft',
                            'da_gui': 'to_approve',
                            'da_xem': 'to_approve',
                            'dam_phan': 'to_approve',
                            'chap_nhan': 'approved',
                            'tu_choi': 'archived'
                        }
                        new_doc_status = mapping.get(rec.status, doc.status)
                        doc.write({'status': new_doc_status})
                        # create approval history if approved/rejected
                        if rec.status in ['chap_nhan', 'tu_choi']:
                            try:
                                self.env['van_ban.approval'].create({
                                    'document_id': doc.id,
                                    'approver_id': rec.customer_id.nhan_vien_phu_trach_id.id if rec.customer_id and rec.customer_id.nhan_vien_phu_trach_id else False,
                                    'approver_user_id': self.env.uid,
                                    'status': 'approved' if rec.status == 'chap_nhan' else 'rejected',
                                    'comment': 'Auto-created from quotation status change',
                                    'level': 1
                                })
                            except Exception:
                                _logger.exception('Không thể tạo lịch sử phê duyệt cho document %s', doc.id)
                except Exception:
                    _logger.exception('Lỗi khi sync document cho báo giá %s', rec.id)

        return result

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
