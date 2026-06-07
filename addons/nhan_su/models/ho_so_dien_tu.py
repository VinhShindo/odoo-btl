from odoo import models, fields, api


class HoSoDienTu(models.Model):
    _name = 'nhan_su.ho_so_dien_tu'
    _description = 'Hồ sơ điện tử'
    _rec_name = 'ten_file'

    ho_so = fields.Char('Hồ sơ', required=True)
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    loai_ho_so = fields.Selection([
        ('cv', 'CV'),
        ('cccd', 'CCCD'),
        ('bang_cap', 'Bằng cấp'),
        ('hop_dong_lao_dong', 'Hợp đồng lao động')
    ], string='Loại hồ sơ', required=True)
    ten_file = fields.Char('Tên file', required=True)
    tep_dinh_kem = fields.Binary('Tệp đính kèm', attachment=True)
    ngay_dang_tai = fields.Date('Ngày đăng tải', default=fields.Date.context_today)
    van_ban_id = fields.Many2one('van_ban.document', string='Văn bản liên quan')
    note = fields.Text('Ghi chú')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_van_ban_document()
        return records

    def write(self, vals):
        result = super().write(vals)
        for record in self:
            record._create_van_ban_document()
        return result

    def _create_van_ban_document(self):
        """Tự động tạo document trong van_ban khi hồ sơ được tạo/update"""
        self.ensure_one()

        # Nếu chưa có file, không tạo document
        if not self.tep_dinh_kem:
            return

        # Tìm folder của nhân viên
        nhan_vien = self.nhan_vien_id
        if not nhan_vien.folder_id:
            # Nếu chưa có folder, tạo folder
            nhan_vien._create_employee_folder()

        folder_id = nhan_vien.folder_id

        # Ánh xạ loại hồ sơ sang doc_type
        doc_type_map = {
            'cv': 'khac',
            'cccd': 'khac',
            'bang_cap': 'khac',
            'hop_dong_lao_dong': 'hop_dong'
        }

        # Kiểm tra xem đã có document cho hồ sơ này không
        if self.van_ban_id:
            # Update document hiện tại
            self.van_ban_id.write({
                'file': self.tep_dinh_kem,
                'file_name': self.ten_file,
                'note': f"{self.note}\n\n[Từ hồ sơ: {dict(self._fields['loai_ho_so'].selection).get(self.loai_ho_so, 'Hồ sơ')}]"
            })
        else:
            # Tạo document mới
            loai_text = dict(self._fields['loai_ho_so'].selection).get(self.loai_ho_so, 'Hồ sơ')
            doc_vals = {
                'name': f"{nhan_vien.ho_va_ten or nhan_vien.name} - {loai_text}",
                'doc_type': doc_type_map.get(self.loai_ho_so, 'khac'),
                'nhan_vien_id': nhan_vien.id,
                'file': self.tep_dinh_kem,
                'file_name': self.ten_file,
                'folder_id': folder_id.id,
                'status': 'draft',
                'source_module': 'hrm',
                'note': self.note
            }
            
            doc = self.env['van_ban.document'].create(doc_vals)
            self.van_ban_id = doc.id

            if doc and doc.file:
                try:
                    doc.action_scan_ocr()
                except Exception:
                    pass
