from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    approval_type = fields.Selection(selection_add=[("timeoff", "Time Off Approval")])

    @api.onchange("approval_type")
    def _onchange_approval_type_timeoff(self):
        if self.approval_type == "timeoff":
            self.has_period = "required"

    @api.constrains("approval_type", "has_period")
    def _check_timeoff_requires_period(self):
        for category in self:
            if category.approval_type == "timeoff" and category.has_period != "required":
                raise ValidationError(_("Time Off approval categories must require a period."))
