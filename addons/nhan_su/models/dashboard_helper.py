import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HRDashboardHelper(models.AbstractModel):
    _name = 'hr.dashboard.helper'
    _description = 'HR Dashboard Helper'

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
            try:
                assignments = self.env['iot_project_assignment'].search([])
                for assign in assignments:
                    proj_name = assign.project_id.name if assign.project_id else 'Unknown'
                    project_dist[proj_name] = project_dist.get(proj_name, 0) + 1
            except:
                pass

            # Work history distribution
            work_history = {}
            try:
                histories = self.env['lich_su_cong_tac'].search([], order='create_date desc', limit=10)
                for history in histories:
                    if history.nhan_vien_id:
                        emp_name = history.nhan_vien_id.name
                        work_history[emp_name] = work_history.get(emp_name, 0) + 1
            except:
                pass

            # Total certifications
            total_certifications = self.env['danh_sach_chung_chi_bang_cap'].search_count([])

            # Recent employees
            recent_employees = []
            try:
                recent = self.env['nhan_vien'].search([], order='create_date desc', limit=5)
                for emp in recent:
                    recent_employees.append({
                        'name': emp.name or 'N/A',
                        'position': emp.chuc_vu_id.name if emp.chuc_vu_id else 'N/A',
                        'department': emp.don_vi_id.name if emp.don_vi_id else 'N/A'
                    })
            except:
                pass

            return {
                'emp_by_dept': emp_by_dept,
                'emp_by_pos': emp_by_pos,
                'total_employees': total_employees,
                'cert_dist': cert_dist,
                'avg_age': avg_age,
                'project_dist': project_dist,
                'work_history': work_history,
                'total_certifications': total_certifications,
                'recent_employees': recent_employees,
            }
        except Exception as e:
            _logger.error(f"Error in get_hr_dashboard_data: {str(e)}")
            return {}
