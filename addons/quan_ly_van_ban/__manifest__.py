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
        'views/van_ban_views.xml',        # Views cho van_ban.document
        'views/van_ban_folder.xml',       # Views cho folder (THÊM MỚI)
        'views/van_ban_routing.xml',      # Views cho routing (THÊM MỚI)
        'views/van_ban_den.xml',
        'views/van_ban_di.xml',
        'views/loai_van_ban.xml',
        'views/menu.xml',                 # Menu và actions (ĐẶT CUỐI CÙNG)
    ],
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['pytesseract', 'Pillow', 'PyPDF2', 'pdf2image'],
    },
}