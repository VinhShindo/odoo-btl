{
    'name': 'Quản lý văn bản',
    'version': '2.0',
    'category': 'Document Management',
    'summary': 'Quản lý văn bản với OCR cho PDF và ảnh',
    'description': 'Module quản lý văn bản hỗ trợ OCR cho PDF và ảnh, lưu trữ đầy đủ',
    'author': 'FIT-DNU',
    'website': 'https://ttdn1501.aiotlabdnu.xyz/web',
    'depends': ['base', 'quan_ly_khach_hang', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/van_ban_views.xml',
        'views/van_ban_folder.xml',
        'views/van_ban_folder_explorer.xml',
        'views/van_ban_routing.xml',
        'views/van_ban_den.xml',
        'views/van_ban_di.xml',
        'views/loai_van_ban.xml',
        'views/dashboard.xml',
        'views/menu.xml',
        'views/dashboard_templates.xml',
    ],
    'models': [
        'models/models.py',
        'models/van_ban_dashboard_helper.py',   # Đã đổi tên file Helper
    ],
    'controllers': [
        'controllers/doc_dashboard.py',          # Đã đổi tên file Controller
    ],
    'qweb': [
        'static/src/xml/document_dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'quan_ly_van_ban/static/src/css/folder.css',
            'quan_ly_van_ban/static/src/css/document_dashboard.css',  
            'quan_ly_van_ban/static/src/js/folder_explorer.js',
            'quan_ly_van_ban/static/src/js/van_ban_dashboard.js',   # Đã đổi tên file JS
            'quan_ly_van_ban/static/src/xml/document_dashboard.xml',
            'quan_ly_van_ban/static/src/xml/folder_explorer.xml',
        ],
        'web.assets_qweb': [
            'quan_ly_van_ban/static/src/xml/document_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['pytesseract', 'Pillow', 'PyPDF2', 'pdf2image'],
    },
}