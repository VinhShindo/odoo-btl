from odoo import models, fields


class VanBanVersion(models.Model):
    _name = 'van_ban.version'
    _description = 'Phiên bản văn bản'
    _order = 'id desc'

    document_id = fields.Many2one(
        'van_ban.document',
        required=True,
        ondelete='cascade'
    )

    version_no = fields.Char(
        required=True
    )

    file = fields.Binary(
        'File'
    )

    file_name = fields.Char()

    created_by = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user
    )

    created_date = fields.Datetime(
        default=fields.Datetime.now
    )

    note = fields.Text()