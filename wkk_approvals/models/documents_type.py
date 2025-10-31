from odoo import fields, models


class DocumentsType(models.Model):
    _name = 'documents.type'
    _description = 'Document Type'

    name = fields.Char(required=True, index='trigram')
    sequence = fields.Integer(default=10)
