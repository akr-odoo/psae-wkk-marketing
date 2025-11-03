from odoo import fields, models


class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    approval_type = fields.Selection(selection_add=[("timeoff", "Time Off Approval")])
