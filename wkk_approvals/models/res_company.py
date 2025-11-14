from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    vendor_require_approval = fields.Boolean(help='Enables vendor approvals flow')
    vendor_approval_category_id = fields.Many2one('approval.category', help='Approval category to be used for the vendor approval flow')
    document_expiry_notify_user_ids = fields.Many2many('res.users', 'document_expiry_notify_users_company_rel', 'company_id', 'user_id', help='Users to notify for vendor document expiry')
    vendor_modification_notify_user_ids = fields.Many2many('res.users', 'vendor_modification_notify_users_company_rel', 'company_id', 'user_id', help='Users to notify for vendor modifications')
    document_expiry_notify_users_days = fields.Integer(help='Days to notify before vendor document expiry')
    model_approval_settings_ids = fields.One2many('model.approval.settings', 'company_id')
