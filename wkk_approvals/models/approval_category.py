from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[
        ('vendor_approval', 'Vendor Approval'),
    ])
    model_id = fields.Many2one('ir.model', string='Model', help="Model for which this approval category is applicable")
    model_name = fields.Char(related='model_id.model')

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
