# -*- coding: utf-8 -*-
{
    'name': 'WKK - Account',
    'summary': 'WKK - Account Extension',
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'category': 'Accounting/Accounting',
    'version': '19.0.2.0.0',
    'license': 'OEEL-1',
    'depends': ['accountant', 'account_batch_payment', 'wkk_approvals'],
    'data': [
        'data/ir_cron.xml',
        'views/account_payment_views.xml',
        'views/account_batch_payment_views.xml',
        'views/account_journal_views.xml',
        'wizards/account_payment_register_views.xml',
    ],
    'task_ids': [5110120, 5211287]
}
