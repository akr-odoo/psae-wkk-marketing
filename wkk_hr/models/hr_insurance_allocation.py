from odoo import api, fields, models


class HrInsuranceAllocation(models.Model):
    _name = 'hr.insurance.allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Insurance Allocation'
    _order = 'expiry_date ASC'

    name = fields.Char(name='Insurance Card Number', required=True, index='trigram')
    employee_id = fields.Many2one('hr.employee', ondelete='restrict', required=True)
    employee_dependent_ids = fields.Many2many('hr.dependent.dependent', compute='_compute_employee_dependent_ids', precompute=True, store=True)
    dependent_id = fields.Many2one('hr.dependent.dependent', ondelete='restrict')
    provider_id = fields.Many2one('hr.insurance.provider', ondelete='restrict', required=True)
    category_id = fields.Many2one('hr.insurance.category', ondelete='restrict', required=True)
    expiry_date = fields.Date(required=True)

    @api.depends('employee_id')
    def _compute_employee_dependent_ids(self):
        for allocation in self:
            allocation.employee_dependent_ids = allocation.employee_id.dependent_ids

