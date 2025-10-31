from odoo import fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    is_document_expiry_notification = fields.Boolean()
    is_vendor_modified_notification = fields.Boolean()
