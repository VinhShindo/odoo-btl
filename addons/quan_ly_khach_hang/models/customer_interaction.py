from datetime import timedelta
import logging
import os
import sys

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CustomerInteraction(models.Model):
    _name = 'qlkh.customer_interaction'
    _description = 'Lịch sử tương tác, chăm sóc khách hàng'

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
    nhan_vien_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên thực hiện',
        ondelete='set null'
    )
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
        
        # ========== TRIGGER 11: Tạo meeting khi có khiếu nại ==========
        if interaction.type == 'khieu_nai':
            interaction._create_complaint_meeting()
        # ========== KẾT THÚC TRIGGER 11 ==========
        
        interaction._analyze_sentiment_if_required()
        return interaction

    def write(self, vals):
        original_types = {rec.id: rec.type for rec in self}
        result = super().write(vals)
        for record in self:
            if 'type' in vals and record.type == 'khieu_nai' and original_types.get(record.id) != 'khieu_nai':
                record._create_complaint_meeting()
            if 'content' in vals or 'note' in vals:
                record._analyze_sentiment_if_required()
        return result

    def _analyze_sentiment_if_required(self):
        for record in self:
            content_to_analyze = record.content or record.note
            if not content_to_analyze:
                continue
            if record.sentiment_label or record.sentiment_score or record.sentiment_summary:
                continue
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.ai_helper import AIHelper

                ai_helper = AIHelper()
                analysis = ai_helper.analyze_sentiment(content_to_analyze)

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

                # ========== TRIGGER 10: Tạo meeting khi cảm xúc tiêu cực ==========
                if sentiment == 'negative' and confidence >= 0.8:
                    record._create_negative_feedback_meeting(summary)
                # ========== KẾT THÚC TRIGGER 10 ==========

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

    def _create_negative_feedback_meeting(self, summary):
        """Tạo meeting khi phát hiện phản hồi tiêu cực"""
        if not self.customer_id or not self.customer_id.email:
            return
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.google_helper import GoogleHelper
            from smart_biz_services.notif_helper import NotifHelper
            
            google = GoogleHelper()
            notif = NotifHelper()
            
            meeting_title = f"Khắc phục sự cố - {self.customer_id.name}"
            reason = f"Phát hiện phản hồi tiêu cực (độ tin cậy: {self.sentiment_confidence:.0%})\nNội dung: {summary[:200]}"
            
            meeting_link = google.create_meeting(
                customer_email=self.customer_id.email,
                customer_name=self.customer_id.name,
                title=meeting_title,
                duration_minutes=30
            )
            
            if meeting_link:
                notif.send_telegram_template(
                    'meeting_created',
                    customer_name=self.customer_id.name,
                    meeting_link=meeting_link,
                    reason=reason,
                    meeting_title=meeting_title
                )
                
                notif.send_email_template(
                    'meeting_invitation',
                    to_email=self.customer_id.email,
                    recipient_name=self.customer_id.name.split()[0] if self.customer_id.name else self.customer_id.name,
                    customer_name=self.customer_id.name,
                    meeting_link=meeting_link,
                    title=meeting_title,
                    reason=reason
                )
                
                _logger.info(f'Đã tạo meeting khắc phục cho khách hàng {self.customer_id.name}')
                
        except Exception as e:
            _logger.error(f'Lỗi tạo meeting khắc phục: {e}')

    def _create_complaint_meeting(self):
        """Tạo meeting khi có khiếu nại"""
        if not self.customer_id or not self.customer_id.email:
            return
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.google_helper import GoogleHelper
            from smart_biz_services.notif_helper import NotifHelper
            
            google = GoogleHelper()
            notif = NotifHelper()
            
            meeting_title = f"Giải quyết khiếu nại - {self.customer_id.name}"
            reason = f"Khiếu nại từ khách hàng: {self.content[:200]}"
            
            meeting_link = google.create_meeting(
                customer_email=self.customer_id.email,
                customer_name=self.customer_id.name,
                title=meeting_title,
                duration_minutes=45
            )
            
            if meeting_link:
                notif.send_telegram_template(
                    'meeting_created',
                    customer_name=self.customer_id.name,
                    meeting_link=meeting_link,
                    reason=reason,
                    meeting_title=meeting_title
                )
                
                notif.send_email_template(
                    'meeting_invitation',
                    to_email=self.customer_id.email,
                    recipient_name=self.customer_id.name.split()[0] if self.customer_id.name else self.customer_id.name,
                    customer_name=self.customer_id.name,
                    meeting_link=meeting_link,
                    title=meeting_title,
                    reason=reason
                )
                
                # Tạo activity cho nhân viên phụ trách
                activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                if activity_type and self.customer_id.nhan_vien_phu_trach_id:
                    self.env['mail.activity'].create({
                        'activity_type_id': activity_type.id,
                        'summary': f'Xử lý khiếu nại: {meeting_title}',
                        'note': f'Link họp: {meeting_link}\nNội dung khiếu nại: {self.content[:500]}',
                        'res_model_id': self.env['ir.model']._get(self._name).id,
                        'res_id': self.id,
                        'user_id': self.customer_id.nhan_vien_phu_trach_id.user_id.id if self.customer_id.nhan_vien_phu_trach_id.user_id else self.env.user.id,
                        'date_deadline': fields.Date.today() + timedelta(days=1),
                    })
                
                _logger.info(f'Đã tạo meeting giải quyết khiếu nại cho khách hàng {self.customer_id.name}')
                
        except Exception as e:
            _logger.error(f'Lỗi tạo meeting khiếu nại: {e}')

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
