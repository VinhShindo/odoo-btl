from odoo import models, fields, api

class VanBanFolder(models.Model):
    _name = 'van_ban.folder'
    _description = 'Thư mục văn bản'
    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Tên thư mục', required=True)
    parent_id = fields.Many2one('van_ban.folder', string='Thư mục cha', index=True, ondelete='cascade')
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('van_ban.folder', 'parent_id', string='Thư mục con')
    document_ids = fields.One2many('van_ban.document', 'folder_id', string='Tài liệu')
    document_count = fields.Integer('Số tài liệu', compute='_compute_document_count')
    complete_name = fields.Char('Đường dẫn đầy đủ', compute='_compute_complete_name', store=True, recursive=True)
    folder_type = fields.Selection([
        ('customer','Khách hàng'),
        ('employee','Nhân viên'),
        ('document_type','Loại văn bản'),
        ('department','Phòng ban'),
        ('general','Chung')
    ], string='Loại thư mục', default='general')
    
    folder_group = fields.Selection([
        ('employee','Nhân viên'),
        ('department','Phòng ban'),
        ('common','Chung')
    ], string='Cột nhóm', compute='_compute_folder_group', store=True)
    
    kanban_group = fields.Char(string='Nhóm Kanban', compute='_compute_kanban_group', store=True)

    @api.depends('folder_type')
    def _compute_folder_group(self):
        for rec in self:
            if rec.folder_type == 'employee':
                rec.folder_group = 'employee'
            elif rec.folder_type == 'department':
                rec.folder_group = 'department'
            else:
                rec.folder_group = 'common'

    @api.depends('folder_type', 'parent_id', 'parent_id.folder_type')
    def _compute_kanban_group(self):
        """
        Tính toán tên cột hiển thị trên Kanban View:
        1. Chung/ Danh mục => Cột: 'Danh mục dùng chung'
        2. Phòng ban => Cột: 'Nhân viên'
        3. Nhân viên => Cột: Tên Phòng ban trực thuộc (cha gần nhất thuộc loại department)
        """
        for rec in self:
            # 1. Các thư mục gốc (Hợp đồng, Danh mục chung, Văn bản khác...) -> Cột Danh mục dùng chung
            if rec.folder_type in ('general', 'document_type', 'customer'):
                rec.kanban_group = 'Danh mục dùng chung'
            
            # 2. Thư mục Phòng ban (R&D, PMO...) -> Cột Nhân viên
            elif rec.folder_type == 'department':
                rec.kanban_group = 'Nhân viên'
            
            # 3. Thư mục Nhân viên (NV001...) -> Cột là tên Phòng ban cha
            elif rec.folder_type == 'employee':
                dept = rec.parent_id
                while dept:
                    if dept.folder_type == 'department':
                        rec.kanban_group = dept.name
                        break
                    dept = dept.parent_id
                # Trường hợp nhân viên không thuộc phòng ban nào, dồn vào cột Nhân viên chung
                if not dept:
                    rec.kanban_group = 'Nhân viên'
            
            # Mặc định
            else:
                rec.kanban_group = 'Danh mục dùng chung'

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for rec in self:
            if rec.parent_id:
                rec.complete_name = f"{rec.parent_id.complete_name or rec.parent_id.name} / {rec.name}"
            else:
                rec.complete_name = rec.name

    @api.model_create_multi
    def create(self, vals_list):
        """
        Ghi đè hàm tạo mới: Khi tạo một thư mục Nhân viên, 
        hệ thống sẽ tự động sinh thêm 3 thư mục con (Hồ sơ cá nhân, Hợp đồng báo giá, Chứng chỉ)
        """
        records = super(VanBanFolder, self).create(vals_list)
        for record in records:
            if record.folder_type == 'employee':
                subfolders = [
                    {'name': 'Hồ sơ cá nhân', 'folder_type': 'employee', 'parent_id': record.id},
                    {'name': 'Hợp đồng báo giá', 'folder_type': 'employee', 'parent_id': record.id},
                    {'name': 'Chứng chỉ, bằng cấp', 'folder_type': 'employee', 'parent_id': record.id}
                ]
                existing_names = record.child_ids.mapped('name')
                for val in subfolders:
                    if val['name'] not in existing_names:
                        self.env['van_ban.folder'].create(val)
        return records