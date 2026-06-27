from odoo import models, fields, api


class VanBanRouting(models.Model):
    _name = 'van_ban.routing'
    _description = 'Quy trình/luồng xử lý văn bản'

    name = fields.Char('Tiêu đề', required=True)
    document_id = fields.Many2one('van_ban.document', string='Văn bản', required=True, ondelete='cascade')
    assigned_to = fields.Many2one('hr.employee', string='Người xử lý', ondelete='set null')
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

            if rec.document_id:

                employee = rec.assigned_to

                rec.document_id.write({
                    'status': 'approved',
                    'approved_date': fields.Datetime.now(),
                    'approved_by': employee.id if employee else False,
                    'is_locked': True
                })

                self.env['van_ban.approval'].create({
                    'document_id': rec.document_id.id,
                    'approver_id': employee.id if employee else False,
                    'approver_user_id': self.env.uid,
                    'status': 'approved',
                    'comment': f'Approved via routing stage {rec.stage}',
                    'level': 1
                })

    def action_reject(self):
        for rec in self:
            rec.stage = 'rejected'
            if rec.document_id:
                rec.document_id.write({
                    'status': 'draft'
                })
