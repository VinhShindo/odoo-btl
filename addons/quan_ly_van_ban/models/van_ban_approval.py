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

    approver_user_id = fields.Many2one(
        'res.users',
        string='Người duyệt (User)'
    )

    approve_date = fields.Datetime(
        default=fields.Datetime.now
    )

    # approval level for multi-level approvals (1 = first level, 2 = second, ...)
    level = fields.Integer(string='Cấp phê duyệt', default=1)

    status = fields.Selection([
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ])

    comment = fields.Text()