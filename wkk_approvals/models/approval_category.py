from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[
        ('vendor_approval', 'Vendor Approval'),
        ('redirect_approval', 'Redirect Approval'),
    ])
    model_id = fields.Many2one("ir.model", string="Model", help="Model for which this approval category is applicable")
    folder_id = fields.Many2one("approval.folder", string="Approval Folder", ondelete="set null")
    redirect_action_id = fields.Many2one("ir.actions.act_window")
    allowed_user_ids = fields.Many2many('res.users', 'approval_category_allowed_users_rel', 'category_id', 'user_id')
    folder_tag_ids = fields.Many2many("approval.folder.tag", string="Tags")

    def create_request(self):
        self.ensure_one()
        if self.approval_type == 'redirect_approval':
            if not self.redirect_action_id:
                raise ValidationError(_("No action specified to redirect to"))
            return {**self.redirect_action_id._get_action_dict(), "views": [(False, "form")], "view_mode": "form"}
        return super().create_request()

    def _constrains_approval_minimum(self):
        """Override to ensure minimum is not less than required approvers only if domain is not set"""
        for record in self:
            if record.approval_minimum < len(record.approver_ids.filtered(lambda a: a.required and (not a.apply_on_domain or a.apply_on_domain == '[]'))):
                raise ValidationError(_('Minimum Approval must be equal or superior to the sum of required Approvers for: %s') % record.name)

    @api.onchange('approval_type')
    def _onchange_type_assign_has_date(self):
        for category in self:
            category.has_date = 'required' if category.approval_type == 'vendor_approval' else category.has_date

    @api.onchange('approval_type')
    def _onchange_type_assign_has_partner(self):
        for category in self:
            category.has_partner = 'required' if category.approval_type == 'vendor_approval' else category.has_partner
