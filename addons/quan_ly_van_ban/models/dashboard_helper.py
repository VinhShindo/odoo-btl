import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class DocumentDashboardHelper(models.AbstractModel):
    _name = 'document.dashboard.helper'
    _description = 'Document Dashboard Helper'

    @api.model
    def get_document_dashboard_data(self):
        """Get Document dashboard statistics"""
        try:
            # Documents by type
            doc_by_type = {}
            loai_vbs = self.env['van_ban.loai_van_ban'].search([])
            for loai in loai_vbs:
                count = self.env['van_ban.document'].search_count([
                    ('loai_van_ban_id', '=', loai.id)
                ])
                if count > 0:
                    doc_by_type[loai.name] = count

            # Documents by status
            doc_status = {}
            for status in self.env['van_ban.document']._fields['status'].selection:
                count = self.env['van_ban.document'].search_count([('status', '=', status[0])])
                if count > 0:
                    doc_status[status[1]] = count

            # Documents incoming vs outgoing
            incoming = self.env['van_ban.van_ban_den'].search_count([])
            outgoing = self.env['van_ban.van_ban_di'].search_count([])

            # Total documents
            total_docs = self.env['van_ban.document'].search_count([])

            # Approved documents
            approved_docs = self.env['van_ban.document'].search_count([
                ('status', '=', 'da_duyet')
            ])
            approval_rate = (approved_docs / total_docs * 100) if total_docs > 0 else 0

            # Documents with AI summary
            ai_docs = self.env['van_ban.document'].search_count([
                ('ai_summary', '!=', False),
                ('ai_summary', '!=', '')
            ])

            # Recent documents
            recent_docs = self.env['van_ban.document'].search([], order='create_date desc', limit=5)
            recent_list = []
            for doc in recent_docs:
                recent_list.append({
                    'name': doc.name or 'N/A',
                    'status': dict(self.env['van_ban.document']._fields['status'].selection).get(doc.status, 'N/A'),
                    'created': doc.create_date.strftime('%d/%m/%Y') if doc.create_date else 'N/A'
                })

            return {
                'doc_by_type': doc_by_type,
                'doc_status': doc_status,
                'incoming': incoming,
                'outgoing': outgoing,
                'total_docs': total_docs,
                'approved_docs': approved_docs,
                'approval_rate': approval_rate,
                'ai_docs': ai_docs,
                'recent_docs': recent_list,
            }
        except Exception as e:
            _logger.error(f"Error in get_document_dashboard_data: {str(e)}")
            return {}
