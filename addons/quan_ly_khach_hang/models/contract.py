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
    iot_device = fields.Many2one(
        'qlkh.contract_product',
        string='Thiết bị IoT bảo trì'
    )
    available_iot_device_ids = fields.Many2many(
        'qlkh.contract_product',
        compute='_compute_available_iot_device_ids'
    )
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
    meeting_created = fields.Boolean('Đã tạo meeting gia hạn', default=False)

    document_count = fields.Integer(
        compute='_compute_document_count'
    )

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = self.env['van_ban.document'].search_count([
                ('related_contract_id', '=', rec.id)
            ])

    @api.depends('quotation_id.line_ids.product_id')
    def _compute_available_iot_device_ids(self):
        for rec in self:
            if rec.quotation_id:
                rec.available_iot_device_ids = rec.quotation_id.line_ids.mapped('product_id').ids
            else:
                rec.available_iot_device_ids = False

    @api.onchange('quotation_id')
    def _onchange_quotation_id(self):
        for rec in self:
            if rec.quotation_id and rec.iot_device and rec.iot_device not in rec.quotation_id.line_ids.mapped('product_id'):
                rec.iot_device = False

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
            
    @api.model
    def create(self, vals):
        contract = super().create(vals)
        
        # ========== TRIGGER 5: Meeting cho hợp đồng mới ==========
        if contract.customer_id and contract.status == 'nhap':
            contract._create_contract_meeting('new_contract')
        # ========== KẾT THÚC TRIGGER 5 ==========

        # Tự động tạo/đồng bộ document khi hợp đồng được tạo
        try:
            contract._create_linked_document_for_contract(contract)
        except Exception:
            _logger.exception('Không thể tạo document liên kết cho hợp đồng %s khi tạo', contract.id)
        
        return contract

    @api.model
    def _create_linked_document_for_contract(self, contract):
        try:
            doc = self.env['van_ban.document'].search([('related_contract_id', '=', contract.id)], limit=1)
            if not doc:
                metadata = self.env['van_ban.document']._get_default_document_metadata(
                    customer=contract.customer_id,
                    employee=contract.customer_id.nhan_vien_phu_trach_id if contract.customer_id else False,
                    doc_type='hop_dong'
                )
                status_mapping = {
                    'nhap': 'draft',
                    'cho_duyet': 'to_approve',
                    'da_duyet': 'approved',
                    'hieu_luc': 'approved',
                    'sap_het_han': 'approved',
                    'het_han': 'archived'
                }
                document_status = status_mapping.get(contract.status, 'draft')
                doc_vals = {
                    'name': f'Hợp đồng {contract.name}',
                    'doc_type': 'hop_dong',
                    'customer_id': contract.customer_id.id if contract.customer_id else False,
                    'related_contract_id': contract.id,
                    'source_module': 'crm',
                    'status': document_status,
                }
                if contract.file:
                    doc_vals.update({
                        'file': contract.file,
                        'file_name': contract.file_name,
                        'date_upload': fields.Datetime.now(),
                    })
                doc_vals.update(metadata)
                doc = self.env['van_ban.document'].create(doc_vals)
            else:
                update_vals = {}
                if doc.doc_type != 'hop_dong':
                    update_vals['doc_type'] = 'hop_dong'
                expected_name = f'Hợp đồng {contract.name}'
                if doc.name != expected_name:
                    update_vals['name'] = expected_name
                customer_id = contract.customer_id.id if contract.customer_id else False
                if (doc.customer_id.id if doc.customer_id else False) != customer_id:
                    update_vals['customer_id'] = customer_id
                if not doc.related_contract_id:
                    update_vals['related_contract_id'] = contract.id
                metadata = self.env['van_ban.document']._get_default_document_metadata(
                    customer=contract.customer_id,
                    employee=contract.customer_id.nhan_vien_phu_trach_id if contract.customer_id else False,
                    doc_type='hop_dong'
                )
                for key, value in metadata.items():
                    if value and not doc[key]:
                        update_vals[key] = value
                if update_vals:
                    doc.write(update_vals)
            if not self.env['van_ban_di'].search([('document_id', '=', doc.id)], limit=1):
                try:
                    self.env['van_ban_di'].create({
                        'document_id': doc.id,
                        'so_van_ban_di': doc.code or doc.name,
                        'so_hieu_van_ban': doc.code or doc.name,
                        'ten_van_ban': doc.name,
                        'customer_id': contract.customer_id.id if contract.customer_id else False,
                        'nhan_vien_tao_id': contract.customer_id.nhan_vien_phu_trach_id.id if contract.customer_id and contract.customer_id.nhan_vien_phu_trach_id else False,
                        'loai_van_ban_id': doc.loai_van_ban_id.id if doc.loai_van_ban_id else self.env['van_ban.document']._lookup_loai_van_ban('hop_dong'),
                        'trang_thai': 'draft'
                    })
                except Exception:
                    _logger.exception('Không thể tạo van_ban_di cho hợp đồng %s', contract.id)
        except Exception:
            _logger.exception('Lỗi khi tạo document cho hợp đồng %s', contract.id)

    def write(self, vals):
        old_status = {rec.id: rec.status for rec in self}
        result = super().write(vals)

        for rec in self:
            try:
                self._create_linked_document_for_contract(rec)
                doc = self.env['van_ban.document'].search([('related_contract_id', '=', rec.id)], limit=1)
                if doc:
                    metadata = self.env['van_ban.document']._get_default_document_metadata(
                        customer=rec.customer_id,
                        employee=rec.customer_id.nhan_vien_phu_trach_id if rec.customer_id else False,
                        doc_type='hop_dong'
                    )
                    update_vals = {}
                    expected_name = f'Hợp đồng {rec.name}'
                    if doc.name != expected_name:
                        update_vals['name'] = expected_name
                    if doc.doc_type != 'hop_dong':
                        update_vals['doc_type'] = 'hop_dong'
                    customer_id = rec.customer_id.id if rec.customer_id else False
                    if (doc.customer_id.id if doc.customer_id else False) != customer_id:
                        update_vals['customer_id'] = customer_id
                    if not doc.related_contract_id:
                        update_vals['related_contract_id'] = rec.id
                    for key, value in metadata.items():
                        if value and not doc[key]:
                            update_vals[key] = value
                    if update_vals:
                        doc.write(update_vals)
            except Exception:
                _logger.exception('Không thể đồng bộ metadata document cho hợp đồng %s', rec.id)

            if 'file' in vals or 'file_name' in vals:
                try:
                    self._create_linked_document_for_contract(rec)
                    doc = self.env['van_ban.document'].search([('related_contract_id', '=', rec.id)], limit=1)
                    if not doc:
                        continue
                    if rec.file and (not doc.file or doc.file != rec.file or doc.file_name != rec.file_name):
                        if doc.file:
                            try:
                                current_ver = doc.current_version or 'v1'
                                try:
                                    ver_num = int(current_ver.lstrip('v').strip())
                                except Exception:
                                    ver_num = 1
                                new_ver_no = f'v{ver_num + 1}'
                                self.env['van_ban.version'].create({
                                    'document_id': doc.id,
                                    'version_no': current_ver,
                                    'file': doc.file,
                                    'file_name': doc.file_name,
                                    'note': f'Phiên bản lưu tự động trước khi cập nhật từ hợp đồng {rec.name}'
                                })
                                doc.current_version = new_ver_no
                            except Exception:
                                _logger.exception('Không thể tạo phiên bản cho document %s trước khi ghi đè file', doc.id)
                        doc.write({
                            'file': rec.file,
                            'file_name': rec.file_name,
                            'date_upload': fields.Datetime.now(),
                        })
                except Exception:
                    _logger.exception('Không thể đồng bộ file hợp đồng lên document cho hợp đồng %s', rec.id)

            if 'status' in vals:
                try:
                    self._create_linked_document_for_contract(rec)
                    doc = self.env['van_ban.document'].search([('related_contract_id', '=', rec.id)], limit=1)
                    if doc:
                        mapping = {
                            'nhap': 'draft',
                            'cho_duyet': 'to_approve',
                            'da_duyet': 'approved',
                            'hieu_luc': 'approved',
                            'sap_het_han': 'approved',
                            'het_han': 'archived'
                        }
                        new_doc_status = mapping.get(rec.status, doc.status)
                        doc.write({'status': new_doc_status})
                        if rec.status == 'da_duyet':
                            try:
                                self.env['van_ban.approval'].create({
                                    'document_id': doc.id,
                                    'approver_id': rec.approved_by.id if hasattr(rec, 'approved_by') and rec.approved_by else False,
                                    'approver_user_id': self.env.uid,
                                    'status': 'approved',
                                    'comment': 'Auto-created from contract approval',
                                    'level': 1
                                })
                            except Exception:
                                _logger.exception('Không thể tạo lịch sử phê duyệt cho document %s', doc.id)
                except Exception:
                    _logger.exception('Lỗi khi sync document cho hợp đồng %s', rec.id)

        return result
    
    def action_submit(self):
        for rec in self:
            rec.status = 'cho_duyet'

    def _create_contract_meeting(self, meeting_type):
        """
        Tạo meeting liên quan đến hợp đồng
        
        Args:
            meeting_type: 'new_contract' hoặc 'expiring_contract'
        """
        if not self.customer_id or not self.customer_id.email:
            return None
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.google_helper import GoogleHelper
            from smart_biz_services.notif_helper import NotifHelper
            
            google = GoogleHelper()
            notif = NotifHelper()
            
            if meeting_type == 'new_contract':
                meeting_title = f"Bàn giao hợp đồng {self.name}"
                reason = f"Hợp đồng mới được tạo, giá trị: {self.contract_value:,.0f} VNĐ"
                duration = 45
            elif meeting_type == 'expiring_contract':
                days_left = (self.date_end - fields.Date.today()).days
                meeting_title = f"Gia hạn hợp đồng {self.name}"
                reason = f"Hợp đồng sắp hết hạn (còn {days_left} ngày)"
                duration = 30
            else:
                return None
            
            meeting_link = google.create_meeting(
                customer_email=self.customer_id.email,
                customer_name=self.customer_id.name,
                title=meeting_title,
                duration_minutes=duration
            )
            
            if meeting_link:
                # Gửi Telegram nội bộ
                notif.send_telegram_template(
                    'meeting_created',
                    customer_name=self.customer_id.name,
                    meeting_link=meeting_link,
                    reason=reason,
                    meeting_title=meeting_title
                )
                
                # Gửi Email cho khách hàng
                notif.send_email_template(
                    'meeting_invitation',
                    to_email=self.customer_id.email,
                    recipient_name=self.customer_id.name.split()[0] if self.customer_id.name else self.customer_id.name,
                    customer_name=self.customer_id.name,
                    meeting_link=meeting_link,
                    title=meeting_title,
                    reason=reason
                )
                
                _logger.info(f'Đã tạo meeting {meeting_type} cho hợp đồng {self.name}')
                return meeting_link
                
        except Exception as e:
            _logger.error(f'Lỗi tạo meeting cho hợp đồng {self.name}: {e}')
            return None
        
    def check_and_create_expiry_meeting(self):
        """
        Kiểm tra và tạo meeting cho hợp đồng sắp hết hạn (được gọi từ cron)
        """
        today = fields.Date.today()
        soon = today + timedelta(days=30)
        
        # Tìm hợp đồng sắp hết hạn (còn 30 ngày) và chưa có meeting
        contracts = self.search([
            ('date_end', '=', soon),
            ('status', '=', 'hieu_luc'),
            ('meeting_created', '=', False)  # Cần thêm field này
        ])
        
        for contract in contracts:
            contract._create_contract_meeting('expiring_contract')
            contract.write({'meeting_created': True})

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        """
        Override method get_view để kiểm tra hợp đồng sắp hết hạn khi mở tree view
        """
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        
        # Chỉ kiểm tra khi mở tree view (danh sách hợp đồng)
        if view_type == 'tree':
            # Sử dụng sudo để đảm bảo quyền truy cập
            self.sudo().check_and_create_expiry_meeting()
        
        return result
    
    def action_check_expiring(self):
        """Kiểm tra thủ công hợp đồng sắp hết hạn"""
        count = self.check_and_create_expiry_meeting()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Kết quả kiểm tra',
                'message': f'Đã tạo {count} meeting cho hợp đồng sắp hết hạn',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_approve(self):
        for rec in self:
            if rec.status == 'da_duyet':
                continue

            rec.status = 'da_duyet'

            document = self.env['van_ban.document'].search([
                ('related_contract_id', '=', rec.id)
            ], limit=1)

            if not document:
                document = self.env['van_ban.document'].create({
                    'name': f'Hồ sơ hợp đồng {rec.name}',
                    'doc_type': 'hop_dong',
                    'customer_id': rec.customer_id.id,
                    'related_contract_id': rec.id,
                    'status': 'approved',
                    'file': rec.file,
                    'file_name': rec.file_name,
                })
            else:
                try:
                    if document.status != 'approved':
                        document.write({'status': 'approved'})
                except Exception:
                    _logger.exception('Không thể cập nhật trạng thái document hợp đồng %s', document.id)

            if document and document.file:
                try:
                    ocr_done = getattr(document, 'ocr_status', None) == 'completed'
                except Exception:
                    ocr_done = False
                if not ocr_done:
                    try:
                        document.action_scan_ocr()
                    except Exception:
                        _logger.exception('OCR failed for document %s', document.id)

            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.ai_helper import AIHelper
                from smart_biz_services.notif_helper import NotifHelper

                ai = AIHelper()
                notif = NotifHelper()

                summary = ''
                text_to_summarize = rec.name
                if document and document.ocr_text:
                    text_to_summarize = document.ocr_text
                elif rec.file_name:
                    text_to_summarize = rec.name

                if text_to_summarize:
                    try:
                        summary = ai.summarize_document(text_to_summarize, max_length=200)
                    except Exception as e:
                        _logger.warning('Summarize contract failed: %s', e)
                        summary = f'Hợp đồng: {rec.name}'

                rec.ai_summary = summary
                rec.ai_processed_at = fields.Datetime.now()
                rec.ai_processed_by = self.env.user


                try:
                    notif.send_telegram_template(
                        'contract_approved',
                        contract_name=rec.name,
                        customer_name=rec.customer_id.name if rec.customer_id else 'N/A',
                        contract_value=rec.contract_value,
                        start_date=rec.date_start.strftime('%d/%m/%Y') if rec.date_start else 'N/A',
                        end_date=rec.date_end.strftime('%d/%m/%Y') if rec.date_end else 'N/A',
                        summary=summary or rec.ai_summary or 'Hợp đồng đã được phê duyệt theo đúng quy trình.'
                    )
                except Exception as e:
                    _logger.error('Gửi Telegram cho hợp đồng thất bại: %s', e, exc_info=True)

                if rec.customer_id and rec.customer_id.email:
                    try:
                        notif.send_email_template(
                            'contract_approved',
                            to_email=rec.customer_id.email,
                            recipient_name=rec.customer_id.name.split()[0] if rec.customer_id.name else rec.customer_id.name,
                            contract_name=rec.name,
                            customer_name=rec.customer_id.name,
                            contract_value=rec.contract_value,
                            start_date=rec.date_start.strftime('%d/%m/%Y') if rec.date_start else 'N/A',
                            end_date=rec.date_end.strftime('%d/%m/%Y') if rec.date_end else 'N/A',
                            summary=summary or rec.ai_summary or 'Hợp đồng đã được phê duyệt theo đúng quy trình.'
                        )
                    except Exception as e:
                        _logger.error('Gửi email khách hàng thất bại: %s', e, exc_info=True)

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