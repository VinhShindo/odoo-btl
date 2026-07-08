from odoo import models, fields, api
import logging
import os
import sys


class HoSoDienTu(models.Model):
    _name = 'nhan_su.ho_so_dien_tu'
    _description = 'Hồ sơ điện tử'
    _rec_name = 'ten_file'

    ho_so = fields.Char('Hồ sơ', required=True)
    nhan_vien_id = fields.Many2one('hr.employee', string='Nhân viên', required=False, ondelete='set null')
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

        if not self.tep_dinh_kem:
            return

        nhan_vien = self.nhan_vien_id
        if not nhan_vien:
            return

        if not nhan_vien.folder_id:
            nhan_vien._create_employee_folder()

        metadata = self.env['van_ban.document']._get_default_document_metadata(
            employee=nhan_vien,
            doc_type='hop_dong' if self.loai_ho_so == 'hop_dong_lao_dong' else 'khac'
        )

        doc_type_map = {
            'cv': 'khac',
            'cccd': 'khac',
            'bang_cap': 'khac',
            'hop_dong_lao_dong': 'hop_dong'
        }
        doc_type = doc_type_map.get(self.loai_ho_so, 'khac')

        loai_text = dict(self._fields['loai_ho_so'].selection).get(self.loai_ho_so, 'Hồ sơ')
        note_text = f"{self.note}\n\n[Từ hồ sơ: {loai_text}]" if self.note else f"[Từ hồ sơ: {loai_text}]"

        doc_vals = {
            'name': f"{nhan_vien.ho_va_ten or nhan_vien.name} - {loai_text}",
            'doc_type': doc_type,
            'nhan_vien_id': nhan_vien.id,
            'file': self.tep_dinh_kem,
            'file_name': self.ten_file,
            'status': 'draft',
            'source_module': 'hrm',
            'note': note_text,
        }
        doc_vals.update(metadata)

        if self.van_ban_id:
            self.van_ban_id.write({
                **doc_vals,
                'note': note_text,
            })
            doc = self.van_ban_id
        else:
            doc = self.env['van_ban.document'].create(doc_vals)
            self.van_ban_id = doc.id

        if doc and doc.file:
            try:
                # Only run OCR if it hasn't completed yet
                try:
                    ocr_done = getattr(doc, 'ocr_status', None) == 'completed'
                except Exception:
                    ocr_done = False

                if not ocr_done:
                    try:
                        doc.action_scan_ocr()
                    except Exception:
                        logging.getLogger(__name__).exception('OCR failed for document %s', doc.id)

                # Send notification about employee document update with AI summary
                try:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../addons'))
                    from smart_biz_services.ai_helper import AIHelper
                    from smart_biz_services.notif_helper import NotifHelper

                    ai = AIHelper()
                    notif = NotifHelper()

                    summary = ''
                    if getattr(doc, 'ocr_text', None):
                        try:
                            summary = ai.summarize_document(doc.ocr_text, max_length=200)
                        except Exception:
                            summary = (doc.ocr_text or '')[:400]
                    else:
                        summary = doc.note or doc.file_name or doc.name

                    try:
                        notif.send_telegram_template(
                            'employee_document_updated',
                            employee_name=nhan_vien.ho_va_ten or nhan_vien.name,
                            doc_name=doc.name,
                            doc_summary=summary
                        )
                        if nhan_vien and getattr(nhan_vien, 'work_email', None):
                            notif.send_email_template(
                                'employee_document_updated',
                                to_email=nhan_vien.work_email,
                                recipient_name=nhan_vien.ho_va_ten or nhan_vien.name,
                                employee_name=nhan_vien.ho_va_ten or nhan_vien.name,
                                doc_name=doc.name,
                                doc_summary=summary
                            )
                    except Exception:
                        logging.getLogger(__name__).exception('Không thể gửi thông báo cập nhật hồ sơ nhân viên cho document %s', doc.id)
                except Exception:
                    logging.getLogger(__name__).exception('Không thể xử lý AI/notify cho document %s', doc.id)
            except Exception:
                pass
