from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vendor_require_approval = fields.Boolean(related='company_id.vendor_require_approval', readonly=False)
    vendor_approval_category_id = fields.Many2one(related='company_id.vendor_approval_category_id', readonly=False)
    document_expiry_notify_user_ids = fields.Many2many(related='company_id.document_expiry_notify_user_ids', readonly=False)
    vendor_modification_notify_user_ids = fields.Many2many(related='company_id.vendor_modification_notify_user_ids', readonly=False)
    document_expiry_notify_users_days = fields.Integer(related='company_id.document_expiry_notify_users_days', readonly=False)
    model_approval_settings_ids = fields.One2many(related='company_id.model_approval_settings_ids', readonly=False)
