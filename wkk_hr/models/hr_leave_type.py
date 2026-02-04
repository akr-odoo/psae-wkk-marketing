from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    approval_categ_id = fields.Many2one(
        "approval.category", string="Approval Categoery", domain=[("approval_type", "=", "timeoff")]
    )
