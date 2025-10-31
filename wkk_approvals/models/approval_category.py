from odoo import api, fields, models


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[
        ('vendor_approval', 'Vendor Approval'),
    ])

    @api.onchange('approval_type')
    def _onchange_type_assign_has_date(self):
        for category in self:
            category.has_date = 'required' if category.approval_type == 'vendor_approval' else category.has_date

    @api.onchange('approval_type')
    def _onchange_type_assign_has_partner(self):
        for category in self:
            category.has_partner = 'required' if category.approval_type == 'vendor_approval' else category.has_partner
