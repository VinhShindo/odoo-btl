import logging
import os
import sys

from numpy import record

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class NhanVien(models.Model):
    _inherit = 'hr.employee'  # Kế thừa từ model chuẩn Odoo
    _description = 'Bảng chứa thông tin nhân viên mở rộng'

    ma_dinh_danh = fields.Char("Mã định danh", required=False)
    ho_ten_dem = fields.Char("Họ tên đệm")
    ten = fields.Char("Tên")
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    que_quan = fields.Char("Quê quán")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    so_nguoi_bang_tuoi = fields.Integer("Số người bằng tuổi", compute="_compute_so_nguoi_bang_tuoi", store=True)
    don_vi_id = fields.Many2one('don_vi', string='Phòng ban / Đơn vị')
    so_khach_hang_phu_trach = fields.Integer('Số khách hàng phụ trách', compute='_compute_quan_ly_khach_hang', store=False)
    so_bao_gia = fields.Integer('Số báo giá', compute='_compute_quan_ly_khach_hang', store=False)
    so_hop_dong = fields.Integer('Số hợp đồng', compute='_compute_quan_ly_khach_hang', store=False)
    so_van_ban_xu_ly = fields.Integer('Số văn bản xử lý', compute='_compute_quan_ly_khach_hang', store=False)
    diem_kpi = fields.Float('Điểm KPI', compute='_compute_quan_ly_khach_hang', store=False)
    muc_tieu_doanh_so = fields.Float('Mục tiêu doanh số', compute='_compute_quan_ly_khach_hang', store=False)
    tien_do_kpi = fields.Float('Tiến độ KPI', compute='_compute_quan_ly_khach_hang', store=False)
    ghi_chu_nhan_su = fields.Text('Ghi chú nhân sự', compute='_compute_quan_ly_khach_hang', store=False)
    lich_su_cong_tac_ids = fields.One2many('lich_su_cong_tac', 'nhan_vien_id', string='Lịch sử công tác')
    danh_sach_chung_chi_bang_cap_ids = fields.One2many('danh_sach_chung_chi_bang_cap', 'nhan_vien_id', string='Danh sách chứng chỉ bằng cấp')
    document_ids = fields.One2many(
        'van_ban.document',
        'nhan_vien_id'
    )
    folder_id = fields.Many2one('van_ban.folder', string='Thư mục hồ sơ nhân viên', readonly=True)
    ho_so_dien_tu_ids = fields.One2many(
        'nhan_su.ho_so_dien_tu',
        'nhan_vien_id',
        string='Hồ sơ điện tử'
    )
    chuc_vu_id = fields.Many2one('chuc_vu', string='Chức vụ', ondelete='set null')

    @api.model
    def _get_employee_domain_exclude_admin(self):
        """Get domain to exclude admin user from employee records"""
        admin_user = self.env.ref('base.user_admin', raise_if_not_found=False)
        if admin_user:
            return [('user_id', '!=', admin_user.id)]
        return []

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override search to automatically exclude admin user"""
        # Thêm domain để bỏ qua admin user
        admin_domain = self._get_employee_domain_exclude_admin()
        if admin_domain:
            args = args + admin_domain
        return super().search(args, offset=offset, limit=limit, order=order, count=count)

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten
            elif record.ten:
                record.ho_va_ten = record.ten
            else:
                record.ho_va_ten = record.ho_ten_dem or ''

    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                domain = [
                    ('tuoi', '=', record.tuoi),
                    ('user_id', '!=', self.env.ref('base.user_admin', raise_if_not_found=False).id if self.env.ref('base.user_admin', raise_if_not_found=False) else 0)
                ]
                if isinstance(record.id, int):
                    domain.append(('id', '!=', record.id))
                records = self.env['hr.employee'].search(domain)
                record.so_nguoi_bang_tuoi = len(records)
            else:
                record.so_nguoi_bang_tuoi = 0

    @api.depends("birthday")
    def _compute_tuoi(self):
        for record in self:
            if record.birthday:
                year_now = date.today().year
                record.tuoi = year_now - record.birthday.year
            else:
                record.tuoi = 0

    @api.depends()
    def _compute_quan_ly_khach_hang(self):
        for record in self:
            customers = self.env['qlkh.customer'].search([('nhan_vien_phu_trach_id', '=', record.id)])
            record.so_khach_hang_phu_trach = len(customers)
            record.so_bao_gia = self.env['qlkh.quotation'].search_count([('customer_id.nhan_vien_phu_trach_id', '=', record.id)])
            record.so_hop_dong = self.env['qlkh.contract'].search_count([('customer_id.nhan_vien_phu_trach_id', '=', record.id)])
            docs = self.env['van_ban.document'].search([
                '|',
                ('nhan_vien_id', '=', record.id),
                ('customer_id', 'in', customers.ids)
            ])
            record.so_van_ban_xu_ly = len(docs)
            record.diem_kpi = record.so_hop_dong * 10.0 + record.so_bao_gia * 2.0
            record.muc_tieu_doanh_so = record.so_hop_dong * 1000000.0 + record.so_khach_hang_phu_trach * 500000.0
            record.tien_do_kpi = record.diem_kpi * 100.0 if record.diem_kpi else 0.0
            record.ghi_chu_nhan_su = (
                f"Tổng số khách hàng: {record.so_khach_hang_phu_trach}. "
                f"Báo giá: {record.so_bao_gia}. "
                f"Hợp đồng: {record.so_hop_dong}. "
                f"Văn bản xử lý: {record.so_van_ban_xu_ly}."
            )

    @api.model
    def default_get(self, fields_list):
        """Đảm bảo name luôn có giá trị khi form khởi tạo"""
        res = super().default_get(fields_list)
        # Nếu chưa có name, tạo từ ho_ten_dem và ten
        if 'name' not in fields_list or not res.get('name'):
            ho_ten_dem = res.get('ho_ten_dem', '')
            ten = res.get('ten', '')
            if ho_ten_dem and ten:
                res['name'] = f"{ho_ten_dem} {ten}"
            elif ten:
                res['name'] = ten
            else:
                res['name'] = "Nhân viên mới"
        return res

    @api.model_create_multi
    def create(self, vals_list):
        # In log để kiểm tra (bạn có thể xem trong terminal)
        _logger.info("vals_list trước khi create: %s", vals_list)

        for vals in vals_list:
            if not vals.get('name'):
                ho_ten_dem = vals.get('ho_ten_dem', '')
                ten = vals.get('ten', '')
                if ho_ten_dem and ten:
                    vals['name'] = f"{ho_ten_dem} {ten}"
                elif ten:
                    vals['name'] = ten
                else:
                    vals['name'] = "Nhân viên mới"

        records = super().create(vals_list)

        for rec in records:
            _logger.info("Nhân viên tạo thành công: ID=%s, Name=%s", rec.id, rec.name)

        # Phần tạo thư mục và gửi thông báo giữ nguyên
        for record in records:
            record._create_employee_folder()
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.agent_helper import AgentHelper
                from smart_biz_services.notif_helper import NotifHelper

                agent = AgentHelper()
                notif = NotifHelper()

                suggested = []
                try:
                    suggested = agent.generate_employee_folder_structure(record.ho_va_ten or record.name or f'Nhân viên {record.id}')
                except Exception:
                    suggested = []

                if suggested and record.folder_id:
                    for name in suggested:
                        try:
                            exists = self.env['van_ban.folder'].search([
                                ('name', '=', name),
                                ('parent_id', '=', record.folder_id.id)
                            ], limit=1)
                            if not exists:
                                self.env['van_ban.folder'].create({
                                    'name': name,
                                    'parent_id': record.folder_id.id,
                                    'folder_type': 'employee'
                                })
                        except Exception:
                            _logger.exception('Không tạo được thư mục phụ: %s', name)

                try:
                    notif.send_telegram_template(
                        'employee_created',
                        employee_name=record.ho_va_ten or record.name,
                        department=record.don_vi_id.ten_don_vi if record.don_vi_id else 'Chưa phân công',
                        job_title=record.chuc_vu_id.ten_chuc_vu if record.chuc_vu_id else 'Chưa phân công'
                    )
                    if record.work_email:
                        notif.send_email_template(
                            'employee_created',
                            to_email=record.work_email,
                            recipient_name=record.name,
                            employee_name=record.ho_va_ten or record.name,
                            department=record.don_vi_id.ten_don_vi if record.don_vi_id else 'Chưa phân công',
                            job_title=record.chuc_vu_id.ten_chuc_vu if record.chuc_vu_id else 'Chưa phân công'
                        )
                except Exception as e:
                    _logger.error('Không thể gửi thông báo tạo nhân viên: %s', e, exc_info=True)
            except Exception:
                _logger.exception('Lỗi khi gọi service tạo cấu trúc thư mục nhân viên')

        return records

    def write(self, vals):
        # Theo dõi các trường thay đổi để kích hoạt thông báo
        employees = self
        old_values = {
            rec.id: {
                'don_vi_id': rec.don_vi_id.id if rec.don_vi_id else False,
                'chuc_vu_id': rec.chuc_vu_id.id if rec.chuc_vu_id else False,
                'job_id': rec.job_id.id if rec.job_id else False,
            }
            for rec in employees
        }

        result = super().write(vals)

        # Chỉ tiếp tục nếu có thay đổi ở don_vi_id hoặc chuc_vu_id
        if not any(k in vals for k in ('don_vi_id', 'chuc_vu_id')):
            return result

        for rec in self:
            old_dv = old_values.get(rec.id, {}).get('don_vi_id')
            old_cv = old_values.get(rec.id, {}).get('chuc_vu_id')
            new_dv = rec.don_vi_id.id if rec.don_vi_id else False
            new_cv = rec.chuc_vu_id.id if rec.chuc_vu_id else False

            if old_dv == new_dv and old_cv == new_cv:
                continue

            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                from smart_biz_services.notif_helper import NotifHelper

                notif = NotifHelper()

                employee_name = rec.ho_va_ten or rec.name or f'Nhân viên {rec.id}'
                dept = rec.don_vi_id.ten_don_vi if rec.don_vi_id else 'Chưa có'
                job = rec.chuc_vu_id.ten_chuc_vu if rec.chuc_vu_id else 'Chưa có'
                manager = rec.parent_id.name if rec.parent_id else 'Chưa có'

                try:
                    telegram_success = notif.send_telegram_template(
                        'employee_updated',
                        employee_name=employee_name,
                        department=dept,
                        job_title=job,
                        manager=manager
                    )
                    
                    if telegram_success:
                        _logger.info(f"📤 Telegram updated sent for {employee_name}")
                    else:
                        _logger.warning(f"📤 Telegram updated failed for {employee_name} (template missing or error)")
                        
                except Exception:
                    _logger.exception('Gửi telegram thất bại cho nhân viên %s', employee_name)

                try:
                    if rec.work_email:
                        notif.send_email_template(
                            'employee_updated',
                            to_email=rec.work_email,
                            recipient_name=rec.name,
                            employee_name=employee_name,
                            department=dept,
                            job_title=job,
                            manager=manager
                        )
                        _logger.info(f"📧 Email updated sent to {rec.work_email}")
                except Exception:
                    _logger.exception('Gửi email thất bại cho nhân viên %s', employee_name)

            except Exception:
                _logger.exception('Lỗi khi xử lý notification sau write cho nhân viên %s', rec.id)

        return result

    def _clear_custom_employee_references(self):
        """Clear related custom model references when employee is archived or deleted."""
        if not self:
            return
        employee_ids = self.ids
        self.env['qlkh.customer'].search([('nhan_vien_phu_trach_id', 'in', employee_ids)]).write({'nhan_vien_phu_trach_id': False})
        self.env['qlkh.customer_interaction'].search([('nhan_vien_id', 'in', employee_ids)]).write({'nhan_vien_id': False})
        self.env['qlkh.appointment'].search([('nhan_vien_id', 'in', employee_ids)]).write({'nhan_vien_id': False})
        self.env['van_ban.document'].search([('nhan_vien_id', 'in', employee_ids)]).write({'nhan_vien_id': False})
        self.env['van_ban_di'].search([('nhan_vien_tao_id', 'in', employee_ids)]).write({'nhan_vien_tao_id': False})
        self.env['van_ban_di'].search([('nhan_vien_ky_id', 'in', employee_ids)]).write({'nhan_vien_ky_id': False})
        self.env['van_ban_den'].search([('nhan_vien_nhan_id', 'in', employee_ids)]).write({'nhan_vien_nhan_id': False})
        self.env['van_ban_den'].search([('nhan_vien_chuyen_id', 'in', employee_ids)]).write({'nhan_vien_chuyen_id': False})
        self.env['van_ban.routing'].search([('assigned_to', 'in', employee_ids)]).write({'assigned_to': False})
        self.env['nhan_su.ho_so_dien_tu'].search([('nhan_vien_id', 'in', employee_ids)]).write({'nhan_vien_id': False})

    def toggle_active(self):
        employees_to_archive = self.filtered(lambda e: e.active)
        result = super().toggle_active()
        archived_employees = employees_to_archive.filtered(lambda e: not e.active)
        if archived_employees:
            archived_employees._clear_custom_employee_references()
        return result

    def unlink(self):
        self._clear_custom_employee_references()
        return super().unlink()

    def _create_employee_folder(self):
        """Tự động tạo thư mục hồ sơ nhân viên khi tạo nhân viên mới"""
        self.ensure_one()
        
        # Tìm hoặc tạo folder "Nhân viên" gốc
        employee_root = self.env['van_ban.folder'].search([
            ('name', '=', 'Nhân viên'),
            ('parent_id', '=', False)
        ], limit=1)
        
        if not employee_root:
            employee_root = self.env['van_ban.folder'].create({
                'name': 'Nhân viên',
                'folder_type': 'employee'
            })
        
        # Tìm hoặc tạo folder phòng ban
        don_vi_name = self.don_vi_id.ten_don_vi if self.don_vi_id else 'Không xác định'
        don_vi_folder = self.env['van_ban.folder'].search([
            ('name', '=', don_vi_name),
            ('parent_id', '=', employee_root.id)
        ], limit=1)
        
        if not don_vi_folder:
            don_vi_folder = self.env['van_ban.folder'].create({
                'name': don_vi_name,
                'parent_id': employee_root.id,
                'folder_type': 'employee'
            })
        
        # Tạo folder nhân viên chính và tự động sinh thư mục con
        employee_name = self.ho_va_ten or self.name or f"Nhân viên {self.id}"
        employee_folder = self.env['van_ban.folder'].with_context(create_employee_subfolders=True).create({
            'name': employee_name,
            'parent_id': don_vi_folder.id,
            'folder_type': 'employee'
        })
        
        # Lưu reference - dùng write để chắc chắn save vào database
        self.write({'folder_id': employee_folder.id})
