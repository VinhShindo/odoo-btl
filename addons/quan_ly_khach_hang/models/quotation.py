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

    name = fields.Char('Số báo giá', required=True, default=lambda self: self._get_default_name())
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    source = fields.Selection([
        ('system', 'Hệ thống'),
        ('customer', 'Khách hàng')
    ], string='Nguồn báo giá', default='system')
    date = fields.Date('Ngày báo giá', required=True, default=fields.Date.context_today)
    status = fields.Selection([
        ('nhap', 'Nháp'),
        ('da_gui', 'Đã gửi'),
        ('da_xem', 'Đã xem'),
        ('dam_phan', 'Đàm phán'),
        ('chap_nhan', 'Chấp nhận'),
        ('tu_choi', 'Từ chối')
    ], string='Trạng thái', default='nhap')
    file = fields.Binary('File báo giá')
    file_name = fields.Char('Tên file báo giá')
    note = fields.Text('Ghi chú')
    meet_url = fields.Char('Link Google Meet')
    contract_ids = fields.One2many('qlkh.contract', 'quotation_id', string='Hợp đồng')
    line_ids = fields.One2many('qlkh.quotation.line', 'quotation_id', string='Chi tiết sản phẩm')
    quotation_value = fields.Float(
        string='Giá trị báo giá',
        compute='_compute_quotation_value',
        store=True
    )

    _sql_constraints = [('name_unique', 'unique(name)', 'Số báo giá phải là duy nhất!')]

    @api.depends('line_ids.price_total')
    def _compute_quotation_value(self):
        for rec in self:
            rec.quotation_value = sum(rec.line_ids.mapped('price_total')) if rec.line_ids else 0.0

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            domain = ['|', ('name', operator, name), ('customer_id.name', operator, name)]
            return self.search(domain + args, limit=limit).name_get()
        return super(Quotation, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model
    def _get_default_name(self):
        date_str = fields.Date.today().strftime('%Y%m%d')
        seq_code = 'qlkh.quotation'
        sequence_name = self.env['ir.sequence'].next_by_code(seq_code)
        if sequence_name:
            return sequence_name
        count = self.search_count([('name', 'ilike', f'BG-{date_str}%')]) + 1
        return f'BG-{date_str}-{count:03d}'

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self._get_default_name()
        quotation = super().create(vals)
        try:
            quotation._ensure_linked_document()
        except Exception as e:
            _logger.exception('Không thể tạo document cho báo giá: %s', e)
        return quotation

    def write(self, vals):
        """Consolidated write: sync file/metadata, skip redundant OCR, handle status."""
        old_status = {rec.id: rec.status for rec in self}
        result = super().write(vals)

        for rec in self:
            try:
                # Ensure a linked document exists when relevant fields change
                needs_doc = any(k in vals for k in ('file', 'file_name', 'customer_id', 'source', 'name'))
                doc = rec._get_linked_document() if not needs_doc else None
                if needs_doc and not doc:
                    doc = rec._ensure_linked_document()
                    doc = rec._get_linked_document()

                # If customer/source/name changed, ensure metadata and title updated
                if any(k in vals for k in ('customer_id', 'source', 'name')):
                    if not doc:
                        doc = rec._ensure_linked_document()
                    if doc:
                        # Update default metadata without overwriting existing values
                        metadata = self.env['van_ban.document']._get_default_document_metadata(
                            customer=rec.customer_id,
                            employee=rec.customer_id.nhan_vien_phu_trach_id if rec.customer_id else False,
                            doc_type='bao_gia'
                        )
                        update_vals = {}
                        desired_name = f'Báo giá {rec.name}'
                        if doc.name != desired_name:
                            update_vals['name'] = desired_name
                        for k, v in metadata.items():
                            if v and not doc[k]:
                                update_vals[k] = v
                        if update_vals:
                            try:
                                doc.write(update_vals)
                            except Exception:
                                _logger.exception('Không thể cập nhật metadata cho document báo giá %s', doc.id)

                # File changed: sync file and run OCR only if not completed
                if 'file' in vals or 'file_name' in vals:
                    if not doc:
                        doc = rec._ensure_linked_document()
                        doc = rec._get_linked_document()
                    if doc and (rec.file or rec.file_name):
                        try:
                            ocr_done = getattr(doc, 'ocr_status', None) == 'completed'
                        except Exception:
                            ocr_done = False
                        try:
                            doc.write({
                                'file': rec.file,
                                'file_name': rec.file_name,
                                'date_upload': fields.Datetime.now(),
                                'status': 'draft',
                            })
                        except Exception:
                            _logger.exception('Không thể đồng bộ file báo giá vào document %s', doc.id)

                        if not ocr_done:
                            try:
                                doc.action_scan_ocr()
                            except Exception:
                                _logger.exception('Không thể chạy OCR document cho báo giá %s', doc.id)

                # Status changes: map to document status and create approval history
                if 'status' in vals:
                    try:
                        # Ensure document exists and update metadata/title always when status changes
                        rec._ensure_linked_document()
                        doc = rec._get_linked_document()
                        if doc:
                            try:
                                metadata = self.env['van_ban.document']._get_default_document_metadata(
                                    customer=rec.customer_id,
                                    employee=rec.customer_id.nhan_vien_phu_trach_id if rec.customer_id else False,
                                    doc_type='bao_gia'
                                )
                                update_vals = {}
                                desired_name = f'Báo giá {rec.name}'
                                if doc.name != desired_name:
                                    update_vals['name'] = desired_name
                                for k, v in metadata.items():
                                    if v and not doc[k]:
                                        update_vals[k] = v
                                if update_vals:
                                    doc.write(update_vals)
                            except Exception:
                                _logger.exception('Không thể cập nhật metadata cho document %s', doc.id)
                        if doc:
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
                            # When quotation accepted, ensure a Google Meet link is created and saved
                            if rec.status == 'chap_nhan' and not rec.meet_url:
                                try:
                                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                                    from smart_biz_services.google_helper import GoogleHelper
                                    from smart_biz_services.notif_helper import NotifHelper

                                    google = GoogleHelper()
                                    notif = NotifHelper()

                                    meeting_title = f'Bàn giao báo giá {rec.name}'
                                    meeting_link = google.create_meeting(
                                        customer_email=rec.customer_id.email if rec.customer_id and rec.customer_id.email else None,
                                        customer_name=rec.customer_id.name if rec.customer_id else None,
                                        title=meeting_title,
                                        duration_minutes=30
                                    )
                                    if meeting_link:
                                        try:
                                            rec.write({'meet_url': meeting_link})
                                        except Exception:
                                            rec.meet_url = meeting_link
                                    # update document status mapping already done; also ensure van_ban_di/den exist
                                    if doc:
                                        try:
                                            if rec.source == 'customer':
                                                incoming = self.env['van_ban_den'].search([('document_id', '=', doc.id)], limit=1)
                                                if not incoming:
                                                    self.env['van_ban_den'].create({
                                                        'document_id': doc.id,
                                                        'so_van_ban_den': doc.code or doc.name,
                                                        'so_hieu_van_ban': doc.code or doc.name,
                                                        'ten_van_ban': doc.name,
                                                        'customer_id': rec.customer_id.id if rec.customer_id else False,
                                                        'nhan_vien_nhan_id': rec.customer_id.nhan_vien_phu_trach_id.id if rec.customer_id and rec.customer_id.nhan_vien_phu_trach_id else False,
                                                        'loai_van_ban_id': doc.loai_van_ban_id.id if doc.loai_van_ban_id else self.env['van_ban.document']._lookup_loai_van_ban('bao_gia'),
                                                        'trang_thai': 'moi'
                                                    })
                                            else:
                                                outgoing = self.env['van_ban_di'].search([('document_id', '=', doc.id)], limit=1)
                                                if not outgoing:
                                                    self.env['van_ban_di'].create({
                                                        'document_id': doc.id,
                                                        'so_van_ban_di': doc.code or doc.name,
                                                        'so_hieu_van_ban': doc.code or doc.name,
                                                        'ten_van_ban': doc.name,
                                                        'customer_id': rec.customer_id.id if rec.customer_id else False,
                                                        'nhan_vien_tao_id': rec.customer_id.nhan_vien_phu_trach_id.id if rec.customer_id and rec.customer_id.nhan_vien_phu_trach_id else False,
                                                        'loai_van_ban_id': doc.loai_van_ban_id.id if doc.loai_van_ban_id else self.env['van_ban.document']._lookup_loai_van_ban('bao_gia'),
                                                        'trang_thai': 'draft'
                                                    })
                                        except Exception:
                                            _logger.exception('Không thể tạo van_ban_den/di cho báo giá %s', rec.id)
                                except Exception:
                                    _logger.exception('Không thể tạo link Google Meet cho báo giá %s', rec.id)
                    except Exception:
                        _logger.exception('Lỗi khi sync document cho báo giá %s', rec.id)

                # Recompute totals when lines change
                if 'line_ids' in vals:
                    try:
                        rec._compute_quotation_value()
                    except Exception:
                        _logger.exception('Không thể tính lại tổng báo giá cho %s', rec.id)

            except Exception:
                _logger.exception('Lỗi trong write() của quotation %s', rec.id)

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
        for rec in self:
            rec.status = 'da_gui'
            if rec.customer_id:
                rec.customer_id.status = 'da_gui_bao_gia'
            try:
                rec._ensure_linked_document()
                if rec._get_linked_document():
                    doc = rec._get_linked_document()
                    doc.write({'status': 'to_approve'})
            except Exception:
                _logger.exception('Lỗi khi cập nhật document khi gửi báo giá %s', rec.id)

            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.notif_helper import NotifHelper
                notif = NotifHelper()
                rec._compute_quotation_value()
                line_items = []
                for line in rec.line_ids:
                    line_items.append({
                        'product_name': line.product_name or (line.product_id.name if line.product_id else ''),
                        'description': line.description or '',
                        'quantity': line.quantity,
                        'unit_price': line.unit_price,
                        'vat_rate': line.vat_rate,
                        'price_subtotal': line.price_subtotal,
                        'price_tax': line.price_tax,
                        'price_total': line.price_total,
                    })
                if rec.customer_id and rec.customer_id.email:
                    notif.send_email_template(
                        'quotation_sent',
                        to_email=rec.customer_id.email,
                        recipient_name=rec.customer_id.name.split()[0] if rec.customer_id.name else rec.customer_id.name,
                        quotation_name=rec.name,
                        customer_name=rec.customer_id.name,
                        quotation_value=rec.quotation_value,
                        quotation_date=rec.date,
                        meeting_link=rec.meet_url or 'Chưa có link họp',
                        line_items=line_items,
                    )
                notif.send_telegram_template(
                    'quotation_sent',
                    quotation_name=rec.name,
                    customer_name=rec.customer_id.name if rec.customer_id else 'Khách hàng',
                    meeting_link=rec.meet_url or 'Chưa có link họp',
                    quotation_value=rec.quotation_value,
                    quotation_date=rec.date,
                    line_items=line_items,
                )
            except Exception as e:
                _logger.exception('Lỗi gửi thông báo khi gửi báo giá %s: %s', rec.id, e)
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
        self.ensure_one()
        doc = self._get_linked_document()
        metadata = self.env['van_ban.document']._get_default_document_metadata(
            customer=self.customer_id,
            employee=self.customer_id.nhan_vien_phu_trach_id if self.customer_id else False,
            doc_type='bao_gia'
        )
        if not doc:
            doc_vals = {
                'name': f'Báo giá {self.name}',
                'doc_type': 'bao_gia',
                'customer_id': self.customer_id.id if self.customer_id else False,
                'related_quotation_id': self.id,
                'status': 'draft',
                'source_module': 'crm',
            }
            doc_vals.update(metadata)
            if self.file:
                doc_vals.update({
                    'file': self.file,
                    'file_name': self.file_name,
                    'date_upload': fields.Datetime.now(),
                })
            doc = self.env['van_ban.document'].create(doc_vals)
            if doc.file:
                try:
                    ocr_done = getattr(doc, 'ocr_status', None) == 'completed'
                except Exception:
                    ocr_done = False
                if not ocr_done:
                    try:
                        doc.action_scan_ocr()
                    except Exception:
                        _logger.exception('Không thể chạy OCR document báo giá %s sau khi tạo', self.id)
        else:
            updated_vals = {}
            updated_vals.update(metadata)
            if self.file and (not doc.file or doc.file != self.file or doc.file_name != self.file_name):
                updated_vals.update({
                    'file': self.file,
                    'file_name': self.file_name,
                    'date_upload': fields.Datetime.now(),
                })
            if updated_vals:
                try:
                    doc.write(updated_vals)
                except Exception:
                    _logger.exception('Không thể đồng bộ file báo giá vào document %s', doc.id)
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
                        'loai_van_ban_id': doc.loai_van_ban_id.id if doc.loai_van_ban_id else self.env['van_ban.document']._lookup_loai_van_ban('bao_gia'),
                        'trang_thai': 'moi'
                    })
                except Exception:
                    _logger.exception('Không thể tạo van_ban_den cho báo giá %s', self.id)
        else:
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
                        'loai_van_ban_id': doc.loai_van_ban_id.id if doc.loai_van_ban_id else self.env['van_ban.document']._lookup_loai_van_ban('bao_gia'),
                        'trang_thai': 'draft'
                    })
                except Exception:
                    _logger.exception('Không thể tạo van_ban_di cho báo giá %s', self.id)
        if self.status:
            try:
                status_mapping = {
                    'nhap': 'draft',
                    'da_gui': 'to_approve',
                    'da_xem': 'to_approve',
                    'dam_phan': 'to_approve',
                    'chap_nhan': 'approved',
                    'tu_choi': 'archived'
                }
                mapped_status = status_mapping.get(self.status, doc.status)
                if doc and doc.status != mapped_status:
                    doc.write({'status': mapped_status})
            except Exception:
                _logger.exception('Không thể đồng bộ trạng thái document báo giá %s', self.id)

    # NOTE: consolidated `write()` is defined earlier. Duplicate implementation removed.

    def action_accept_quotation(self):
        self.ensure_one()
        self.status = 'chap_nhan'
        self.customer_id.status = 'dam_phan'

        today = fields.Date.today()
        contract = self.env['qlkh.contract'].create({
            'name': f'HD-{self.name}',
            'customer_id': self.customer_id.id,
            'quotation_id': self.id,
            'contract_value': self.quotation_value,
            'date_start': today,
            'date_end': today + timedelta(days=365),
            'status': 'nhap',
        })
        # Nếu báo giá đã có document liên kết, liên kết nó với hợp đồng mới
        try:
            doc = self._get_linked_document()
            if doc and not doc.related_contract_id:
                doc.write({
                    'related_contract_id': contract.id,
                    'doc_type': 'hop_dong',
                    'loai_van_ban_id': self.env['van_ban.document']._lookup_loai_van_ban('hop_dong') or doc.loai_van_ban_id.id,
                })
            if doc and doc.file and doc.ocr_status != 'completed':
                try:
                    doc.action_scan_ocr()
                except Exception:
                    _logger.exception('Không thể chạy OCR document khi chấp nhận báo giá %s', self.id)
        except Exception:
            _logger.exception('Không thể liên kết document báo giá với hợp đồng %s', contract.id)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qlkh.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }
