import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class DashboardHelper(models.AbstractModel):
    _name = 'dashboard.helper'
    _description = 'Dashboard Helper - Abstract model for statistics'

    @api.model
    def get_crm_dashboard_data(self):
        """Get CRM dashboard statistics"""
        try:
            # Total customers by status
            customer_status = {}
            status_choices = dict(self.env['qlkh.customer']._fields['status'].selection)
            for status in status_choices:
                count = self.env['qlkh.customer'].search_count([('status', '=', status)])
                if count > 0:
                    customer_status[status_choices[status]] = count

            # Total customers
            total_customers = self.env['qlkh.customer'].search_count([])

            # Revenue metrics
            total_expected_revenue = sum(
                self.env['qlkh.customer'].search([]).mapped('expected_revenue')
            )

            # Quotations by status
            quotation_status = {}
            for status in self.env['qlkh.quotation']._fields['status'].selection:
                count = self.env['qlkh.quotation'].search_count([('status', '=', status[0])])
                if count > 0:
                    quotation_status[status[1]] = count

            # Contracts by status
            contract_status = {}
            for status in self.env['qlkh.contract']._fields['status'].selection:
                count = self.env['qlkh.contract'].search_count([('status', '=', status[0])])
                if count > 0:
                    contract_status[status[1]] = count

            # Total contracts value
            total_contracts_value = sum(
                self.env['qlkh.contract'].search([
                    ('status', 'in', ['da_duyet', 'hieu_luc', 'sap_het_han'])
                ]).mapped('contract_value')
            )

            # Revenue by customer type
            revenue_by_type = {}
            for ctype in self.env['qlkh.customer']._fields['customer_type'].selection:
                customers = self.env['qlkh.customer'].search([('customer_type', '=', ctype[0])])
                revenue = sum(customers.mapped('expected_revenue'))
                if revenue > 0:
                    revenue_by_type[ctype[1]] = revenue

            # Top 5 customers by revenue
            top_customers = []
            customers = self.env['qlkh.customer'].search([
                ('expected_revenue', '>', 0)
            ], order='expected_revenue desc', limit=5)
            for cust in customers:
                top_customers.append({
                    'name': cust.name,
                    'revenue': cust.expected_revenue
                })

            # Quotation count by customer
            quotation_count = len(self.env['qlkh.quotation'].search([]))
            accepted_quotations = len(self.env['qlkh.quotation'].search([
                ('status', '=', 'chap_nhan')
            ]))
            conversion_rate = (accepted_quotations / quotation_count * 100) if quotation_count > 0 else 0

            return {
                'customer_status': customer_status,
                'total_customers': total_customers,
                'total_expected_revenue': total_expected_revenue,
                'quotation_status': quotation_status,
                'contract_status': contract_status,
                'total_contracts_value': total_contracts_value,
                'revenue_by_type': revenue_by_type,
                'top_customers': top_customers,
                'quotation_count': quotation_count,
                'accepted_quotations': accepted_quotations,
                'conversion_rate': conversion_rate,
            }
        except Exception as e:
            _logger.error(f"Error in get_crm_dashboard_data: {str(e)}")
            return {}

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

            # Approval rate
            total_docs = self.env['van_ban.document'].search_count([])
            approved_docs = self.env['van_ban.document'].search_count([
                ('status', '=', 'da_duyet')
            ])
            approval_rate = (approved_docs / total_docs * 100) if total_docs > 0 else 0

            # Documents with OCR
            ocr_docs = self.env['van_ban.document'].search_count([
                ('ocr_text', '!=', False),
                ('ocr_text', '!=', '')
            ])

            # Routing distribution
            routing_dist = {}
            routings = self.env['van_ban.routing'].search([])
            for routing in routings:
                count = self.env['van_ban.document'].search_count([
                    ('routing_id', '=', routing.id)
                ])
                if count > 0:
                    routing_dist[routing.name] = count

            return {
                'doc_by_type': doc_by_type,
                'doc_status': doc_status,
                'incoming': incoming,
                'outgoing': outgoing,
                'total_docs': total_docs,
                'approved_docs': approved_docs,
                'approval_rate': approval_rate,
                'ocr_docs': ocr_docs,
                'routing_dist': routing_dist,
            }
        except Exception as e:
            _logger.error(f"Error in get_document_dashboard_data: {str(e)}")
            return {}

    @api.model
    def get_hr_dashboard_data(self):
        """Get HR dashboard statistics"""
        try:
            # Employees by department
            emp_by_dept = {}
            depts = self.env['don_vi'].search([])
            for dept in depts:
                count = self.env['nhan_vien'].search_count([
                    ('don_vi_id', '=', dept.id)
                ])
                if count > 0:
                    emp_by_dept[dept.name] = count

            # Employees by position
            emp_by_pos = {}
            positions = self.env['chuc_vu'].search([])
            for pos in positions:
                count = self.env['nhan_vien'].search_count([
                    ('chuc_vu_id', '=', pos.id)
                ])
                if count > 0:
                    emp_by_pos[pos.name] = count

            # Total employees
            total_employees = self.env['nhan_vien'].search_count([])

            # Certifications distribution
            cert_dist = {}
            certs = self.env['chung_chi_bang_cap'].search([])
            for cert in certs:
                count = self.env['danh_sach_chung_chi_bang_cap'].search_count([
                    ('chung_chi_bang_cap_id', '=', cert.id)
                ])
                if count > 0:
                    cert_dist[cert.name] = count

            # Average age
            employees = self.env['nhan_vien'].search([])
            avg_age = 0
            if employees:
                ages = []
                for emp in employees:
                    if hasattr(emp, 'tuoi') and emp.tuoi:
                        ages.append(emp.tuoi)
                avg_age = sum(ages) / len(ages) if ages else 0

            # Project assignments
            project_dist = {}
            assignments = self.env['iot_project_assignment'].search([])
            for assign in assignments:
                proj_name = assign.project_id.name if assign.project_id else 'Unknown'
                project_dist[proj_name] = project_dist.get(proj_name, 0) + 1

            # Certification data
            total_certifications = self.env['danh_sach_chung_chi_bang_cap'].search_count([])

            return {
                'emp_by_dept': emp_by_dept,
                'emp_by_pos': emp_by_pos,
                'total_employees': total_employees,
                'cert_dist': cert_dist,
                'avg_age': avg_age,
                'project_dist': project_dist,
                'total_certifications': total_certifications,
            }
        except Exception as e:
            _logger.error(f"Error in get_hr_dashboard_data: {str(e)}")
            return {}
