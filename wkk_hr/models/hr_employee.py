from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    insurance_allocation_ids = fields.One2many('hr.insurance.allocation', 'employee_id', groups='hr.group_hr_user')
    dependent_ids = fields.One2many('hr.dependent.dependent', 'employee_id', groups='hr.group_hr_user')
