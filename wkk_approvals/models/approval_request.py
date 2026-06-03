from odoo import Command, api, fields, models
from odoo.tools.safe_eval import safe_eval


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    vendor_id = fields.Many2one('res.partner', copy=False)
    res_model = fields.Char(string='Origin Model', readonly=True, help="Model of the originating document")
    res_id = fields.Integer(string='Origin ID', readonly=True, help="ID of the originating document")
    origin_reference = fields.Integer(string='Origin Reference', readonly=True, help="Used to link back to the originating document")
    origin_record_name = fields.Char(string="Origin Document", compute="_compute_origin_record_name", store=True)
    currency_id = fields.Many2one("res.currency")
    folder_tag_ids = fields.Many2many(
        "approval.folder.tag", compute="_compute_folder_tag_ids", string="Folder Tags", store=True
    )

    @api.depends("category_id.folder_tag_ids")
    def _compute_folder_tag_ids(self):
        for request in self:
            request.folder_tag_ids = request.category_id.folder_tag_ids

    @api.depends('res_model', 'res_id')
    def _compute_origin_record_name(self):
        """Compute a readable name for the origin document"""
        for request in self:
            if request.res_model and request.res_id:
                try:
                    record = self.env[request.res_model].browse(request.res_id).exists()
                    if record:
                        request.origin_record_name = record.display_name
                    else:
                        request.origin_record_name = f"{request.res_model}#{request.res_id} (deleted)"
                except Exception:
                    request.origin_record_name = f"{request.res_model}#{request.res_id}"
            else:
                request.origin_record_name = False

    def action_cancel(self):
        not_cancelled = self.filtered(lambda r: r.request_status != 'cancel' and r.approval_type == 'vendor_approval')
        super().action_cancel()
        self.flush_model(['request_status'])
        cancelled = self.filtered(lambda r: r.request_status == 'cancel')
        if vendors := (not_cancelled & cancelled).vendor_id:
            vendors.vendor_state = 'draft'
        # This section is for the approvals on PO, SO, Invoices, Bills
        for request in self.filtered(lambda r: r.res_model and r.res_id and r.request_status == 'cancel'):
            record = self.env[request.res_model].browse(request.res_id).exists()
            if record and hasattr(record, '_on_approval_cancel'):
                record._on_approval_cancel()

    def action_approve(self, approver=None):
        not_approved = self.filtered(lambda r: r.request_status != 'approved' and r.approval_type == 'vendor_approval')
        super().action_approve(approver)
        self.flush_model(['request_status'])
        approved = self.filtered(lambda r: r.request_status == 'approved')
        if vendors := (not_approved & approved).vendor_id:
            vendors.vendor_state = 'approved'
        # This section is for the approvals on PO, SO, Invoices, Bills
        for request in self.filtered(lambda r: r.res_model and r.res_id and r.request_status == 'approved'):
            record = self.env[request.res_model].browse(request.res_id).exists()
            if record and hasattr(record, '_on_approval_approved'):
                record._on_approval_approved()

    def action_refuse(self, approver=None):
        not_refused = self.filtered(lambda r: r.request_status != 'refused' and r.approval_type == 'vendor_approval')
        super().action_refuse(approver)
        self.flush_model(['request_status'])
        refused = self.filtered(lambda r: r.request_status == 'refused')
        if vendors := (not_refused & refused).vendor_id:
            vendors.vendor_state = 'rejected'
        for request in self.filtered(lambda r: r.res_model and r.res_id and r.request_status == 'refused'):
            record = self.env[request.res_model].browse(request.res_id).exists()
            if record and hasattr(record, '_on_approval_refused'):
                record._on_approval_refused()

    def action_view_origin_document(self):
        """Action to open the origin document"""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            return False
        return self.env[self.res_model].browse(self.res_id).exists()._get_records_action()

    def _compute_approver_ids(self):
        """ Override to handle dynamic user field in the category based on the model """
        for request in self:
            users_to_category_approver = {}
            for approver in request.category_id.approver_ids:
                users_to_category_approver[approver.user_id.id] = approver

            approver_id_vals = [Command.clear()]

            if request.category_id.manager_approval:
                employee = self.env['hr.employee'].search([('user_id', '=', request.request_owner_id.id)], limit=1)
                if employee.parent_id.user_id:
                    manager_user_id = employee.parent_id.user_id.id
                    manager_required = request.category_id.manager_approval == 'required'
                    # We set the manager sequence to be lower than all others (9) so they are the first to approve.
                    approver_id_vals.append(Command.create({
                        'user_id': manager_user_id,
                        'status': 'new',
                        'required': manager_required,
                        'sequence': 9,
                    }))
                    if manager_user_id in users_to_category_approver:
                        users_to_category_approver.pop(manager_user_id)

            for user_id in users_to_category_approver:
                # BEGIN OVERRIDE
                actual_user_id = user_id
                if request.category_id.model_id and request.res_model == request.category_id.model_id.model:
                    approver = users_to_category_approver[user_id]
                    approver_apply_on_domain = approver.apply_on_domain
                    approver_user = approver.user_field
                    record = None

                    if request.res_model and request.res_id and (approver_apply_on_domain or approver_user):
                        record = self.env[request.res_model].browse(request.res_id).exists()

                    if approver_apply_on_domain and record and \
                        not record.filtered_domain(safe_eval(approver_apply_on_domain, {'uid': self.env.uid})):
                        continue

                    if record and approver_user:
                        dynamic_approvers = record.mapped(approver_user)
                        user_id = dynamic_approvers.id if len(dynamic_approvers) == 1 else user_id

                approver_id_vals.append(Command.create({
                    'user_id': user_id,
                    'status': 'new',
                    'required': users_to_category_approver[actual_user_id].required,
                    'sequence': users_to_category_approver[actual_user_id].sequence,
                }))
                # END OVERRIDE
            request.update({'approver_ids': approver_id_vals})
