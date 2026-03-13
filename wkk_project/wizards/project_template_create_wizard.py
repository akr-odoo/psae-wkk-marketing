from odoo import fields, models


class ProjectTemplateCreateWizard(models.TransientModel):
    _inherit = "project.template.create.wizard"

    project_reference = fields.Char(copy=False)
    referred_by = fields.Selection(
        [("employee", "Employee"), ("manager", "Manager"), ("third_party", "Third Party"), ("others", "Others")],
        copy=False,
    )
    referred_name = fields.Char(copy=False)
    referred_employee = fields.Many2one("hr.employee.public", copy=False)
    priority = fields.Selection(
        [("critical", "Critical"), ("high", "High"), ("medium", "Medium"), ("low", "Low")], copy=False
    )
    rfp_file_name = fields.Char(readonly=True)
    rfp_upload_file = fields.Binary(string="RFP Upload File")

    def _get_template_whitelist_fields(self):
        return super()._get_template_whitelist_fields() + [
            "referred_by",
            "referred_name",
            "referred_employee",
            "priority",
            "project_reference",
            "rfp_upload_file",
        ]
