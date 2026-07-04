import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HRDashboardController(http.Controller):
    @http.route('/dashboard/nhan_su/data', auth='user', type='json')
    def get_hr_dashboard_data(self, **kwargs):
        """Get HR dashboard data"""
        try:
            # Gọi Helper riêng của Nhân sự
            helper = request.env['nhan_su.dashboard.helper']
            data = helper.get_nhan_su_dashboard_data()
            return {
                'status': 'success',
                'data': data
            }
        except Exception as e:
            _logger.error(f"Error fetching HR dashboard data: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }