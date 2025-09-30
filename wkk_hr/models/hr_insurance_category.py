from odoo import fields, models


class HrInsuranceCategory(models.Model):
    _name = 'hr.insurance.category'
    _description = 'Insurance Category'
    _order = 'sequence, id'

    name = fields.Char(name='category', required=True, index='trigram')
    sequence = fields.Integer(default=10)

