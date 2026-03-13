# -*- coding: utf-8 -*-
{
    'name': 'WKK - Sales',
    'summary': 'WKK - Sales Extension',
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'category': 'Sales/Sales',
    'version': '19.0.2.1.0',
    'license': 'OEEL-1',
    'depends': ['wkk_approvals', 'sale_management'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'task_ids': [5110121, 5211287, 6022465]
}
