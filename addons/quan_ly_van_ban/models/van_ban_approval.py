from odoo import models, fields


class VanBanApproval(models.Model):
    _name = 'van_ban.approval'
    _description = 'Lịch sử phê duyệt'

    document_id = fields.Many2one(
        'van_ban.document',
        required=True,
        ondelete='cascade'
    )

    approver_id = fields.Many2one(
        'hr.employee',
        string='Người duyệt'
    )

    approve_date = fields.Datetime(
        default=fields.Datetime.now
    )

    status = fields.Selection([
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ])

    comment = fields.Text()