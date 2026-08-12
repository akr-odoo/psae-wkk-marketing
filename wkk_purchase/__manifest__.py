{
    "name": "WKK - Purchase",
    "summary": "WKK - Purchase Extension",
    "author": "Odoo PS",
    "website": "https://www.odoo.com",
    "category": "Purchase/Purchase",
    "version": "19.0.1.1.0",
    "license": "OEEL-1",
    "depends": ["wkk_approvals", "project_purchase"],
    "data": [
        "views/purchase_order_views.xml",
        "report/purchase_quotation_templates.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "wkk_purchase/static/src/scss/report.scss",
        ],
    },
    "task_ids": [5211287, 6431144],
}
