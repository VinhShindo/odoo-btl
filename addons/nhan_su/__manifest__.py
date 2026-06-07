# -*- coding: utf-8 -*-
{
    'name': "Quản Lý Nhân Sự",

    'summary': """
        Quản lý các thông tin liên quan đến nhân sự, bao gồm hồ sơ nhân viên, lịch sử công tác, chứng chỉ bằng cấp, phân công dự án IoT, và nhật ký thiết bị IoT.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'quan_ly_van_ban', 'quan_ly_khach_hang'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/chuc_vu.xml',
        'views/don_vi.xml',
        'views/nhan_vien.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/ho_so_dien_tu.xml',
        'views/menu.xml',
        'views/iot_project_assignment.xml',
        'views/iot_device_log.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
