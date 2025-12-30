# -*- coding: utf-8 -*-
{
    'name': "Zkteco Biopro Attendance",
    'summary': """
        Integrate Zkteco BioPro with attendances app via BioTime 8.5 & 9.0 API
    """,
    'description': '''
        System parameter "zkteco_auth_endpoint" takes the endpoint for authentication specified by the respective API documentation used. (e.g., '/api-token-auth/' & '/jwt-api-token-auth/').
        System parameter "zkteco_prefix" takes the prefix for using the generated token specified by the respective API documentation used. (e.g., 'Token' & 'JWT').
        Authentication Payload takes in a dictionary "{}" with the required payload information (e.g., {"username": "user123", "password": "mypassword"}) based on the API documentation.
    ''',
    'author': "Odoo PS",
    'website': "https://www.odoo.com",
    "version": "19.0.0.0.0",
    'license': 'OEEL-1',
    'depends': ['hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'data/config_parameter_data.xml',
        'views/biotime_server_views.xml',
        'views/hr_employee.xml',
        'views/hr_views.xml',
        'data/ir_cron_data.xml',
    ],
}
