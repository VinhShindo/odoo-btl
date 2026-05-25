from odoo import models, fields, api


class VanBanRouting(models.Model):
    _name = 'van_ban.routing'
    _description = 'Quy trình/luồng xử lý văn bản'

    name = fields.Char('Tiêu đề', required=True)
    document_id = fields.Many2one('van_ban.document', string='Văn bản', required=True, ondelete='cascade')
    assigned_to = fields.Many2one('hr.employee', string='Người xử lý')
    stage = fields.Selection([
        ('to_process', 'Chờ xử lý'),
        ('in_progress', 'Đang xử lý'),
        ('done', 'Hoàn tất'),
        ('rejected', 'Từ chối')
    ], string='Trạng thái', default='to_process')
    date_deadline = fields.Date('Hạn xử lý')
    note = fields.Text('Ghi chú')

    def action_set_in_progress(self):
        for rec in self:
            rec.stage = 'in_progress'

    def action_set_done(self):
        for rec in self:
            rec.stage = 'done'
            # mark document as approved when routing completes
            if rec.document_id:
                rec.document_id.status = 'approved'

    def action_reject(self):
        for rec in self:
            rec.stage = 'rejected'
            if rec.document_id:
                rec.document_id.status = 'draft'
