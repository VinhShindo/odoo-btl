from odoo import models, fields, api

class IotDeviceLog(models.Model):
    _name = 'iot_device_log'
    _description = 'Lịch sử sử dụng thiết bị IoT'

    device_name = fields.Char('Tên thiết bị', required=True)
    device_code = fields.Char('Mã thiết bị')
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên sử dụng', required=True)
    event_type = fields.Selection([
        ('use', 'Sử dụng'),
        ('maintenance', 'Bảo trì'),
        ('error', 'Sự cố'),
        ('return', 'Thu hồi')
    ], string='Loại sự kiện', required=True)
    event_date = fields.Datetime('Thời gian')
    note = fields.Text('Ghi chú')
