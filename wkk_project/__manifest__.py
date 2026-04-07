{
    "name": "WKK - Project",
    "summary": "WKK - Project Extension",
    "author": "Odoo PS",
    "website": "https://www.odoo.com",
    "category": "Services/Project",
    "version": "19.0.1.3.0",
    "license": "OEEL-1",
    "depends": ["sale_purchase_project", "sale_project", "hr", "wkk_approvals"],
    "data": [
        "data/ir_sequence_data.xml",
        "views/project_task_views.xml",
        "views/project_project_views.xml",
        "views/purchase_order_views.xml",
        "views/sale_order_views.xml",
        "wizards/project_template_create_wizard_views.xml",
    ],
    "task_ids": [6022465, 6022310],
}
