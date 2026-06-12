from odoo import models, fields


class ContractProduct(models.Model):
    _name = 'qlkh.contract_product'
    _description = 'Sản phẩm / Dịch vụ công ty (IoT)'

    name = fields.Char('Tên sản phẩm', required=True)
    code = fields.Char('Mã sản phẩm', index=True)
    category = fields.Char('Danh mục')
    device_type = fields.Selection([
        ('device', 'Thiết bị'),
        ('service', 'Dịch vụ'),
        ('bundle', 'Gói')
    ], string='Loại', default='device')
    technical_specs = fields.Text('Thông số kỹ thuật')
    connectivity = fields.Char('Kết nối')
    warranty = fields.Char('Bảo hành')
    service_plan = fields.Char('Gói dịch vụ')
    list_price = fields.Float('Giá niêm yết')
    cost_price = fields.Float('Giá vốn')
    support_info = fields.Text('Thông tin hỗ trợ')
    active = fields.Boolean('Hiển thị', default=True)
