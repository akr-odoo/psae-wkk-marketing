from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    document_type_id = fields.Many2one('documents.type')
    expiry_date = fields.Date()
