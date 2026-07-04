import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DocDashboardController(http.Controller):
    @http.route('/dashboard/van_ban/data', auth='user', type='json')
    def get_document_dashboard_data(self, **kwargs):
        """Get Document dashboard data"""
        try:
            # Gọi Helper riêng của Văn bản
            helper = request.env['van_ban.dashboard.helper']
            data = helper.get_van_ban_dashboard_data()
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