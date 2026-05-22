from odoo import models, fields, api

class IotProjectAssignment(models.Model):
    _name = 'iot_project_assignment'
    _description = 'Phân công dự án IoT cho nhân viên'

    name = fields.Char('Tên dự án', required=True)
    description = fields.Text('Mô tả dự án')
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    role = fields.Char('Vai trò trong dự án')
    date_start = fields.Date('Ngày bắt đầu')
    date_end = fields.Date('Ngày kết thúc')
    note = fields.Text('Ghi chú')
