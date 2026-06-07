# -*- coding: utf-8 -*-
{
    'name': 'Quản lý khách hàng',
    'version': '1.0',
    'category': 'CRM',
    'summary': 'Quản lý hồ sơ khách hàng, báo giá, hợp đồng, giao dịch, chăm sóc khách hàng',
    'description': 'Module quản lý khách hàng cho doanh nghiệp IoT',
    'license': 'LGPL-3',
    'author': 'Your Company',
    'website': 'http://yourcompany.com',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/customer.xml',
        'views/quotation.xml',
        'views/contract.xml',
        'views/customer_interaction.xml',
        'views/appointment.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
