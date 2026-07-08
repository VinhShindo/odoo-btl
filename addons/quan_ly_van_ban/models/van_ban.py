# models.py - Cập nhật hoàn chỉnh
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
import io
import os
import sys
from datetime import datetime
from urllib.parse import quote

_logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_bytes
    import PyPDF2
    PdfReader = getattr(PyPDF2, 'PdfReader', None) or getattr(PyPDF2, 'PdfFileReader', None)
    OCR_AVAILABLE = True
    _logger.info("OCR libraries loaded successfully")
except ImportError as e:
    OCR_AVAILABLE = False
    _logger.warning(f"OCR libraries not available: {e}")

class VanBan(models.Model):
    _name = 'van_ban.document'
    _description = 'Văn bản / Tài liệu liên quan đến khách hàng và nhân sự'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    # Basic Information
    name = fields.Char('Tiêu đề', required=True, tracking=True)
    code = fields.Char('Mã văn bản', readonly=True, copy=False, 
                       default=lambda self: _('New'))
    
    doc_type = fields.Selection([
        ('bao_gia', 'Báo giá'),
        ('hop_dong', 'Hợp đồng'),
        ('phu_luc', 'Phụ lục'),
        ('phap_ly', 'Hồ sơ pháp lý'),
        ('khac', 'Khác')
    ], string='Loại văn bản (tạm)', default='khac', required=True, tracking=True)

    loai_van_ban_id = fields.Many2one('loai_van_ban', string='Loại văn bản', tracking=True)
    
    # Relationships
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', tracking=True)
    folder_id = fields.Many2one('van_ban.folder', string='Thư mục', tracking=True)
    nhan_vien_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên chịu trách nhiệm',
        tracking=True,
        ondelete='set null'
    )
    related_contract_id = fields.Many2one('qlkh.contract', string='Hợp đồng liên quan')
    related_quotation_id = fields.Many2one('qlkh.quotation', string='Báo giá liên quan')
    
    # File Management
    file = fields.Binary('File', attachment=True)  # attachment=True giúp lưu riêng
    file_name = fields.Char('Tên file')
    file_size = fields.Integer('Kích thước file', compute='_compute_file_size', store=True)
    file_type = fields.Char('Loại file', compute='_compute_file_type', store=True)  
    
    # OCR Data
    ocr_text = fields.Text('Nội dung OCR', readonly=True, help='Văn bản được quét từ file')
    ocr_date = fields.Datetime('Ngày OCR', readonly=True)
    ocr_status = fields.Selection([
        ('not_started', 'Chưa OCR'),
        ('processing', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Thất bại')
    ], string='Trạng thái OCR', default='not_started', tracking=True)
    
    # Page Management for PDF
    total_pages = fields.Integer('Tổng số trang', compute='_compute_pages', store=True)
    current_page = fields.Integer('Trang hiện tại', default=1)
    page_images = fields.Text('Ảnh các trang', help='Base64 của các trang PDF')
    
    # Other fields
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments',
                                     domain=[('res_model', '=', 'van_ban.document')])
    status = fields.Selection([
        ('draft', 'Nháp'),
        ('to_approve', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('archived', 'Lưu trữ')
    ], string='Trạng thái', default='draft', tracking=True)
    date = fields.Date('Ngày tạo', default=fields.Date.context_today, tracking=True)
    date_upload = fields.Datetime('Ngày upload', default=fields.Datetime.now)
    note = fields.Text('Ghi chú')
    version_ids = fields.One2many(
        'van_ban.version',
        'document_id',
        string='Phiên bản'
    )
    
    current_version = fields.Char(
        string='Phiên bản hiện tại',
        default='v1',
        tracking=True
    )

    approval_ids = fields.One2many(
        'van_ban.approval',
        'document_id',
        string='Lịch sử phê duyệt'
    )

    van_ban_den_ids = fields.One2many(
        'van_ban_den',
        'document_id',
        string='Văn bản đến'
    )
    van_ban_di_ids = fields.One2many(
        'van_ban_di',
        'document_id',
        string='Văn bản đi'
    )

    routing_ids = fields.One2many(
        'van_ban.routing',
        'document_id',
        string='Luồng xử lý'
    )

    is_locked = fields.Boolean(
        string='Khóa chỉnh sửa',
        default=False
    )

    approved_date = fields.Datetime(
        string='Ngày duyệt'
    )

    approved_by = fields.Many2one(
        'hr.employee',
        string='Người duyệt'
    )
    ai_summary = fields.Text('Tóm tắt AI')
    ai_processed_at = fields.Datetime('Thời điểm xử lý AI')
    ai_processed_by = fields.Many2one('res.users', string='AI xử lý bởi')
    source_module = fields.Selection([
    ('crm', 'CRM'),
    ('hrm', 'HRM'),
    ('manual', 'Thủ công')
], default='manual')
    
    # Preview
    preview_url = fields.Char('URL xem trước', compute='_compute_preview_url')
    preview_html = fields.Html(string='Preview', compute='_compute_preview_html', sanitize=False, store=False,)

    @api.depends('file', 'file_name')
    def _compute_preview_html(self):
        for rec in self:
            if not rec.file:
                rec.preview_html = '<div class="alert alert-info">Chưa có file đính kèm.</div>'
                continue
            
            if not rec.id:
                rec.preview_html = '<div class="alert alert-warning">Vui lòng lưu bản ghi trước khi xem preview.</div>'
                continue
            
            # PDF
            if rec.file_type == 'pdf':
                url = f"/van_ban/preview/{rec.id}"
                rec.preview_html = f'''
                    <div class="text-center">
                        <iframe src="{url}" width="100%" height="700" style="border:1px solid #ccc; border-radius:5px;"></iframe>
                        <div class="text-muted mt-2"><i class="fa fa-file-pdf-o text-danger"/> PDF Document</div>
                        <div style="margin-top:10px"><a href="{url}" target="_blank" class="btn btn-secondary">Mở preview trong tab mới</a></div>
                    </div>'''
            
            # IMAGE
            elif rec.file_type in ['jpg', 'jpeg', 'png', 'bmp', 'gif']:
                url = f"/web/image/{rec._name}/{rec.id}/file"
                rec.preview_html = f'''
                    <div class="text-center">
                        <img src="{url}" style="max-width:100%; max-height:700px; border:1px solid #ccc; border-radius:5px;"/>
                    </div>'''
            
            # UNSUPPORTED
            else:
                rec.preview_html = f'<div class="alert alert-warning">Không hỗ trợ preview file loại: <b>{rec.file_type}</b></div>'
    
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('van_ban.document') or _('New')
        document = super(VanBan, self).create(vals)
        try:
            document._ensure_initial_routing()
        except Exception:
            _logger.exception('Không thể tạo luồng xử lý văn bản cho document %s', document.id)

        if document.status == 'approved':
            try:
                super(VanBan, document).write({
                    'approved_date': fields.Datetime.now(),
                    'is_locked': True,
                    'approved_by': document.approved_by.id if document.approved_by else False,
                })
            except Exception:
                _logger.exception('Không thể cập nhật thông tin duyệt cho document %s', document.id)
            try:
                if not document.approval_ids.filtered(lambda a: a.status == 'approved'):
                    self.env['van_ban.approval'].create({
                        'document_id': document.id,
                        'approver_id': document.approved_by.id if document.approved_by else False,
                        'approver_user_id': self.env.uid,
                        'status': 'approved',
                        'comment': 'Tạo tự động khi document được tạo ở trạng thái approved',
                        'level': 1,
                    })
            except Exception:
                _logger.exception('Không thể tạo lịch sử phê duyệt cho document %s khi create', document.id)
            try:
                document._on_document_approved()
            except Exception:
                _logger.exception('Không thể thực thi _on_document_approved cho document %s khi create', document.id)
        return document
    
    def _ensure_initial_routing(self):
        self.ensure_one()
        if self.routing_ids:
            return
        assigned_to = self.nhan_vien_id.id if self.nhan_vien_id else False
        if not assigned_to and self.customer_id and getattr(self.customer_id, 'nhan_vien_phu_trach_id', False):
            assigned_to = self.customer_id.nhan_vien_phu_trach_id.id
        self.env['van_ban.routing'].create({
            'name': f'Quy trình xử lý văn bản {self.name}',
            'document_id': self.id,
            'assigned_to': assigned_to,
            'stage': 'to_process',
            'note': 'Tự động tạo luồng xử lý khi khởi tạo văn bản.',
        })

    def _update_routing_stage_from_status(self, status):
        self.ensure_one()
        if not self.routing_ids:
            self._ensure_initial_routing()
        if status == 'to_approve':
            self.routing_ids.write({'stage': 'to_process'})
        elif status == 'approved':
            self.routing_ids.write({'stage': 'done'})
        elif status == 'archived':
            self.routing_ids.write({'stage': 'done'})
    
    def write(self, vals):
        # Store old status before write
        old_status = {rec.id: rec.status for rec in self}

        for rec in self:

            if rec.is_locked:

                blocked_fields = {
                    'file',
                    'name',
                    'doc_type'
                }

                if blocked_fields.intersection(vals.keys()):
                    raise UserError(
                        'Văn bản đã duyệt, không được chỉnh sửa.'
                    )

        result = super().write(vals)

        if 'status' in vals:
            for rec in self:
                try:
                    rec._update_routing_stage_from_status(vals['status'])
                except Exception:
                    _logger.exception('Không thể đồng bộ routing cho document %s khi đổi status', rec.id)

        # NEW: Handle document approval - summarize, notify, and create approval record
        if 'status' in vals and vals['status'] == 'approved':
            for rec in self:
                if old_status.get(rec.id) != 'approved':
                    try:
                        rec.write({
                            'approved_date': fields.Datetime.now(),
                            'is_locked': True,
                        })
                    except Exception:
                        _logger.exception('Không thể cập nhật ngày duyệt cho document %s', rec.id)
                    try:
                        if not rec.approval_ids.filtered(lambda a: a.status == 'approved'):
                            self.env['van_ban.approval'].create({
                                'document_id': rec.id,
                                'approver_id': rec.approved_by.id if rec.approved_by else False,
                                'approver_user_id': self.env.uid,
                                'status': 'approved',
                                'comment': 'Phê duyệt tự động khi chuyển trạng thái sang approved',
                                'level': 1,
                            })
                    except Exception:
                        _logger.exception('Không thể tạo lịch sử phê duyệt cho document %s', rec.id)
                    try:
                        rec._on_document_approved()
                    except Exception as e:
                        _logger.exception('Lỗi trong _on_document_approved cho document %s: %s', rec.id, e)

        return result

    def _on_document_approved(self):
        """Khi văn bản được phê duyệt: tóm tắt + gửi thông báo"""
        self.ensure_one()

        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.ai_helper import AIHelper
            from smart_biz_services.notif_helper import NotifHelper

            ai = AIHelper()
            notif = NotifHelper()

            summary = ''
            if self.ocr_text:
                try:
                    summary = ai.summarize_document(self.ocr_text, max_length=200)
                except Exception as e:
                    _logger.warning('Summarize document failed: %s', e)

            if not summary and self.ocr_text:
                summary = self.ocr_text

            self.ai_summary = summary
            self.ai_processed_at = fields.Datetime.now()
            self.ai_processed_by = self.env.user

            doc_type_label = dict(self._fields['doc_type'].selection).get(self.doc_type, self.doc_type)
            notification_content = (
                f"Văn bản phê duyệt: {self.name}\n"
                f"Loại: {doc_type_label}\n"
                f"Khách hàng: {self.customer_id.name if self.customer_id else 'N/A'}\n"
                f"Tóm tắt: {summary or 'Xem chi tiết tại hệ thống'}"
            )

            try:
                notif.send_telegram_template(
                    'document_approved',
                    doc_name=self.name,
                    doc_type=doc_type_label,
                    customer_name=self.customer_id.name if self.customer_id else None,
                    summary=summary or self.ai_summary or 'Văn bản đã được phê duyệt.',
                    full_text=self.ocr_text
                )
            except Exception as e:
                _logger.error('Gửi Telegram cho văn bản thất bại: %s', e, exc_info=True)

            if self.customer_id and self.customer_id.email:
                try:
                    notif.send_email_template(
                        'document_approved',  # Cần thêm template này trong EmailTemplates
                        to_email=self.customer_id.email,
                        recipient_name=self.customer_id.name.split()[0] if self.customer_id.name else self.customer_id.name,
                        doc_name=self.name,
                        doc_type=doc_type_label,
                        customer_name=self.customer_id.name,
                        summary=summary or self.ai_summary or 'Văn bản đã được phê duyệt.'
                    )
                except Exception as e:
                    _logger.error('Gửi email khách hàng thất bại: %s', e, exc_info=True)

        except Exception as e:
            _logger.error('Lỗi trong _on_document_approved: %s', e, exc_info=True)
    
    @api.depends('file')
    def _compute_file_size(self):
        for record in self:
            if record.file:
                import base64
                decoded = base64.b64decode(record.file)
                record.file_size = len(decoded)  # Kích thước bytes
            else:
                record.file_size = 0
    
    @api.depends('file_name')
    def _compute_file_type(self):
        for record in self:
            if record.file_name and '.' in record.file_name:
                ext = record.file_name.split('.')[-1].lower()
                record.file_type = ext
            else:
                record.file_type = ''
    
    @api.depends('file', 'file_name')
    def _compute_pages(self):
        for record in self:
            record.total_pages = 0
            if record.file and record.file_name and record.file_name.lower().endswith('.pdf'):
                try:
                    pdf_data = base64.b64decode(record.file)
                    pdf_reader = PdfReader(io.BytesIO(pdf_data))
                    record.total_pages = len(pdf_reader.pages)
                    _logger.info(f"PDF {record.file_name} has {record.total_pages} pages")
                except Exception as e:
                    _logger.error(f"Error reading PDF pages for {record.file_name}: {str(e)}")
                    record.total_pages = 0

    # Thêm method này vào class VanBan
    def _get_preview_url(self):
        """Lấy URL preview cho file"""
        self.ensure_one()
        return f'/van_ban/preview/{self.id}' if self.file and self.file_name else False
    

    @api.depends('file', 'file_name')
    def _compute_preview_url(self):
        for record in self:
            _logger.info(f"Computing preview URL for record {record.id} with file_name: {record.file_name}")
            if record.file and record.file_name:
                _logger.info(f"Record {record.id} has file, attempting to set preview URL")
                try:
                    record.preview_url = f'/van_ban/preview/{record.id}'
                    _logger.info(f"Preview URL set to: {record.preview_url}")
                except Exception:
                    record.preview_url = f'/web/content/van_ban.document/{record.id}/file/{record.file_name}?download=false'
            else:
                record.preview_url = False

    @api.model
    def _lookup_loai_van_ban(self, doc_type):
        if not doc_type:
            return False
        mapping = {
            'bao_gia': ['BÁO GIÁ', 'BAO GIA', 'BG'],
            'hop_dong': ['HỢP ĐỒNG', 'HOP DONG', 'HD'],
            'phu_luc': ['PHỤ LỤC', 'PHU LUC', 'PL'],
            'phap_ly': ['PHÁP LÝ', 'PHAP LY'],
            'khac': ['KHÁC', 'KHAC'],
        }
        candidates = mapping.get(doc_type, [doc_type])
        for candidate in candidates:
            loai = self.env['loai_van_ban'].search([
                '|',
                ('ma_loai_van_ban', 'ilike', candidate),
                ('ten_loai_van_ban', 'ilike', candidate)
            ], limit=1)
            if loai:
                return loai.id
        return False

    @api.model
    def _get_default_document_metadata(self, customer=None, employee=None, doc_type=None):
        result = {}
        if not employee and customer:
            employee = getattr(customer, 'nhan_vien_phu_trach_id', False)
        if employee:
            result['nhan_vien_id'] = employee.id
            if employee.folder_id:
                result['folder_id'] = employee.folder_id.id
            else:
                try:
                    employee._create_employee_folder()
                    if employee.folder_id:
                        result['folder_id'] = employee.folder_id.id
                except Exception:
                    _logger.exception('Không thể tạo folder nhân viên cho document: %s', employee.id)
        if customer and not result.get('folder_id'):
            customer_root = self.env['van_ban.folder'].search([
                ('name', '=', 'Khách hàng'),
                ('parent_id', '=', False)
            ], limit=1)
            if customer_root:
                folder = self.env['van_ban.folder'].search([
                    ('parent_id', '=', customer_root.id),
                    ('name', '=', customer.name)
                ], limit=1)
                if not folder:
                    try:
                        folder = self.env['van_ban.folder'].create({
                            'name': customer.name,
                            'parent_id': customer_root.id,
                            'folder_type': 'customer'
                        })
                    except Exception:
                        folder = False
                if folder:
                    result['folder_id'] = folder.id
        if doc_type and not result.get('loai_van_ban_id'):
            loai_id = self._lookup_loai_van_ban(doc_type)
            if loai_id:
                result['loai_van_ban_id'] = loai_id
        return result

    def action_scan_ocr(self):
        """Quét OCR cho file (hỗ trợ PDF và ảnh)"""
        self.ensure_one()

        if not OCR_AVAILABLE:
            raise UserError(_('Chưa cài đặt thư viện OCR. Vui lòng liên hệ quản trị viên.'))

        if not self.file:
            raise UserError(_('Chưa có file nào được tải lên. Vui lòng upload file trước.'))

        # If the record is not yet saved, create it so OCR results persist immediately.
        target = self
        if not self.id:
            create_vals = {
                'file': self.file,
                'file_name': self.file_name or (self.name or 'uploaded.pdf'),
                'name': self.name or (self.file_name or 'New Document'),
                'doc_type': self.doc_type or 'khac',
                'ocr_status': 'processing',
            }
            target = self.sudo().create(create_vals)
        else:
            target.sudo().write({'ocr_status': 'processing'})

        try:
            # Decode file
            file_data = base64.b64decode(target.file)

            # Kiểm tra loại file
            if target.file_name and target.file_name.lower().endswith('.pdf'):
                # Xử lý PDF
                ocr_texts = target._ocr_pdf(file_data)
                full_text = '\n\n--- Trang ---\n\n'.join(ocr_texts)
            else:
                # Xử lý ảnh
                full_text = target._ocr_image(file_data)

            target.sudo().write({
                'ocr_text': full_text,
                'ocr_date': fields.Datetime.now(),
                'ocr_status': 'completed'
            })

            # Sau khi OCR hoàn tất, gọi AI để tóm tắt và gửi thông báo
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.ai_helper import AIHelper
                from smart_biz_services.notif_helper import NotifHelper

                ai = AIHelper()
                notif = NotifHelper()

                summary = ''
                if full_text:
                    try:
                        summary = ai.summarize_document(full_text, max_length=300)
                    except Exception as e:
                        _logger.warning('AI summarization failed after OCR: %s', e)

                if not summary:
                    summary = full_text or ''

                # Lưu thông tin tóm tắt
                try:
                    target.sudo().write({
                        'ai_summary': summary,
                        'ai_processed_at': fields.Datetime.now(),
                        'ai_processed_by': self.env.user.id,
                    })
                except Exception:
                    _logger.exception('Không thể lưu thông tin AI summary cho document %s', target.id)

                # Gửi Telegram nội bộ
                try:
                    notif.send_telegram_template(
                        'document_approved',
                        doc_name=target.name,
                        doc_type=dict(target._fields['doc_type'].selection).get(target.doc_type, target.doc_type),
                        customer_name=target.customer_id.name if target.customer_id else None,
                        summary=summary,
                        full_text=full_text
                    )
                except Exception as e:
                    _logger.exception('Gửi Telegram sau OCR thất bại: %s', e)

                # Gửi Email cho khách hàng nếu có email
                if target.customer_id and getattr(target.customer_id, 'email', False):
                    try:
                        notif.send_email_template(
                            'document_approved',
                            to_email=target.customer_id.email,
                            recipient_name=target.customer_id.name.split()[0] if target.customer_id.name else target.customer_id.name,
                            doc_name=target.name,
                            doc_type=dict(target._fields['doc_type'].selection).get(target.doc_type, target.doc_type),
                            customer_name=target.customer_id.name,
                            summary=summary,
                            full_text=full_text
                        )
                    except Exception as e:
                        _logger.exception('Gửi email sau OCR thất bại: %s', e)
            except Exception as e:
                _logger.exception('Lỗi khi xử lý AI/notify sau OCR: %s', e)

            # Mở lại form của bản ghi đã được lưu để hiển thị đúng nội dung OCR và preview PDF.
            return {
                'type': 'ir.actions.act_window',
                'name': _('Văn bản'),
                'res_model': 'van_ban.document',
                'view_mode': 'form',
                'res_id': target.id,
                'views': [(self.env.ref('quan_ly_van_ban.view_van_ban_form').id, 'form')],
                'target': 'current',
                'context': {'form_view_initial_mode': 'edit'},
            }

        except Exception as e:
            _logger.error(f"OCR Error: {str(e)}")
            target.sudo().write({'ocr_status': 'failed'})
            raise UserError(_(f'Lỗi khi quét OCR: {str(e)}'))
        
    def action_view_ocr(self):
        """Hiển thị popup chứa nội dung OCR"""
        self.ensure_one()
        
        if not self.ocr_text:
            raise UserError(_('Chưa có nội dung OCR!'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Nội dung OCR - {self.name}',
            'res_model': 'van_ban.document',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def _ocr_pdf(self, pdf_data):
        """Quét OCR cho file PDF"""
        texts = []
        
        try:
            # Chuyển PDF thành ảnh
            images = convert_from_bytes(pdf_data, dpi=300)
            
            for i, image in enumerate(images):
                _logger.info(f"Processing page {i+1}/{len(images)}")
                
                # Tiền xử lý ảnh
                image = image.convert('L')  # Chuyển sang grayscale
                
                # OCR với tiếng Việt
                text = pytesseract.image_to_string(image, lang='vie+eng')
                texts.append(f"=== Trang {i+1} ===\n{text}")
                
        except Exception as e:
            _logger.error(f"PDF OCR error: {e}")
            raise
        
        return texts
    
    def _ocr_image(self, image_data):
        """Quét OCR cho file ảnh"""
        try:
            image = Image.open(io.BytesIO(image_data))
            # Tiền xử lý
            image = image.convert('L')  # Grayscale
            # Tăng độ phân giải
            width, height = image.size
            if width < 1000:
                image = image.resize((width*2, height*2), Image.Resampling.LANCZOS)
            
            # OCR với tiếng Việt
            text = pytesseract.image_to_string(image, lang='vie+eng')
            return text
            
        except Exception as e:
            _logger.error(f"Image OCR error: {e}")
            raise
    
    def action_generate_pdf_preview(self):
        """Tạo preview cho PDF"""
        self.ensure_one()
        
        if not self.file or not self.file_name.lower().endswith('.pdf'):
            return False
        
        try:
            pdf_data = base64.b64decode(self.file)
            images = convert_from_bytes(pdf_data, dpi=150, first_page=self.current_page, last_page=self.current_page)
            
            if images:
                # Chuyển ảnh thành base64
                img_buffer = io.BytesIO()
                images[0].save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Preview'),
                        'message': _('Đã tạo preview cho trang %d') % self.current_page,
                        'type': 'info',
                        'sticky': False,
                    }
                }
        except Exception as e:
            _logger.error(f"Preview error: {e}")
        
        return False
    
    def action_download_ocr_text(self):
        """Tải file OCR text"""
        self.ensure_one()
        
        if not self.ocr_text:
            raise UserError(_('Chưa có nội dung OCR. Vui lòng chạy OCR trước.'))
        
        # Tạo file text
        content = f"""
        ===================================
        THÔNG TIN VĂN BẢN
        ===================================
        Mã: {self.code}
        Tiêu đề: {self.name}
        Loại: {self.loai_van_ban_id.ten_loai_van_ban if self.loai_van_ban_id else dict(self._fields['doc_type'].selection).get(self.doc_type)}
        Ngày tạo: {self.date}
        
        ===================================
        NỘI DUNG OCR
        ===================================
        {self.ocr_text}
        """
        
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.code}_ocr_{datetime.now().strftime("%Y%m%d")}.txt',
            'datas': base64.b64encode(content.encode('utf-8')),
            'res_model': 'van_ban.document',
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class QlkhCustomer(models.Model):
    _inherit = 'qlkh.customer'

    van_ban_ids = fields.One2many(
        'van_ban.document',
        'customer_id',
        string='Văn bản'
    )


class QlkhContract(models.Model):
    _inherit = 'qlkh.contract'

    van_ban_ids = fields.One2many(
        'van_ban.document',
        'related_contract_id',
        string='Văn bản liên quan'
    )