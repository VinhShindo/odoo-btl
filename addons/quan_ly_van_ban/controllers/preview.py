from odoo import http
from odoo.http import request
import base64
from urllib.parse import quote
import logging

class VanBanPreviewController(http.Controller):
    @http.route('/van_ban/preview/<int:doc_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def preview_pdf(self, doc_id, **kwargs):
        """Preview PDF trực tiếp from binary stored on record"""
        # _logger = logging.getLogger(__name__)
    
        # _logger.info(f"Preview called for doc_id: {doc_id}")
        
        # doc = request.env['van_ban.document'].sudo().browse(doc_id)
        
        # _logger.info(f"Document found: {doc and doc.id}")
        # _logger.info(f"Has file: {doc and bool(doc.file)}")
        # _logger.info(f"File name: {doc and doc.file_name}")

        doc = request.env['van_ban.document'].sudo().browse(doc_id)
        if not doc or not doc.file:
            return request.not_found()
        
        try:
            file_content = base64.b64decode(doc.file)
        except Exception as e:
            return request.not_found()

        fname = doc.file_name or f'document_{doc_id}.pdf'
        
        # Xác định Content-Type dựa trên loại file
        content_type = 'application/pdf'
        if fname.lower().endswith('.jpg') or fname.lower().endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif fname.lower().endswith('.png'):
            content_type = 'image/png'
        elif fname.lower().endswith('.gif'):
            content_type = 'image/gif'
        
        headers = [
            ('Content-Type', content_type),
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
            ('Pragma', 'no-cache'),
            ('Expires', '0')
        ]
        
        try:
            fname_utf8 = quote(fname)
            headers.append(('Content-Disposition', f"inline; filename*=UTF-8''{fname_utf8}"))
        except Exception:
            headers.append(('Content-Disposition', 'inline'))

        return request.make_response(
            file_content,
            headers=headers,
        )
    
    @http.route('/van_ban/preview_thumbnail/<int:doc_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def preview_thumbnail(self, doc_id, **kwargs):
        """Preview thumbnail cho file ảnh"""
        doc = request.env['van_ban.document'].sudo().browse(doc_id)
        if not doc or not doc.file:
            return request.not_found()
        
        try:
            from PIL import Image
            import io
            
            file_content = base64.b64decode(doc.file)
            image = Image.open(io.BytesIO(file_content))
            
            # Tạo thumbnail
            image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Chuyển về base64
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_base64 = img_buffer.getvalue()
            
            headers = [
                ('Content-Type', 'image/png'),
                ('Cache-Control', 'no-cache')
            ]
            
            return request.make_response(img_base64, headers=headers)
            
        except Exception as e:
            return request.not_found()