from odoo import fields, models


class HrInsuranceProvider(models.Model):
    _name = 'hr.insurance.provider'
    _description = 'Insurance Provider'
    _order = 'sequence, id'

    name = fields.Char(name='Provider', required=True, index='trigram')
    sequence = fields.Integer(default=10)

