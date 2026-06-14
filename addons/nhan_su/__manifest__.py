# -*- coding: utf-8 -*-
{
    'name': "Quản Lý Nhân Sự",
    'summary': """
        Quản lý các thông tin liên quan đến nhân sự
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'quan_ly_van_ban', 'quan_ly_khach_hang'],
    'data': [
        'security/ir.model.access.csv',
        'views/don_vi.xml',
        'views/chuc_vu.xml',
        'views/nhan_vien.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/ho_so_dien_tu.xml',
        'views/iot_project_assignment.xml',
        'views/dashboard.xml',  # Dashboard action và template
        'views/menu.xml',       # Menu
        'views/dashboard_templates.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard.xml',  # ĐỔI ĐƯỜNG DẪN - template nên để trong static
    ],
    'assets': {
        'web.assets_backend': [
            'nhan_su/static/src/css/hr_dashboard.css',
            'nhan_su/static/src/js/hr_dashboard.js',
            'nhan_su/static/src/xml/dashboard.xml',  # THÊM TEMPLATE VÀO ASSETS
        ],
        'web.assets_qweb': [
            'nhan_su/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}