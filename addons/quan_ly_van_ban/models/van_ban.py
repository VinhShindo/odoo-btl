# models.py - Cập nhật hoàn chỉnh
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
import io
from datetime import datetime

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
    ], string='Loại văn bản', default='khac', required=True, tracking=True)
    
    # Relationships
    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', tracking=True)
    folder_id = fields.Many2one('van_ban.folder', string='Thư mục', tracking=True)
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên chịu trách nhiệm', tracking=True)
    related_contract_id = fields.Many2one('qlkh.contract', string='Hợp đồng liên quan')
    related_quotation_id = fields.Many2one('qlkh.quotation', string='Báo giá liên quan')
    
    # File Management
    file = fields.Binary('File', attachment=True)  # attachment=True giúp lưu riêng
    file_name = fields.Char('Tên file')
    file_size = fields.Integer('Kích thước file', compute='_compute_file_size', store=False)
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
    
    # Preview
    preview_url = fields.Char('URL xem trước', compute='_compute_preview_url')
    
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('van_ban.document') or _('New')
        return super(VanBan, self).create(vals)
    
    @api.depends('file')
    def _compute_file_size(self):
        for record in self:
            if record.file:
                record.file_size = len(record.file) * 3 / 4  # Xấp xỉ dung lượng
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

    @api.depends('file')
    def _compute_preview_url(self):
        for record in self:
            record.preview_url = f'/van_ban/preview/{record.id}' if record.file and record.file_name else False
    
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
            }
            target = self.sudo().create(create_vals)

        target.ocr_status = 'processing'

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

            # Nếu chúng ta đã tạo một bản ghi mới, mở form của bản ghi đó để người dùng thấy kết quả
            return {
                'type': 'ir.actions.act_window',
                'name': _('Văn bản'),
                'res_model': 'van_ban.document',
                'view_mode': 'form',
                'res_id': target.id,
                'target': 'current',
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
        Loại: {dict(self._fields['doc_type'].selection).get(self.doc_type)}
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