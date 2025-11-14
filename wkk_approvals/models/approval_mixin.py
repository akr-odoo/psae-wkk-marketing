from odoo import _, api, fields, models

PRIORITY_ORDER = {
    'pending': 0,
    'approved': 1,
    'refused': 2,
    'new': 3,
    'cancel': 4,
}

ACTION_MAP = {
    'approve': 'action_approve',
    'reject': 'action_refuse',
    'cancel': 'action_cancel'
}


class ApprovalMixin(models.AbstractModel):
    """
    Universal Approval Mixin

    Inherit this mixin to enable approval workflows for any model.
    This mixin creates and manages approval requests linked to the records
    of the inheriting model.

    To use this mixin:
    1. Add it to your model's _inherit attribute
    2. Configure the approval category for your model in the settings
    3. Implement the method _get_approval_request_vals() to customize approval request creation

    The mixin handles approval status tracking and provides methods to create, view,
    and manage approval requests.
    """
    _name = 'approval.mixin'
    _description = "Approval Mixin"

    approval_request_ids = fields.One2many('approval.request', 'origin_reference', domain=lambda self: [('res_model', '=', self._name)])
    approval_request_id = fields.Many2one('approval.request', compute='_compute_current_approval_request', store=True)
    approval_status = fields.Selection(related='approval_request_id.request_status')
    requires_approval = fields.Boolean(compute='_compute_requires_approval')
    can_current_user_approve = fields.Boolean(compute='_compute_can_current_user_approve')

    ###################################################
    # Compute Methods ---------------------------------
    ###################################################

    @api.depends('approval_request_ids.request_status')
    def _compute_current_approval_request(self):
        """Compute the current active approval request"""
        for record in self:
            if record.approval_request_ids:
                record.approval_request_id = sorted(
                    record.approval_request_ids,
                    key=lambda r: PRIORITY_ORDER.get(r.request_status, 5)
                )[0]
            else:
                record.approval_request_id = False

    @api.depends('approval_status')
    def _compute_requires_approval(self):
        """Determine if a record requires approval based on settings and current status"""
        settings = self._get_approval_settings()
        for record in self:
            record.requires_approval = (settings.get('enabled') and settings.get('category_id')) or \
                                    (record.approval_status and record.approval_status != 'approved')

    @api.depends('approval_request_id', 'approval_request_id.approver_ids', 'approval_status')
    def _compute_can_current_user_approve(self):
        """Determine if the current user can approve this record"""
        user = self.env.user
        for record in self:
            can_approve = False
            if record.approval_request_id and record.approval_status == 'pending':
                is_approver = user in record.approval_request_id.approver_ids.filtered(lambda a: a.status == 'pending').mapped('user_id')
                if is_approver:
                    if record.approval_request_id.approval_type != 'sequential':
                        can_approve = True
                    else:
                        pending_approvers = record.approval_request_id.approver_ids.filtered(lambda a: not a.status)
                        can_approve = pending_approvers and pending_approvers[0].user_id == user
            record.can_current_user_approve = can_approve

    ###################################################
    # Get Methods -------------------------------------
    ###################################################

    def _get_approval_settings(self):
        company = self.env.company

        if setting := self.env['model.approval.settings'].search([('company_id', '=', company.id), ('model_name', '=', self._name)], limit=1):
            return {
                'enabled': setting.approval_enabled,
                'category_id': setting.approval_category_id.id if setting.approval_category_id else False,
            }
        return {
            'enabled': False,
            'category_id': False,
        }

    def get_approval_request_vals(self):
        """This method should be overridden in inheriting models to provide model-specific values for the approval request."""
        self.ensure_one()
        approval_settings = self._get_approval_settings()
        return {
            'name': self.display_name,
            'date': fields.Date.today(),
            'origin_reference': self.id,
            'res_model': self._name,
            'res_id': self.id,
            'category_id': approval_settings.get('category_id'),
            'request_owner_id': self.env.user.id,
        }

    ###################################################
    # Hook Methods ------------------------------------
    ###################################################

    def _on_approval_approved(self):
        """This method should be overridden in inheriting models to implement model-specific behavior when an approval is approved."""
        self.message_post(body=_('Approval has been granted.'), author_id=self.env.ref('base.partner_root').id)
        return True

    def _on_approval_refused(self):
        """This method should be overridden in inheriting models to implement model-specific behavior when an approval is refused."""
        self.message_post(body=_('Approval has been refused.'), author_id=self.env.ref('base.partner_root').id)
        return True

    def _on_approval_cancel(self):
        """This method should be overridden in inheriting models to implement model-specific behavior when an approval is canceled."""
        self.message_post(body=_('Approval has been canceled.'), author_id=self.env.ref('base.partner_root').id)
        return True

    ###################################################
    # Action Methods ----------------------------------
    ###################################################

    def action_create_approvals(self):
        """Create approval requests for the selected records"""
        approval_request_vals = []
        for record in self.filtered(lambda r: r.approval_status != 'pending'):
            vals = record.get_approval_request_vals()
            if vals:
                approval_request_vals.append(vals)

        if not approval_request_vals:
            return False

        approval_request_ids = self.env['approval.request'].create(approval_request_vals)
        for approval_request_id in approval_request_ids:
            if approval_request_id.approver_ids:
                approval_request_id.action_confirm()
            else:
                approval_request_id.request_status = 'approved'

        for record in self:
            if approval_request := approval_request_ids.filtered(lambda r: r.res_id == record.id):
                record.approval_request_id = approval_request[0]
                record.message_post(body=_('Approval request has been created.'))

        self.invalidate_recordset(['approval_request_id', 'approval_status'])

    def action_view_approval_request(self):
        """Open the approval request(s) linked to this record"""
        self.ensure_one()
        return self.approval_request_ids._get_records_action()

    def _process_approval_action(self, action_type):
        """Common method for approval actions (approve/reject/cancel)"""
        for record in self:
            if not record.approval_request_id:
                continue

            if action_type in ('approve', 'reject'):
                if not (record.can_current_user_approve and
                (approver := record.approval_request_id.approver_ids.filtered(lambda a: a.user_id == self.env.user))):
                    continue

                status = 'approved' if action_type == 'approve' else 'refused'
                approver.write({'status': status})
                getattr(record.approval_request_id, ACTION_MAP[action_type])()

            elif action_type == 'cancel':
                record.approval_request_id.action_cancel()

        return True if self else False

    def action_approve(self):
        """Directly approve the current approval request linked to this record"""
        return self._process_approval_action('approve')

    def action_reject(self):
        """Directly reject the current approval request linked to this record"""
        return self._process_approval_action('reject')

    def action_cancel_approval(self):
        """Cancel record and related approval request"""
        return self._process_approval_action('cancel')
