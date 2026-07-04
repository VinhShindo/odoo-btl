import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class VanBanDashboardHelper(models.AbstractModel):
    _name = 'van_ban.dashboard.helper'
    _description = 'Van Ban Dashboard Helper'

    @api.model
    def get_van_ban_dashboard_data(self):
        """Get Document dashboard statistics"""
        try:
            # 1. Tổng số & Phê duyệt
            total_docs = self.env['van_ban.document'].search_count([])
            approved_docs = self.env['van_ban.document'].search_count([('status', '=', 'approved')])
            pending_docs = self.env['van_ban.document'].search_count([('status', '=', 'to_approve')])
            draft_docs = self.env['van_ban.document'].search_count([('status', '=', 'draft')])
            archived_docs = self.env['van_ban.document'].search_count([('status', '=', 'archived')])
            approval_rate = (approved_docs / total_docs * 100) if total_docs > 0 else 0

            # 2. Văn bản đến & đi (Đã sửa đúng tên model: bỏ "van_ban.")
            incoming = self.env['van_ban_den'].search_count([])
            outgoing = self.env['van_ban_di'].search_count([])

            # 3. OCR & AI
            ocr_completed = self.env['van_ban.document'].search_count([('ocr_status', '=', 'completed')])
            ocr_pending = self.env['van_ban.document'].search_count([('ocr_status', 'in', ['not_started', 'processing'])])
            ai_docs = self.env['van_ban.document'].search_count([('ai_summary', '!=', False), ('ai_summary', '!=', '')])

            # 4. Loại văn bản
            loai_vbs = self.env['loai_van_ban'].sudo().search_read([], ['ten_loai_van_ban', 'id'])
            
            doc_by_type = {}
            for loai in loai_vbs:
                count = self.env['van_ban.document'].search_count([
                    ('loai_van_ban_id', '=', loai['id'])
                ])
                if count > 0:
                    doc_by_type[loai['ten_loai_van_ban']] = count

            # 5. Trạng thái văn bản
            status_labels = dict(self.env['van_ban.document']._fields['status'].selection)
            doc_status = {}
            for status_key, status_label in status_labels.items():
                count = self.env['van_ban.document'].search_count([('status', '=', status_key)])
                if count > 0:
                    doc_status[status_label] = count

            # 6. Văn bản gần đây
            recent_docs = self.env['van_ban.document'].search([], order='create_date desc', limit=5)
            recent_list = []
            doc_type_labels = dict(self.env['van_ban.document']._fields['doc_type'].selection)
            for doc in recent_docs:
                recent_list.append({
                    'name': doc.name or 'N/A',
                    'status': status_labels.get(doc.status, 'N/A'),
                    'created': doc.create_date.strftime('%d/%m/%Y') if doc.create_date else 'N/A',
                    'doc_type': doc_type_labels.get(doc.doc_type, 'N/A'),
                    'responsible': doc.nhan_vien_id.name or 'N/A'
                })

            return {
                'doc_by_type': doc_by_type,
                'doc_status': doc_status,
                'incoming': incoming,
                'outgoing': outgoing,
                'total_docs': total_docs,
                'approved_docs': approved_docs,
                'pending_docs': pending_docs,
                'draft_docs': draft_docs,
                'archived_docs': archived_docs,
                'approval_rate': approval_rate,
                'ocr_completed': ocr_completed,
                'ocr_pending': ocr_pending,
                'ai_docs': ai_docs,
                'recent_docs': recent_list,
            }
        except Exception as e:
            _logger.error(f"Error in get_van_ban_dashboard_data: {str(e)}", exc_info=True)
            return {}