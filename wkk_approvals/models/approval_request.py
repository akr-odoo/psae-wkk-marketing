from odoo import fields, models


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    vendor_id = fields.Many2one('res.partner', copy=False, domain=[('partner_type', 'in', ['vendor', 'both'])])

    def action_cancel(self):
        not_cancelled = self.filtered(lambda r: r.request_status != 'cancel' and r.approval_type == 'vendor_approval')
        super().action_cancel()
        self.flush_model(['request_status'])
        cancelled = self.filtered(lambda r: r.request_status == 'cancel')
        if vendors := (not_cancelled & cancelled).vendor_id:
            vendors.vendor_state = 'draft'

    def action_approve(self, approver=None):
        not_approved = self.filtered(lambda r: r.request_status != 'approved' and r.approval_type == 'vendor_approval')
        super().action_approve(approver)
        self.flush_model(['request_status'])
        approved = self.filtered(lambda r: r.request_status == 'approved')
        if vendors := (not_approved & approved).vendor_id:
            vendors.vendor_state = 'approved'

    def action_refuse(self, approver=None):
        not_refused = self.filtered(lambda r: r.request_status != 'refused' and r.approval_type == 'vendor_approval')
        super().action_refuse(approver)
        self.flush_model(['request_status'])
        refused = self.filtered(lambda r: r.request_status == 'refused')
        if vendors := (not_refused & refused).vendor_id:
            vendors.vendor_state = 'rejected'
