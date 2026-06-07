from odoo import models, fields, api


class QuotationLine(models.Model):
    _name = 'qlkh.quotation.line'
    _description = 'Dòng chi tiết báo giá'

    quotation_id = fields.Many2one(
        'qlkh.quotation',
        string='Báo giá',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Sản phẩm'
    )
    description = fields.Char(
        string='Mô tả'
    )
    quantity = fields.Float(
        string='Số lượng',
        default=1.0
    )
    unit_price = fields.Float(
        string='Đơn giá'
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
