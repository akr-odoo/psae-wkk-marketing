from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrDependentRelation(models.Model):
    _name = 'hr.dependent.dependent'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dependent'

    age = fields.Float(compute='_compute_age', search='_search_age')
    name = fields.Char(required=True, index='trigram', tracking=True)
    birthday = fields.Date(tracking=True)
    employee_id = fields.Many2one('hr.employee', ondelete='restrict', required=True, tracking=True)
    relation_id = fields.Many2one('hr.dependent.relation', ondelete='restrict', required=True, tracking=True)
    insurance_allocation_ids = fields.One2many('hr.insurance.allocation', 'dependent_id', tracking=True)

    @api.depends('birthday')
    def _compute_age(self):
        today = fields.Date.today()
        for birthdate, dependents in self.grouped('birthday').items():
            dependents.age = birthdate and today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))  # Removes either 1 or 0 off of the years difference depending on whether the birth month & date have passed or not

    def _search_age(self, operator, value):
        today = fields.Date.today()
        cutoff_date = today - relativedelta(years=value)
        domain = []
        if operator == '>':
            domain = [('birthday', '<', fields.Date.to_string(cutoff_date))]
        elif operator == '>=':
            domain = [('birthday', '<=', fields.Date.to_string(cutoff_date))]
        elif operator == '<':
            domain = [('birthday', '>', fields.Date.to_string(cutoff_date))]
        elif operator == '<=':
            domain = [('birthday', '>=', fields.Date.to_string(cutoff_date))]
        elif operator in ['=', '!=']:
            if operator == '=':
                date_end_of_year = today - relativedelta(years=value)
                date_start_of_year = today - relativedelta(years=value + 1)
                domain = [
                    ('birthday', '>', fields.Date.to_string(date_start_of_year)),
                    ('birthday', '<=', fields.Date.to_string(date_end_of_year))
                ]
            else:
                date_end_of_year = today - relativedelta(years=value)
                date_start_of_year = today - relativedelta(years=value + 1)

                domain = [
                    '|',
                    ('birthday', '<=', fields.Date.to_string(date_start_of_year)),
                    ('birthday', '>', fields.Date.to_string(date_end_of_year))
                ]
        else:
            return NotImplemented
        return domain
