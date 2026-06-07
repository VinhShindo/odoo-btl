from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Customer(models.Model):
    _name = 'qlkh.customer'
    _description = 'Khách hàng'
    _rec_name = 'name'

    name = fields.Char('Tên khách hàng', required=True)
    code = fields.Char('Mã khách hàng', required=True)
    customer_type = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('doanh_nghiep', 'Doanh nghiệp')
    ], string='Loại khách hàng', required=True)
    status = fields.Selection([
        ('khach_hang_tiem_nang', 'Khách hàng tiềm năng'),
        ('da_xac_thuc', 'Đã xác thực'),
        ('bao_gia', 'Báo giá'),
        ('dam_phan', 'Đàm phán'),
        ('thanh_cong', 'Thành công'),
        ('that_bai', 'Thất bại')
    ], string='Trạng thái',
    default='khach_hang_tiem_nang',)
    nhan_vien_phu_trach_id = fields.Many2one('hr.employee', string='Người phụ trách', required=True)
    iot_device = fields.Char('Thiết bị IoT sử dụng')
    email = fields.Char('Email')
    phone = fields.Char('Số điện thoại')
    address = fields.Char('Địa chỉ')
    note = fields.Text('Ghi chú')

    interaction_count = fields.Integer(
        compute='_compute_statistics',
        string='Số tương tác'
    )

    quotation_count = fields.Integer(
        compute='_compute_statistics',
        string='Số báo giá'
    )

    contract_count = fields.Integer(
        compute='_compute_statistics',
        string='Số hợp đồng'
    )

    revenue_total = fields.Float(
        compute='_compute_statistics',
        string='Tổng doanh thu'
    )

    customer_score = fields.Float(
        string='Điểm khách hàng',
        compute='_compute_customer_score',
        store=True
    )

    interaction_ids = fields.One2many(
        'qlkh.customer_interaction',
        'customer_id',
        string='Lịch sử tương tác'
    )

    quotation_ids = fields.One2many(
        'qlkh.quotation',
        'customer_id',
        string='Báo giá'
    )

    contract_ids = fields.One2many(
        'qlkh.contract',
        'customer_id',
        string='Hợp đồng'
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã khách hàng phải là duy nhất!'),
        ('name_unique', 'unique(name)', 'Tên khách hàng phải là duy nhất!')
    ]

    @api.model
    def create(self, vals):

        if 'name' in vals and self.search([
            ('name', '=', vals['name'])
        ]):
            raise ValidationError(
                'Tên khách hàng đã tồn tại!'
            )

        if 'code' in vals and self.search([
            ('code', '=', vals['code'])
        ]):
            raise ValidationError(
                'Mã khách hàng đã tồn tại!'
            )
        
        customer = super().create(vals)

        if customer.status == 'da_xac_thuc':
            self.env['qlkh.appointment'].create({
                'name': f'Chăm sóc khách hàng - {customer.name}',
                'customer_id': customer.id,
                'nhan_vien_id': customer.nhan_vien_phu_trach_id.id,
                'appointment_date': fields.Datetime.now(),
                'status': 'moi',
                'note': 'Lịch hẹn được tạo tự động'
            })

        if customer.status == 'bao_gia' and not customer.quotation_ids:
            today_code = fields.Date.today().replace('-', '')
            self.env['qlkh.quotation'].create({
                'name': f'BQ-{customer.code or customer.id}-{today_code}',
                'customer_id': customer.id,
                'date': fields.Date.today(),
                'status': 'nhap',
            })

        return customer
    
    @api.depends(
    'interaction_count',
    'quotation_count',
    'contract_count',
    'revenue_total'
)
    def _compute_customer_score(self):

        for rec in self:

            score = (
                rec.interaction_count * 2
                + rec.quotation_count * 5
                + rec.contract_count * 10
                + rec.revenue_total / 10000000
            )

            rec.customer_score = min(score, 100)

    @api.depends(
    'interaction_ids',
    'quotation_ids',
    'contract_ids',
    'contract_ids.contract_value'
)
    def _compute_statistics(self):
        for rec in self:

            rec.interaction_count = len(
                rec.interaction_ids
            )

            rec.quotation_count = len(
                rec.quotation_ids
            )

            rec.contract_count = len(
                rec.contract_ids
            )

            rec.revenue_total = sum(
                rec.contract_ids.mapped(
                    'contract_value'
                )
            )

    def write(self, vals):
        customers = self
        statuses = {customer.id: customer.status for customer in customers}
        result = super().write(vals)

        for customer in self:
            new_status = vals.get('status')
            if new_status and statuses.get(customer.id) != new_status:
                if new_status == 'bao_gia' and not customer.quotation_ids:
                    today_code = fields.Date.today().replace('-', '')
                    self.env['qlkh.quotation'].create({
                        'name': f'BQ-{customer.code or customer.id}-{today_code}',
                        'customer_id': customer.id,
                        'date': fields.Date.today(),
                        'status': 'nhap',
                    })

        return result
