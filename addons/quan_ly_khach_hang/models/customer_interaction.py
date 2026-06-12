import logging
import os
import sys

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CustomerInteraction(models.Model):
    _name = 'qlkh.customer_interaction'
    _description = 'Lịch sử giao dịch, chăm sóc khách hàng'

    customer_id = fields.Many2one('qlkh.customer', string='Khách hàng', required=True)
    date = fields.Datetime('Thời gian')
    type = fields.Selection([
        ('goi_dien', 'Gọi điện'),
        ('gap_mat', 'Gặp mặt'),
        ('email', 'Email'),
        ('ho_tro', 'Hỗ trợ'),
        ('khieu_nai', 'Khiếu nại'),
        ('khac', 'Khác')
    ], string='Loại tương tác')
    status = fields.Selection([
        ('moi', 'Mới'),
        ('da_thuc_hien', 'Đã thực hiện'),
        ('huy', 'Hủy')
    ], string='Trạng thái',
    default='moi')
    content = fields.Text('Nội dung')
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên thực hiện')
    note = fields.Text('Ghi chú')

    sentiment_score = fields.Float('Điểm cảm xúc')
    sentiment_confidence = fields.Float('Độ tin cậy cảm xúc')
    sentiment_label = fields.Selection([
        ('positive', 'Tích cực'),
        ('negative', 'Tiêu cực'),
        ('neutral', 'Trung tính')
    ], string='Nhãn cảm xúc')
    sentiment_summary = fields.Text('Tóm tắt cảm xúc')

    @api.model
    def create(self, vals):
        interaction = super().create(vals)
        interaction._analyze_sentiment_if_required()
        return interaction

    def write(self, vals):
        result = super().write(vals)
        if 'content' in vals:
            self._analyze_sentiment_if_required()
        return result

    def _analyze_sentiment_if_required(self):
        for record in self:
            if not record.content:
                continue
            if record.sentiment_label or record.sentiment_score or record.sentiment_summary:
                continue
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.ai_helper import AIHelper

                ai_helper = AIHelper()
                analysis = ai_helper.analyze_sentiment(record.content)

                if not isinstance(analysis, dict):
                    raise ValueError('Kết quả phân tích không hợp lệ')

                sentiment = analysis.get('sentiment') or 'neutral'
                confidence = float(analysis.get('score') or 0.0)
                summary = analysis.get('summary')
                if not summary:
                    key_points = analysis.get('key_points')
                    if isinstance(key_points, list):
                        summary = '; '.join(str(x) for x in key_points)
                    elif key_points is not None:
                        summary = str(key_points)
                    else:
                        summary = ''

                record.write({
                    'sentiment_label': sentiment,
                    'sentiment_score': confidence,
                    'sentiment_confidence': float(analysis.get('confidence') or 0.0),
                    'sentiment_summary': summary,
                })

                if sentiment == 'negative' and confidence >= 0.6:
                    record._create_manager_activity(
                        summary=f'Tương tác tiêu cực cần quản lý xem xét: {summary or record.content[:120]}'
                    )
            except Exception as exc:
                _logger.error(
                    'Lỗi phân tích cảm xúc cho interaction %s: %s',
                    record.id,
                    exc,
                    exc_info=True
                )

    def _create_manager_activity(self, summary=None):
        try:
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if not activity_type:
                _logger.warning('Không tìm thấy activity type mail.todo; bỏ qua tạo activity quản lý')
                return

            assigned_user = self.env.user
            if self.customer_id and self.customer_id.nhan_vien_phu_trach_id:
                manager = self.customer_id.nhan_vien_phu_trach_id.parent_id
                if manager and manager.user_id:
                    assigned_user = manager.user_id

            self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'summary': summary or 'Tương tác tiêu cực cần xem xét',
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'res_id': self.id,
                'user_id': assigned_user.id,
                'date_deadline': fields.Date.context_today(self),
            })
        except Exception as exc:
            _logger.error(
                'Không thể tạo activity cho quản lý khi tương tác tiêu cực %s: %s',
                self.id,
                exc,
                exc_info=True
            )
