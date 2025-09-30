from odoo import fields, models


class HrInsuranceAllocation(models.Model):
    _name = 'hr.insurance.allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Insurance Allocation'
    _order = 'expiry_date ASC'

    name = fields.Char(name='Insurance Card Number', required=True, index='trigram')
    employee_id = fields.Many2one('hr.employee', ondelete='restrict', required=True)
    dependent_id = fields.Many2one('hr.dependent.dependent', ondelete='restrict')
    provider_id = fields.Many2one('hr.insurance.provider', ondelete='restrict', required=True)
    category_id = fields.Many2one('hr.insurance.category', ondelete='restrict', required=True)
    expiry_date = fields.Date(required=True)

