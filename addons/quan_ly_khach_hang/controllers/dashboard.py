import logging
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DashboardController(http.Controller):
    @http.route('/dashboard/crm/data', auth='user', type='json')
    def get_crm_dashboard_data(self, **kwargs):
        """Get CRM dashboard data"""
        try:
            helper = request.env['dashboard.helper']
            data = helper.get_crm_dashboard_data()
            return {
                'status': 'success',
                'data': data
            }
        except Exception as e:
            _logger.error(f"Error fetching CRM dashboard data: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/dashboard/document/data', auth='user', type='json')
    def get_document_dashboard_data(self, **kwargs):
        """Get Document dashboard data"""
        try:
            helper = request.env['dashboard.helper']
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

    @http.route('/dashboard/hr/data', auth='user', type='json')
    def get_hr_dashboard_data(self, **kwargs):
        """Get HR dashboard data"""
        try:
            helper = request.env['dashboard.helper']
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
