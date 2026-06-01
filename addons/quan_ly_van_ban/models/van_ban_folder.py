from odoo import models, fields, api


class VanBanFolder(models.Model):
    _name = 'van_ban.folder'
    _description = 'Thư mục văn bản'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên thư mục', required=True)
    parent_id = fields.Many2one('van_ban.folder', string='Thư mục cha', index=True, ondelete='cascade')
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('van_ban.folder', 'parent_id', string='Thư mục con')
    document_ids = fields.One2many('van_ban.document', 'folder_id', string='Tài liệu')
    document_count = fields.Integer('Số tài liệu', compute='_compute_document_count')
    complete_name = fields.Char('Đường dẫn đầy đủ', compute='_compute_complete_name', store=True)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for rec in self:
            if rec.parent_id:
                rec.complete_name = f"{rec.parent_id.complete_name or rec.parent_id.name} / {rec.name}"
            else:
                rec.complete_name = rec.name
