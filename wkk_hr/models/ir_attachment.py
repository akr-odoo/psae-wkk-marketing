from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    source_leave_attachment_id = fields.Many2one(
        "ir.attachment",
        index=True,
        ondelete="set null",
        copy=False,
    )

    def _leave_attachments_approval_map(self):
        """Return leave attachments and {leave_id: approval.request} for those with a linked approval."""
        leave_attachments = self.filtered(lambda a: a.res_model == "hr.leave" and a.res_id)
        if not leave_attachments:
            return leave_attachments, {}
        leaves = self.env["hr.leave"].browse(leave_attachments.mapped("res_id"))
        approval_by_leave = {
            leave.id: leave.approval_request_id
            for leave in leaves
            if leave.approval_request_id
        }
        leave_attachments = leave_attachments.filtered(lambda a: a.res_id in approval_by_leave)
        return leave_attachments, approval_by_leave

    def _copy_to_leave_approval_request(self):
        leave_attachments, approval_by_leave = self._leave_attachments_approval_map()
        if not leave_attachments:
            return
        already_copied = set(self.search([
            ("source_leave_attachment_id", "in", leave_attachments.ids),
        ]).mapped("source_leave_attachment_id").ids)
        for attachment in leave_attachments:
            if attachment.id in already_copied:
                continue
            attachment.with_context(no_document=True).copy({
                "res_model": "approval.request",
                "res_id": approval_by_leave[attachment.res_id].id,
                "source_leave_attachment_id": attachment.id,
            })

    def _unlink_matching_approval_attachments(self, approval=None):
        """Unlink approval attachments that were copied from these leave attachments."""
        if not self:
            return
        domain = [
            ("source_leave_attachment_id", "in", self.ids),
            ("res_model", "=", "approval.request"),
        ]
        if approval:
            domain.append(("res_id", "=", approval.id))
        to_unlink = self.search(domain)
        if to_unlink:
            to_unlink.with_context(skip_leave_approval_attachment_sync=True).unlink()

    def _unlink_from_leave_approval_request(self):
        self._unlink_matching_approval_attachments()

    @api.model_create_multi
    def create(self, vals_list):
        attachments = super().create(vals_list)
        if not self.env.context.get("skip_leave_approval_attachment_sync"):
            attachments._copy_to_leave_approval_request()
        return attachments

    def write(self, vals):
        res = super().write(vals)
        if (
            not self.env.context.get("skip_leave_approval_attachment_sync")
            and {"res_model", "res_id"} & set(vals)
        ):
            self._copy_to_leave_approval_request()
        return res

    def unlink(self):
        if not self.env.context.get("skip_leave_approval_attachment_sync"):
            self._unlink_from_leave_approval_request()
        return super().unlink()
