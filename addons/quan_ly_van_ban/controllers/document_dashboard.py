import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DocumentDashboardController(http.Controller):
    @http.route('/dashboard/document/data', auth='user', type='json')
    def get_document_dashboard_data(self, **kwargs):
        """Get Document dashboard data"""
        try:
            helper = request.env['document.dashboard.helper']
            data = helper.get_document_dashboard_data()
            return {
                'status': 'success',
                'data': data
            }
        except Exception as e:
            _logger.error(f"Error fetching document dashboard data: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
