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
    code = fields.Char('Mã khách hàng', required=True)
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
    ], string='Trạng thái',
    default='tiem_nang',)
    area = fields.Char('Khu vực')
    industry = fields.Char('Ngành nghề')
    expected_revenue = fields.Float('Doanh thu kỳ vọng')
    priority = fields.Selection([
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao')
    ], string='Độ ưu tiên')
    nhan_vien_phu_trach_id = fields.Many2one('hr.employee', string='Người phụ trách', required=True)
    iot_device = fields.Char('Thiết bị IoT sử dụng')
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

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã khách hàng phải là duy nhất!'),
        ('name_unique', 'unique(name)', 'Tên khách hàng phải là duy nhất!')
    ]

    @api.model
    def create(self, vals):

        if 'name' in vals and self.search([
            ('name', '=', vals['name'])
        ]):
            raise ValidationError(
                'Tên khách hàng đã tồn tại!'
            )

        if 'code' in vals and self.search([
            ('code', '=', vals['code'])
        ]):
            raise ValidationError(
                'Mã khách hàng đã tồn tại!'
            )
        
        customer = super().create(vals)

        if customer.status == 'da_xac_thuc':
            self.env['qlkh.appointment'].create({
                'name': f'Chăm sóc khách hàng - {customer.name}',
                'customer_id': customer.id,
                'nhan_vien_id': customer.nhan_vien_phu_trach_id.id,
                'appointment_date': fields.Datetime.now(),
                'status': 'moi',
                'note': 'Lịch hẹn được tạo tự động'
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

            agent_helper = AgentHelper()  # Already imported above in try block
            agents_meta = []
            for emp in self.env['hr.employee'].search([]):
                agents_meta.append({
                    'user_id': emp.id,
                    'name': emp.name,
                    'job': emp.job_id.name if emp.job_id else 'Unknown',
                    'department': emp.department_id.name if emp.department_id else 'Unknown',
                    'region': emp.work_location_id.name if hasattr(emp, 'work_location_id') and emp.work_location_id else 'Unknown',
                    'load': 0
                })

            route_result = agent_helper.route_lead({
                'area': vals.get('area') or customer.area or 'Không xác định',
                'industry': customer_industry,
                'customer_type': customer_type_label,
                'priority': vals.get('priority') or customer.priority or 'medium',
                'ai_score': ai_result.get('ai_score', 0.0),
                'ai_reason': ai_result.get('ai_reason', '')
            }, agents_meta=agents_meta)

            if route_result.get('confidence', 0.0) >= 0.75 and not customer.nhan_vien_phu_trach_id:
                employee_id = route_result.get('employee_id')
                if employee_id:
                    employee = self.env['hr.employee'].browse(employee_id)
                    if employee.exists():
                        customer.write({'nhan_vien_phu_trach_id': employee.id})
                        _logger.info('Tự động gán nhân viên theo route_lead: %s', employee.name)
                    else:
                        _logger.warning('route_lead trả employee_id không tồn tại: %s', employee_id)
                else:
                    _logger.warning('route_lead trả employee_id trống, không gán nhân viên tự động.')
            else:
                _logger.info('route_lead confidence thấp hoặc nhân viên đã được gán, không tự động gán. confidence=%s', route_result.get('confidence'))

            default_message = (
                f"Khách hàng mới đã được tạo:\n"
                f"Tên: {customer.name}\n"
                f"Loại khách hàng: {customer_type_label}\n"
                f"Ngành nghề: {customer_industry}\n"
                f"Địa chỉ: {customer.address or 'Không xác định'}\n"
                f"Mô tả: {customer_description}\n"
                f"AI Score: {ai_result.get('ai_score', 0.0)}\n"
                f"AI Reason: {ai_result.get('ai_reason', '')}\n"
            )

            notif.send_telegram(
                title='Khách hàng mới được tạo',
                content=default_message
            )

            if customer.email:
                notif.send_email(
                    to_email=customer.email,
                    subject='Khách hàng mới được tạo',
                    body=default_message,
                    is_html=False,
                    use_default=False
                )
            else:
                _logger.warning('Không có email khách hàng để gửi thông báo Gmail.')
        except Exception as e:
            _logger.warning('AI đánh giá khách hàng thất bại: %s', e)

        return customer
    
    @api.depends(
    'interaction_count',
    'quotation_count',
    'contract_count',
    'revenue_total'
)
    def _compute_customer_score(self):

        for rec in self:

            score = (
                rec.interaction_count * 2
                + rec.quotation_count * 5
                + rec.contract_count * 10
                + rec.revenue_total / 10000000
            )

            rec.customer_score = min(score, 100)

    @api.depends(
    'interaction_ids',
    'quotation_ids',
    'contract_ids',
    'contract_ids.contract_value'
)
    def _compute_statistics(self):
        for rec in self:

            rec.interaction_count = len(
                rec.interaction_ids
            )

            rec.quotation_count = len(
                rec.quotation_ids
            )

            rec.contract_count = len(
                rec.contract_ids
            )

            rec.revenue_total = sum(
                rec.contract_ids.mapped(
                    'contract_value'
                )
            )

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
            if not any(
                field in vals and old_values.get(customer.id, {}).get(field) != vals.get(field)
                for field in tracked_fields
            ):
                continue

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

                notification_content = ai_helper.generate_message(
                    customer_name=customer.name,
                    requirement=(
                        f"Trạng thái mới: {status_label}. "
                        f"Bước tiếp theo: {next_step}"
                    ),
                    employee_name=employee_name,
                    meeting_link=None
                )

                if not notification_content:
                    notification_content = (
                        f"Khách hàng: {customer.name}\n"
                        f"Trạng thái mới: {status_label}\n"
                        f"Người phụ trách: {employee_name}\n"
                        f"Bước tiếp theo: {next_step}"
                    )

                notif.send_telegram(
                    title=f'Cập nhật trạng thái khách hàng: {customer.name}',
                    content=notification_content
                )

                if customer.email:
                    notif.send_email(
                        to_email=customer.email,
                        subject='Cập nhật trạng thái khách hàng',
                        body=notification_content,
                        is_html=False,
                        use_default=False
                    )
            except Exception as e:
                _logger.error(
                    'Không thể gửi thông báo khi trạng thái khách hàng thay đổi cho %s: %s',
                    customer.name,
                    e,
                    exc_info=True
                )

        return result
