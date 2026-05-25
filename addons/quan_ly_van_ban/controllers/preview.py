from odoo import http
from odoo.http import request
import base64


class VanBanPreviewController(http.Controller):
    @http.route('/van_ban/preview/<int:doc_id>', type='http', auth='user')
    def preview_pdf(self, doc_id, **kwargs):
        """Preview PDF trực tiếp from binary stored on record"""
        doc = request.env['van_ban.document'].sudo().browse(doc_id)
        if not doc or not doc.file:
            return request.not_found()
        # ensure filename
        fname = doc.file_name or f'document_{doc_id}.pdf'
        try:
            file_content = base64.b64decode(doc.file)
        except Exception:
            return request.not_found()

        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{fname}"'),
                ('Cache-Control', 'no-cache')
            ]
        )
