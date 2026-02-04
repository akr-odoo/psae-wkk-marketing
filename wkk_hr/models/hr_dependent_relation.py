from odoo import fields, models


class HrDependentRelation(models.Model):
    _name = 'hr.dependent.relation'
    _description = 'Dependent Relation'
    _order = 'sequence, id'

    name = fields.Char(name='Relation', required=True, index='trigram')
    sequence = fields.Integer(default=10)
