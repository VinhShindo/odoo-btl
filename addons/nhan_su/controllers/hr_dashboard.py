import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HRDashboardController(http.Controller):
    @http.route('/dashboard/hr/data', auth='user', type='json')
    def get_hr_dashboard_data(self, **kwargs):
        """Get HR dashboard data"""
        try:
            helper = request.env['hr.dashboard.helper']
            data = helper.get_hr_dashboard_data()
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
