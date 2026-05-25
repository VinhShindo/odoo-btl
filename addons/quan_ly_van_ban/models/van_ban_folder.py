from odoo import models, fields, api


class VanBanFolder(models.Model):
    _name = 'van_ban.folder'
    _description = 'Thư mục văn bản'

    name = fields.Char('Tên thư mục', required=True)
    parent_id = fields.Many2one('van_ban.folder', string='Thư mục cha')
    child_ids = fields.One2many('van_ban.folder', 'parent_id', string='Thư mục con')
    document_ids = fields.One2many('van_ban.document', 'folder_id', string='Tài liệu')
    document_count = fields.Integer('Số tài liệu', compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)
