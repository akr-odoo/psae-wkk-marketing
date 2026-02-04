from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    approval_request_id = fields.Many2one("approval.request")
    request_approved = fields.Boolean(compute="_compute_request_approved", store=True)

    @api.depends("approval_request_id.request_status")
    def _compute_request_approved(self):
        for leave in self:
            leave.request_approved = (
                not leave.holiday_status_id.approval_categ_id
                or not leave.approval_request_id
                or leave.approval_request_id.request_status == "approved"
            )

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        request_vals_list = [
            {
                "name": "Time Off Request",
                "request_owner_id": leave.user_id.id,
                "category_id": leave.holiday_status_id.approval_categ_id.id,
                "leave_request_id": leave.id,
            }
            for leave in leaves.filtered("holiday_status_id.approval_categ_id")
        ]
        request_ids = self.env["approval.request"].create(request_vals_list)

        for request in request_ids:
            request.action_confirm()
            request.leave_request_id.approval_request_id = request

        return leaves

    def action_view_approval_request(self):
        return self.approval_request_id._get_records_action()

    def action_approve(self):
        return super(HrLeave, self.filtered("request_approved")).action_approve()
