from odoo import fields, models


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    leave_request_id = fields.Many2one("hr.leave")

    def action_approve(self, approver=None):
        super().action_approve(approver)
        self.flush_model(["request_status"])
        approved = self.filtered(lambda r: r.request_status == "approved")
        approved.leave_request_id.sudo().action_approve()
