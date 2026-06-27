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
    nhan_vien_phu_trach_id = fields.Many2one(
        'hr.employee',
        string='Người phụ trách',
        required=False,
        ondelete='set null'
    )
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
            
            # 1. Tìm nhân viên phù hợp nhất dựa trên AI và thông tin khách hàng
            best_employee, confidence, reason = customer._find_best_employee(
                ai_score=ai_result.get('ai_score', 0.0),
                ai_reason=ai_result.get('ai_reason', ''),
                area=vals.get('area') or customer.area,
                industry=customer_industry,
                customer_type=customer_type_label,
                priority=vals.get('priority') or customer.priority or 'medium'
            )
            
            # 2. Gán nhân viên nếu tìm thấy (so sánh và gán lại nếu phù hợp hơn)
            if best_employee:
                customer._reassign_employee_if_better(best_employee, confidence, reason)
            else:
                _logger.warning('Không tìm thấy nhân viên phù hợp cho khách hàng %s', customer.name)
            
            # ========== TRIGGER 1: Meeting cho khách hàng tiềm năng cao ==========
            ai_score = ai_result.get('ai_score', 0.0)
            customer_priority = vals.get('priority') or customer.priority or 'medium'
            
            if ai_score >= 80 or customer_priority == 'high':
                meeting_title = f"Giới thiệu giải pháp - {customer.name}"
                reason = f"Khách hàng tiềm năng cao (Điểm AI: {ai_score}/100, Độ ưu tiên: {customer_priority})"
                customer._create_meeting(meeting_title, reason, duration_minutes=30)

            # Gửi Telegram
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

            # Gửi Email nội bộ cho phụ trách (không gửi cho khách hàng)
            if customer.nhan_vien_phu_trach_id.work_email:
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

    def _find_best_employee(self, ai_score, ai_reason, area, industry, customer_type, priority):
        """
        Tìm nhân viên phù hợp nhất dựa trên:
        - AI score của khách hàng
        - Khu vực, ngành nghề, loại khách hàng
        - Đánh giá tất cả nhân viên, so sánh và chọn người tốt nhất
        """
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.agent_helper import AgentHelper
            
            agent_helper = AgentHelper()
            
            # Lấy danh sách tất cả nhân viên để đánh giá
            agents_meta = []
            admin_user = self.env.ref('base.user_admin', raise_if_not_found=False)
            admin_domain = [('user_id', '!=', admin_user.id)] if admin_user else []
            for emp in self.env['hr.employee'].search(admin_domain):
                # Tính điểm KPI hiện tại của nhân viên (càng cao càng tốt, nhưng cần cân bằng tải)
                kpi_score = emp.diem_kpi if hasattr(emp, 'diem_kpi') and emp.diem_kpi else 0
                current_customer_count = self.env['qlkh.customer'].search_count([
                    ('nhan_vien_phu_trach_id', '=', emp.id)
                ])
                
                agents_meta.append({
                    'user_id': emp.id,
                    'name': emp.name,
                    'job': emp.job_id.name if emp.job_id else 'Unknown',
                    'department': emp.department_id.name if emp.department_id else 'Unknown',
                    'region': emp.work_location_id.name if hasattr(emp, 'work_location_id') and emp.work_location_id else 'Unknown',
                    'load': current_customer_count,  # Số lượng khách hàng đang phụ trách
                    'kpi_score': kpi_score,  # Điểm KPI hiện tại
                })
            
            # Gọi AI route_lead để đánh giá tất cả nhân viên
            route_result = agent_helper.route_lead({
                'area': area or 'Không xác định',
                'industry': industry or 'Không xác định',
                'customer_type': customer_type or 'Không xác định',
                'priority': priority or 'medium',
                'ai_score': ai_score,
                'ai_reason': ai_reason
            }, agents_meta=agents_meta)
            
            if route_result.get('confidence', 0.0) >= 0.65:  # Hạ ngưỡng xuống 0.65 để linh hoạt hơn
                employee_id = route_result.get('employee_id')
                if employee_id:
                    employee = self.env['hr.employee'].browse(employee_id)
                    if employee.exists():
                        return employee, route_result.get('confidence', 0.0), route_result.get('reason', '')
            
            # Fallback: Chọn nhân viên có ít khách hàng nhất (load balancing)
            employees_with_load = []
            for emp in self.env['hr.employee'].search(admin_domain):
                load = self.env['qlkh.customer'].search_count([('nhan_vien_phu_trach_id', '=', emp.id)])
                employees_with_load.append((emp, load))
            
            if employees_with_load:
                # Sắp xếp theo load tăng dần, chọn người có ít khách nhất
                employees_with_load.sort(key=lambda x: x[1])
                return employees_with_load[0][0], 0.0, 'Load balancing: nhân viên có ít khách hàng nhất'
            
            return None, 0.0, 'Không tìm thấy nhân viên phù hợp'
            
        except Exception as e:
            _logger.error(f'Lỗi tìm nhân viên phù hợp: {e}')
            return None, 0.0, str(e)


    def _reassign_employee_if_better(self, new_employee, new_confidence, new_reason):
        """So sánh và gán lại nhân viên nếu phù hợp hơn"""
        if not new_employee:
            return False
        
        current_employee = self.nhan_vien_phu_trach_id
        
        # Nếu chưa có nhân viên phụ trách -> gán luôn
        if not current_employee:
            self.write({'nhan_vien_phu_trach_id': new_employee.id})
            _logger.info('Gán nhân viên phụ trách mới cho %s: %s (confidence: %s, reason: %s)', 
                        self.name, new_employee.name, new_confidence, new_reason)
            return True
        
        # Nếu đã có, so sánh: chỉ gán lại nếu confidence > 0.8 và khác nhân viên hiện tại
        if new_confidence >= 0.8 and current_employee.id != new_employee.id:
            # Ghi log để theo dõi
            _logger.info('Có nhân viên phù hợp hơn cho %s: %s (confidence: %s) thay vì %s (cũ)',
                        self.name, new_employee.name, new_confidence, current_employee.name)
            
            # Có thể gửi thông báo cho quản lý về việc thay đổi phụ trách
            try:
                from smart_biz_services.notif_helper import NotifHelper
                notif = NotifHelper()
                notif.send_telegram_template(
                    'customer_reassigned',  # Cần thêm template này
                    customer_name=self.name,
                    old_employee=current_employee.name,
                    new_employee=new_employee.name,
                    reason=new_reason,
                    confidence=new_confidence
                )
            except Exception as e:
                _logger.error(f'Không thể gửi thông báo thay đổi phụ trách: {e}')
            
            self.write({'nhan_vien_phu_trach_id': new_employee.id})
            return True
        
        return False
    
    def _create_meeting(self, meeting_title, reason, duration_minutes=30):
        """
        Tạo Google Meet và gửi thông báo cho khách hàng
        
        Args:
            meeting_title: Tiêu đề cuộc họp
            reason: Lý do tạo cuộc họp
            duration_minutes: Thời lượng (phút)
        """
        if not self.email:
            _logger.warning(f'Không thể tạo meeting: khách hàng {self.name} không có email')
            return None
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
            from smart_biz_services.google_helper import GoogleHelper
            from smart_biz_services.notif_helper import NotifHelper
            
            google = GoogleHelper()
            notif = NotifHelper()
            
            # Tạo meeting
            meeting_link = google.create_meeting(
                customer_email=self.email,
                customer_name=self.name,
                title=meeting_title,
                duration_minutes=duration_minutes
            )
            
            if not meeting_link:
                _logger.error(f'Không thể tạo meeting cho {self.name}')
                return None
            
            # Gửi Telegram nội bộ
            notif.send_telegram_template(
                'meeting_created',
                customer_name=self.name,
                meeting_link=meeting_link,
                reason=reason,
                meeting_title=meeting_title
            )
            
            # Gửi Email cho khách hàng
            notif.send_email_template(
                'meeting_invitation',
                to_email=self.email,
                recipient_name=self.name.split()[0] if self.name else self.name,
                customer_name=self.name,
                meeting_link=meeting_link,
                title=meeting_title,
                reason=reason
            )
            
            _logger.info(f'Đã tạo meeting cho khách hàng {self.name}: {meeting_link}')
            
            # Tạo activity trong Odoo để theo dõi
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
            
            return meeting_link
            
        except Exception as e:
            _logger.error(f'Lỗi tạo meeting cho khách hàng {self.name}: {e}')
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

                # Lấy thông tin cũ và mới
                old_status = old_values.get(customer.id, {}).get('status', '')
                new_status = customer.status
                status_label = dict(self._fields['status'].selection).get(new_status, new_status)
                next_step = next_step_map.get(new_status, 'Chúng tôi sẽ cập nhật sau')

                # Gửi Telegram
                notif.send_telegram_template(
                    'customer_status_updated',
                    customer_name=customer.name,
                    old_status=old_status,
                    new_status=status_label,
                    employee_name=customer.nhan_vien_phu_trach_id.name or 'Đang xử lý',
                    next_step=next_step
                )

                # Gửi Email cho khách hàng (nếu có email và status không phải internal)
                if customer.email and new_status not in ['tiem_nang']:  # Chỉ gửi khi thực sự cần
                    notif.send_email_template(
                        'customer_status_updated',
                        to_email=customer.email,
                        recipient_name=customer.name.split()[0] if customer.name else customer.name,
                        customer_name=customer.name,
                        status_code=new_status,
                        employee_name=customer.nhan_vien_phu_trach_id.name or 'Đang xử lý',
                        next_step=next_step,
                        note=customer.note if customer.note else None
                    )
                # ========== THÊM ĐOẠN CODE NÀY VÀO CUỐI VÒNG LẶP for customer ==========
                # BỔ SUNG: Gửi thông báo khi thay đổi customer_type, industry, expected_revenue
                old_customer_type = old_values.get(customer.id, {}).get('customer_type', '')
                old_industry = old_values.get(customer.id, {}).get('industry', '')
                old_expected_revenue = old_values.get(customer.id, {}).get('expected_revenue', 0)
                
                if (old_customer_type != customer.customer_type or 
                    old_industry != customer.industry or 
                    old_expected_revenue != customer.expected_revenue):
                    
                    # Gửi Telegram thông báo nội bộ
                    changes = []
                    if old_customer_type != customer.customer_type:
                        old_label = dict(self._fields['customer_type'].selection).get(old_customer_type, old_customer_type)
                        new_label = dict(self._fields['customer_type'].selection).get(customer.customer_type, customer.customer_type)
                        changes.append(f"Loại KH: {old_label} → {new_label}")
                    if old_industry != customer.industry:
                        changes.append(f"Ngành nghề: {old_industry or 'trống'} → {customer.industry or 'trống'}")
                    if old_expected_revenue != customer.expected_revenue:
                        changes.append(f"Doanh thu KV: {old_expected_revenue:,.0f} → {customer.expected_revenue:,.0f} VNĐ")
                    
                    if changes:
                        change_text = "\n".join([f"• {c}" for c in changes])
                        notif.send_telegram(
                            chat_id=None,
                            title=f"📝 CẬP NHẬT THÔNG TIN KHÁCH HÀNG",
                            content=f"""👤 **Khách hàng**: {customer.name}
    📊 **Thay đổi**:
    {change_text}

    👨‍💼 **Phụ trách**: {customer.nhan_vien_phu_trach_id.name or 'Chưa phân công'}

    ⏰ {fields.Datetime.now().strftime('%H:%M %d/%m/%Y')}
    ━━━━━━━━━━━━━━━━━━━━━━━
    _SmartBiz - Cập nhật thông tin_"""
                        )
                        
                        # Nếu có thay đổi loại KH hoặc ngành nghề, đánh giá lại nhân viên phụ trách
                        if old_customer_type != customer.customer_type or old_industry != customer.industry:
                            new_employee, new_confidence, new_reason = customer._find_best_employee(
                                ai_score=customer.customer_score or 0,
                                ai_reason=f"Thay đổi thông tin: loại KH={customer.customer_type}, ngành={customer.industry}",
                                area=customer.area,
                                industry=customer.industry,
                                customer_type=dict(self._fields['customer_type'].selection).get(customer.customer_type, customer.customer_type),
                                priority=customer.priority or 'medium'
                            )
                            if new_employee:
                                customer._reassign_employee_if_better(new_employee, new_confidence, new_reason)
            except Exception as e:
                _logger.error(
                    'Không thể gửi thông báo khi trạng thái khách hàng thay đổi cho %s: %s',
                    customer.name,
                    e,
                    exc_info=True
                )

        return result
