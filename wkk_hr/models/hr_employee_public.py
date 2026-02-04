from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    insurance_allocation_ids = fields.One2many('hr.insurance.allocation', 'employee_id', readonly=True)
    dependent_ids = fields.One2many('hr.dependent.dependent', 'employee_id', readonly=True)
