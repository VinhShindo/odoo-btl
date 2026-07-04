import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class NhanSuDashboardHelper(models.AbstractModel):
    _name = 'nhan_su.dashboard.helper'
    _description = 'Nhan Su Dashboard Helper'

    @api.model
    def get_nhan_su_dashboard_data(self):
        """Get HR dashboard statistics (100% SQL Version)"""
        try:
            # 1. Tổng nhân viên, Tuổi trung bình, Nhóm phòng ban (dùng SQL thuần)
            self.env.cr.execute("""
                SELECT 
                    COUNT(*) as total_emp,
                    AVG(tuoi) as avg_age,
                    don_vi_id
                FROM hr_employee
                GROUP BY don_vi_id
            """)
            dept_rows = self.env.cr.fetchall()
            
            total_employees = 0
            total_age = 0
            age_count = 0
            emp_by_dept = {}
            
            for row in dept_rows:
                total_employees += row[0]
                if row[1]:
                    total_age += row[1]
                    age_count += 1
                # Lấy tên phòng ban từ bảng don_vi
                if row[2]:
                    self.env.cr.execute("SELECT ten_don_vi FROM don_vi WHERE id = %s", (row[2],))
                    dept_name_row = self.env.cr.fetchone()
                    dept_name = dept_name_row[0] if dept_name_row else 'Không xác định'
                    emp_by_dept[dept_name] = row[0]

            # 2. Nhóm theo Chức vụ (dùng SQL)
            self.env.cr.execute("""
                SELECT chuc_vu_id, COUNT(*) 
                FROM hr_employee 
                WHERE chuc_vu_id IS NOT NULL 
                GROUP BY chuc_vu_id
            """)
            pos_rows = self.env.cr.fetchall()
            
            emp_by_pos = {}
            for row in pos_rows:
                # Lấy tên chức vụ từ bảng chuc_vu
                self.env.cr.execute("SELECT ten_chuc_vu FROM chuc_vu WHERE id = %s", (row[0],))
                pos_name_row = self.env.cr.fetchone()
                pos_name = pos_name_row[0] if pos_name_row else 'Không xác định'
                emp_by_pos[pos_name] = row[1]

            # Tính tuổi trung bình cuối cùng
            avg_age = total_age / age_count if age_count > 0 else 0

            # 3. Chứng chỉ (Dùng SQL)
            self.env.cr.execute("""
                SELECT c.id, c.ten_chung_chi_bang_cap, COUNT(d.id) as count
                FROM chung_chi_bang_cap c
                LEFT JOIN danh_sach_chung_chi_bang_cap d ON d.chung_chi_bang_cap_id = c.id
                GROUP BY c.id, c.ten_chung_chi_bang_cap
                HAVING COUNT(d.id) > 0
            """)
            cert_rows = self.env.cr.fetchall()
            
            cert_dist = {}
            for row in cert_rows:
                cert_dist[row[1]] = row[2]

            # 4. Dự án IoT (Dùng SQL)
            self.env.cr.execute("""
                SELECT name, COUNT(*) 
                FROM iot_project_assignment 
                GROUP BY name
            """)
            project_rows = self.env.cr.fetchall()
            
            project_dist = {}
            for row in project_rows:
                project_dist[row[0]] = row[1]

            # 5. Tổng chứng chỉ
            self.env.cr.execute("SELECT COUNT(*) FROM danh_sach_chung_chi_bang_cap")
            total_certifications = self.env.cr.fetchone()[0] or 0

            # 6. Nhân viên gần đây (Lấy 5 người mới nhất)
            self.env.cr.execute("""
                SELECT e.id, e.name, c.ten_chuc_vu, d.ten_don_vi
                FROM hr_employee e
                LEFT JOIN chuc_vu c ON c.id = e.chuc_vu_id
                LEFT JOIN don_vi d ON d.id = e.don_vi_id
                ORDER BY e.create_date DESC
                LIMIT 5
            """)
            recent_rows = self.env.cr.fetchall()
            
            recent_employees = []
            for row in recent_rows:
                recent_employees.append({
                    'name': row[1] or 'N/A',
                    'position': row[2] or 'N/A',
                    'department': row[3] or 'N/A'
                })

            return {
                'emp_by_dept': emp_by_dept,
                'emp_by_pos': emp_by_pos,
                'total_employees': total_employees,
                'cert_dist': cert_dist,
                'avg_age': avg_age,
                'project_dist': project_dist,
                'work_history': {},  # Tùy chọn
                'total_certifications': total_certifications,
                'recent_employees': recent_employees,
            }
        except Exception as e:
            _logger.error(f"Error in get_nhan_su_dashboard_data: {str(e)}")
            return {}