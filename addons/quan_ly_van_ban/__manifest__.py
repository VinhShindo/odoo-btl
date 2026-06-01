{
    'name': 'Quản lý văn bản',
    'version': '2.0',
    'category': 'Document Management',
    'summary': 'Quản lý văn bản với OCR cho PDF và ảnh',
    'description': 'Module quản lý văn bản hỗ trợ OCR cho PDF và ảnh, lưu trữ đầy đủ',
    'author': 'FIT-DNU',
    'website': 'https://ttdn1501.aiotlabdnu.xyz/web',
    'depends': ['base', 'nhan_su', 'quan_ly_khach_hang', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/van_ban_views.xml',
        'views/van_ban_folder.xml',  # File này chứa model và views cho folder
        'views/van_ban_folder_explorer.xml',
        'views/van_ban_routing.xml',
        'views/van_ban_den.xml',
        'views/van_ban_di.xml',
        'views/loai_van_ban.xml',
        'views/menu.xml',  # Menu nên ở cuối cùng
    ],
    'assets': {
        'web.assets_backend': [
            'quan_ly_van_ban/static/src/css/folder.css',
            'quan_ly_van_ban/static/src/js/folder_explorer.js',
            'quan_ly_van_ban/static/src/xml/folder_explorer.xml',
        ],
    },
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['pytesseract', 'Pillow', 'PyPDF2', 'pdf2image'],
    },
}