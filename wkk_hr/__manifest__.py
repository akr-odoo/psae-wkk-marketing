# -*- coding: utf-8 -*-
{
    'name': 'WKK - HR',
    'summary': 'WKK - HR Extension',
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'category': 'Human Resources',
    'version': '19.0.1.0.0',
    'license': 'OEEL-1',
    'depends': ['hr',],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_insurance_provider_views.xml',
        'views/hr_insurance_category_views.xml',
        'views/hr_insurance_allocation_views.xml',
        'views/hr_dependent_relation_views.xml',
        'views/hr_dependent_dependent_views.xml',
        'views/hr_menu_views.xml',
        'views/hr_employee_public_views.xml',
        'views/hr_employee_views.xml',
    ],
    'task_ids': [5128957, 5128958]
}

