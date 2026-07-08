import logging
import sys
import os

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class Customer(models.Model):
    _name = 'qlkh.customer'
    _description = 'Khách hàng'
    _rec_name = 'name'

    name = fields.Char('Tên khách hàng', required=True)
    code = fields.Char('Mã khách hàng', default=lambda self: self._generate_code(), readonly=True, copy=False)
    customer_type = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('doanh_nghiep', 'Doanh nghiệp')
    ], string='Loại khách hàng', required=True)
    status = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('da_xac_thuc', 'Đã xác thực'),
        ('dang_tu_van', 'Đang tư vấn'),
        ('da_gui_bao_gia', 'Đã gửi báo giá'),
        ('dam_phan', 'Đang đàm phán'),
        ('sap_ky_hd', 'Sắp ký hợp đồng'),
        ('thanh_cong', 'Thành công'),
        ('that_bai', 'Thất bại')
    ], string='Trạng thái', default='tiem_nang')
    area = fields.Char('Khu vực')
    industry = fields.Char('Ngành nghề')
    expected_revenue = fields.Float('Doanh thu kỳ vọng')
    priority = fields.Selection([
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao')
    ], string='Độ ưu tiên')
    nhan_vien_phu_trach_id = fields.Many2one(
        'hr.employee',
        string='Người phụ trách',
        required=False,
        ondelete='set null'
    )
    email = fields.Char('Email')
    phone = fields.Char('Số điện thoại')
    address = fields.Char('Địa chỉ')
    note = fields.Text('Ghi chú')

    interaction_count = fields.Integer(
        compute='_compute_statistics',
        string='Số tương tác'
    )

    quotation_count = fields.Integer(
        compute='_compute_statistics',
        string='Số báo giá'
    )

    contract_count = fields.Integer(
        compute='_compute_statistics',
        string='Số hợp đồng'
    )

    revenue_total = fields.Float(
        compute='_compute_statistics',
        string='Tổng doanh thu'
    )

    customer_score = fields.Float(
        string='Điểm khách hàng',
        compute='_compute_customer_score',
        store=True
    )

    interaction_ids = fields.One2many(
        'qlkh.customer_interaction',
        'customer_id',
        string='Lịch sử tương tác'
    )

    quotation_ids = fields.One2many(
        'qlkh.quotation',
        'customer_id',
        string='Báo giá'
    )

    contract_ids = fields.One2many(
        'qlkh.contract',
        'customer_id',
        string='Hợp đồng'
    )

    product_ids = fields.Many2many(
        'qlkh.contract_product',
        'qlkh_customer_product_rel',
        'customer_id',
        'product_id',
        string='Sản phẩm/Dịch vụ'
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã khách hàng phải là duy nhất!'),
        ('name_unique', 'unique(name)', 'Tên khách hàng phải là duy nhất!')
    ]

    @api.model
    def _generate_code(self):
        """Tự sinh mã khách hàng duy nhất"""
        import time
        return 'KH' + time.strftime('%Y%m%d%H%M%S')

    @api.model
    def create(self, vals):
        if 'name' in vals and self.search([('name', '=', vals['name'])]):
            raise ValidationError('Tên khách hàng đã tồn tại!')

        if not vals.get('code'):
            vals['code'] = self._generate_code()

        customer = super().create(vals)

        if customer.status == 'da_xac_thuc':
            if not self.env['qlkh.appointment'].search([('customer_id', '=', customer.id)], limit=1):
                self.env['qlkh.appointment'].create({
                    'name': f'Chăm sóc khách hàng - {customer.name}',
                    'customer_id': customer.id,
                    'nhan_vien_id': customer.nhan_vien_phu_trach_id.id,
                    'appointment_date': fields.Datetime.now(),
                    'status': 'moi',
                    'note': 'Lịch hẹn được tạo tự động khi khách hàng được xác thực'
                })

        if customer.status == 'da_gui_bao_gia' and not customer.quotation_ids:
            today_code = fields.Date.today().replace('-', '')
            self.env['qlkh.quotation'].create({
                'name': f'BQ-{customer.code or customer.id}-{today_code}',
                'customer_id': customer.id,
                'date': fields.Date.today(),
                'status': 'nhap',
            })

        # ... Phần AI và notification giữ nguyên ...
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.ai_helper import AIHelper
            from smart_biz_services.notif_helper import NotifHelper
            from smart_biz_services.agent_helper import AgentHelper

            ai_helper = AIHelper()
            notif = NotifHelper()

            customer_industry = customer.industry or 'Không xác định'
            customer_description = customer.note or ''
            customer_type_label = dict(self._fields['customer_type'].selection).get(customer.customer_type, customer.customer_type)

            ai_result = ai_helper.evaluate_customer_profile(
                customer_name=customer.name,
                customer_type=customer_type_label,
                source='Không xác định',
                industry=customer_industry,
                address=customer.address or 'Không xác định',
                description=customer_description
            )

            best_employee, confidence, reason = customer._find_best_employee(
                ai_score=ai_result.get('ai_score', 0.0),
                ai_reason=ai_result.get('ai_reason', ''),
                area=vals.get('area') or customer.area,
                industry=customer_industry,
                customer_type=customer_type_label,
                priority=vals.get('priority') or customer.priority or 'medium'
            )

            if best_employee:
                customer._reassign_employee_if_better(best_employee, confidence, reason)

            ai_score = ai_result.get('ai_score', 0.0)
            customer_priority = vals.get('priority') or customer.priority or 'medium'

            if ai_score >= 80 or customer_priority == 'high':
                meeting_title = f"Giới thiệu giải pháp - {customer.name}"
                reason = f"Khách hàng tiềm năng cao (Điểm AI: {ai_score}/100, Độ ưu tiên: {customer_priority})"
                customer._create_meeting(meeting_title, reason, duration_minutes=30)

            notif.send_telegram_template(
                'customer_created',
                customer_name=customer.name,
                customer_type=customer_type_label,
                industry=customer_industry,
                address=customer.address or 'Không xác định',
                ai_score=ai_result.get('ai_score', 0.0),
                ai_reason=ai_result.get('ai_reason', ''),
                employee_name=customer.nhan_vien_phu_trach_id.name or 'Đang phân công'
            )

            if customer.nhan_vien_phu_trach_id and customer.nhan_vien_phu_trach_id.work_email:
                notif.send_email_template(
                    'customer_created',
                    to_email=customer.nhan_vien_phu_trach_id.work_email,
                    recipient_name=customer.nhan_vien_phu_trach_id.name,
                    customer_name=customer.name,
                    customer_type=customer_type_label,
                    industry=customer_industry,
                    address=customer.address or 'Không xác định',
                    ai_score=ai_result.get('ai_score', 0.0),
                    ai_reason=ai_result.get('ai_reason', ''),
                    employee_name=customer.nhan_vien_phu_trach_id.name or 'Đang phân công'
                )
        except Exception as e:
            _logger.warning('AI đánh giá khách hàng thất bại: %s', e)

        return customer

    @api.depends('interaction_count', 'quotation_count', 'contract_count', 'revenue_total')
    def _compute_customer_score(self):
        for rec in self:
            score = (
                rec.interaction_count * 2
                + rec.quotation_count * 5
                + rec.contract_count * 10
                + rec.revenue_total / 10000000
            )
            rec.customer_score = min(score, 100)

    @api.depends('interaction_ids', 'quotation_ids', 'contract_ids', 'contract_ids.contract_value')
    def _compute_statistics(self):
        for rec in self:
            rec.interaction_count = len(rec.interaction_ids)
            rec.quotation_count = len(rec.quotation_ids)
            rec.contract_count = len(rec.contract_ids)
            rec.revenue_total = sum(rec.contract_ids.mapped('contract_value'))

    def _find_best_employee(self, ai_score, ai_reason, area, industry, customer_type, priority):
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.agent_helper import AgentHelper
            agent_helper = AgentHelper()
            agents_meta = []
            admin_user = self.env.ref('base.user_admin', raise_if_not_found=False)
            admin_domain = [('user_id', '!=', admin_user.id)] if admin_user else []
            for emp in self.env['hr.employee'].search(admin_domain):
                kpi_score = emp.diem_kpi if hasattr(emp, 'diem_kpi') and emp.diem_kpi else 0
                current_customer_count = self.env['qlkh.customer'].search_count([('nhan_vien_phu_trach_id', '=', emp.id)])
                agents_meta.append({
                    'user_id': emp.id,
                    'name': emp.name,
                    'job': emp.job_id.name if emp.job_id else 'Unknown',
                    'department': emp.department_id.name if emp.department_id else 'Unknown',
                    'region': emp.work_location_id.name if hasattr(emp, 'work_location_id') and emp.work_location_id else 'Unknown',
                    'load': current_customer_count,
                    'kpi_score': kpi_score,
                })
            route_result = agent_helper.route_lead({
                'area': area or 'Không xác định',
                'industry': industry or 'Không xác định',
                'customer_type': customer_type or 'Không xác định',
                'priority': priority or 'medium',
                'ai_score': ai_score,
                'ai_reason': ai_reason
            }, agents_meta=agents_meta)
            if route_result.get('confidence', 0.0) >= 0.65:
                employee_id = route_result.get('employee_id')
                if employee_id:
                    employee = self.env['hr.employee'].browse(employee_id)
                    if employee.exists():
                        return employee, route_result.get('confidence', 0.0), route_result.get('reason', '')
            employees_with_load = []
            for emp in self.env['hr.employee'].search(admin_domain):
                load = self.env['qlkh.customer'].search_count([('nhan_vien_phu_trach_id', '=', emp.id)])
                employees_with_load.append((emp, load))
            if employees_with_load:
                employees_with_load.sort(key=lambda x: x[1])
                return employees_with_load[0][0], 0.0, 'Load balancing: nhân viên có ít khách hàng nhất'
            return None, 0.0, 'Không tìm thấy nhân viên phù hợp'
        except Exception as e:
            _logger.error(f'Lỗi tìm nhân viên phù hợp: {e}')
            return None, 0.0, str(e)

    def _reassign_employee_if_better(self, new_employee, new_confidence, new_reason):
        if not new_employee:
            return False
        current_employee = self.nhan_vien_phu_trach_id
        if not current_employee:
            self.write({'nhan_vien_phu_trach_id': new_employee.id})
            return True
        if new_confidence >= 0.8 and current_employee.id != new_employee.id:
            self.write({'nhan_vien_phu_trach_id': new_employee.id})
            return True
        return False

    def _create_meeting(self, meeting_title, reason, duration_minutes=30):
        if not self.email:
            return None
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.google_helper import GoogleHelper
            from smart_biz_services.notif_helper import NotifHelper
            google = GoogleHelper()
            notif = NotifHelper()
            meeting_link = google.create_meeting(customer_email=self.email, customer_name=self.name, title=meeting_title, duration_minutes=duration_minutes)
            if not meeting_link:
                return None
            notif.send_telegram_template('meeting_created', customer_name=self.name, meeting_link=meeting_link, reason=reason, meeting_title=meeting_title)
            notif.send_email_template('meeting_invitation', to_email=self.email, recipient_name=self.name.split()[0] if self.name else self.name, customer_name=self.name, meeting_link=meeting_link, title=meeting_title, reason=reason)
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if activity_type:
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type.id,
                    'summary': f'Cuộc họp: {meeting_title}',
                    'note': f'Link Google Meet: {meeting_link}\nLý do: {reason}',
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'res_id': self.id,
                    'user_id': self.nhan_vien_phu_trach_id.user_id.id if self.nhan_vien_phu_trach_id and self.nhan_vien_phu_trach_id.user_id else self.env.user.id,
                    'date_deadline': fields.Date.today(),
                })

            if not self.env['qlkh.appointment'].search([('customer_id', '=', self.id), ('name', '=', meeting_title)], limit=1):
                self.env['qlkh.appointment'].create({
                    'name': meeting_title,
                    'customer_id': self.id,
                    'nhan_vien_id': self.nhan_vien_phu_trach_id.id,
                    'appointment_date': fields.Datetime.now(),
                    'status': 'moi',
                    'note': f'Link Google Meet: {meeting_link}\n{reason}'
                })

            if not self.env['qlkh.customer_interaction'].search([('customer_id', '=', self.id), ('type', '=', 'gap_mat'), ('note', 'ilike', meeting_link)], limit=1):
                self.env['qlkh.customer_interaction'].create({
                    'customer_id': self.id,
                    'date': fields.Datetime.now(),
                    'type': 'gap_mat',
                    'status': 'moi',
                    'content': reason,
                    'nhan_vien_id': self.nhan_vien_phu_trach_id.id,
                    'note': f'Link Google Meet: {meeting_link}'
                })
            return meeting_link
        except Exception:
            return None

    def write(self, vals):
        customers = self
        tracked_fields = {'status', 'expected_revenue', 'customer_type', 'industry'}
        old_values = {
            customer.id: {
                'status': customer.status,
                'expected_revenue': customer.expected_revenue,
                'customer_type': customer.customer_type,
                'industry': customer.industry,
            }
            for customer in customers
        }
        result = super().write(vals)
        if not tracked_fields.intersection(vals):
            return result
        for customer in self:
            if not any(field in vals and old_values.get(customer.id, {}).get(field) != vals.get(field) for field in tracked_fields):
                continue
            # Nếu khách hàng được xác thực, tạo cuộc hẹn chăm sóc ban đầu
            if customer.status == 'da_xac_thuc':
                if not self.env['qlkh.appointment'].search([('customer_id', '=', customer.id), ('status', '=', 'moi')], limit=1):
                    self.env['qlkh.appointment'].create({
                        'name': f'Chăm sóc khách hàng - {customer.name}',
                        'customer_id': customer.id,
                        'nhan_vien_id': customer.nhan_vien_phu_trach_id.id,
                        'appointment_date': fields.Datetime.now(),
                        'status': 'moi',
                        'note': 'Lịch hẹn được tạo tự động khi khách hàng được xác thực'
                    })

            if customer.status == 'da_gui_bao_gia' and not customer.quotation_ids:
                today_code = fields.Date.today().replace('-', '')
                self.env['qlkh.quotation'].create({
                    'name': f'BQ-{customer.code or customer.id}-{today_code}',
                    'customer_id': customer.id,
                    'date': fields.Date.today(),
                    'status': 'nhap',
                })

            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.ai_helper import AIHelper
                from smart_biz_services.notif_helper import NotifHelper
                ai_helper = AIHelper()
                notif = NotifHelper()
                status_label = dict(self._fields['status'].selection).get(customer.status, customer.status)
                employee_name = customer.nhan_vien_phu_trach_id.name or 'Chưa xác định'
                next_step_map = {
                    'tiem_nang': 'Thu thập thông tin, đánh giá tiềm năng.',
                    'da_xac_thuc': 'Xác thực nhu cầu và chuẩn bị tư vấn.',
                    'dang_tu_van': 'Tiếp tục tư vấn và giải pháp.',
                    'da_gui_bao_gia': 'Theo dõi phản hồi báo giá.',
                    'dam_phan': 'Tiếp tục thảo luận điều khoản và giá cả.',
                    'sap_ky_hd': 'Chuẩn bị ký hợp đồng và hoàn thiện thủ tục.',
                    'thanh_cong': 'Hoàn tất hợp đồng và triển khai dịch vụ.',
                    'that_bai': 'Đánh giá lại và tiếp tục xử lý khách hàng khác.',
                }
                next_step = next_step_map.get(customer.status, 'Tiếp tục theo dõi tiến độ khách hàng.')
                old_status = old_values.get(customer.id, {}).get('status', '')
                new_status = customer.status
                notif.send_telegram_template('customer_status_updated', customer_name=customer.name, old_status=old_status, new_status=status_label, employee_name=customer.nhan_vien_phu_trach_id.name or 'Đang xử lý', next_step=next_step)
                if customer.email and new_status not in ['tiem_nang']:
                    notif.send_email_template('customer_status_updated', to_email=customer.email, recipient_name=customer.name.split()[0] if customer.name else customer.name, customer_name=customer.name, status_code=new_status, employee_name=customer.nhan_vien_phu_trach_id.name or 'Đang xử lý', next_step=next_step, note=customer.note if customer.note else None)
            except Exception as e:
                _logger.error('Không thể gửi thông báo khi trạng thái khách hàng thay đổi cho %s: %s', customer.name, e, exc_info=True)
        return result