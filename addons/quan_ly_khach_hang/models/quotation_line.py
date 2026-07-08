from odoo import models, fields, api

class QuotationLine(models.Model):
    _name = 'qlkh.quotation.line'
    _description = 'Dòng chi tiết báo giá'
    _rec_name = 'description'
    _order = 'id'

    quotation_id = fields.Many2one(
        'qlkh.quotation',
        string='Báo giá',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'qlkh.contract_product',
        string='Sản phẩm',
        help='Chọn sản phẩm/dịch vụ từ danh mục'
    )
    product_name = fields.Char(
        string='Tên sản phẩm',
        compute='_compute_product_name',
        store=True,
        help='Tên sản phẩm hoặc dịch vụ'
    )
    description = fields.Char(
        string='Mô tả',
        required=True
    )
    quantity = fields.Float(
        string='Số lượng',
        default=1.0,
        required=True
    )
    unit_price = fields.Float(
        string='Đơn giá',
        required=True
    )
    vat_rate = fields.Float(
        string='VAT (%)',
        default=10.0
    )
    price_subtotal = fields.Float(
        string='Thành tiền trước VAT',
        compute='_compute_amount',
        store=True
    )
    price_tax = fields.Float(
        string='VAT',
        compute='_compute_amount',
        store=True
    )
    price_total = fields.Float(
        string='Thành tiền',
        compute='_compute_amount',
        store=True
    )

    @api.depends('quantity', 'unit_price', 'vat_rate')
    def _compute_amount(self):
        for rec in self:
            subtotal = rec.quantity * rec.unit_price
            tax = subtotal * (rec.vat_rate or 0.0) / 100.0
            rec.price_subtotal = subtotal
            rec.price_tax = tax
            rec.price_total = subtotal + tax

    @api.depends('product_id')
    def _compute_product_name(self):
        for rec in self:
            rec.product_name = rec.product_id.name if rec.product_id else ''

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                if not rec.unit_price or rec.unit_price == 0.0:
                    rec.unit_price = rec.product_id.list_price or 0.0
                if not rec.description:
                    rec.description = rec.product_id.technical_specs or ''
