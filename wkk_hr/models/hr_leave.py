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

    def _prepare_approval_request_vals(self):
        self.ensure_one()
        return {
            "name": "Time Off Request",
            "request_owner_id": self.user_id.id,
            "category_id": self.holiday_status_id.approval_categ_id.id,
            "leave_request_id": self.id,
            "employee_id": self.employee_id.id,
            "date_start": self.date_from,
            "date_end": self.date_to,
            "reason": self.name,
        }

    def _sync_approval_request(self):
        for leave in self.filtered("approval_request_id"):
            leave.approval_request_id.with_context(
                skip_leave_approval_sync=True,
                tracking_disable=True,
            ).write({
                "employee_id": leave.employee_id.id,
                "date_start": leave.date_from,
                "date_end": leave.date_to,
                "reason": leave.name,
            })

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        leaves_with_approval = leaves.filtered("holiday_status_id.approval_categ_id")
        if not leaves_with_approval:
            return leaves

        request_ids = self.env["approval.request"].create([
            leave._prepare_approval_request_vals()
            for leave in leaves_with_approval
        ])
        for request in request_ids:
            request.leave_request_id.approval_request_id = request

        self.env["ir.attachment"].search([
            ("res_model", "=", "hr.leave"),
            ("res_id", "in", leaves_with_approval.ids),
        ])._copy_to_leave_approval_request()
        for request in request_ids:
            request.action_confirm()
        return leaves

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("skip_leave_approval_sync"):
            return res
        sync_fields = {
            "employee_id",
            "date_from",
            "date_to",
            "request_date_from",
            "request_date_to",
            "request_date_from_period",
            "request_hour_from",
            "request_hour_to",
            "request_unit_half",
            "request_unit_hours",
            "name",
        }
        if sync_fields & set(vals):
            self._sync_approval_request()
        return res

    def _inverse_supported_attachment_ids(self):
        removed_by_leave = {
            leave.id: leave.attachment_ids - leave.supported_attachment_ids
            for leave in self
        }
        super()._inverse_supported_attachment_ids()
        for leave in self:
            removed = removed_by_leave.get(leave.id)
            if removed and leave.approval_request_id:
                removed._unlink_matching_approval_attachments(leave.approval_request_id)

    def action_view_approval_request(self):
        return self.approval_request_id._get_records_action()

    def action_approve(self):
        return super(HrLeave, self.filtered("request_approved")).action_approve()

    def action_refuse(self):
        res = super().action_refuse()
        approvals = self.sudo().approval_request_id.filtered(
            lambda r: r.request_status in ("new", "pending")
        )
        approvals.mapped("approver_ids").filtered(
            lambda a: a.status in ("new", "pending", "waiting")
        ).write({"status": "refused"})
        return res
