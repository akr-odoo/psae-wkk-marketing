from odoo import fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    minimum_salary = fields.Float()
    maximum_salary = fields.Float()

    _check_salary_range = models.Constraint(
        "check(maximum_salary >= minimum_salary)",
        "Maximum salary must be greater than or equal to minimum salary.",
    )

    _check_positive_max_salary = models.Constraint(
        "CHECK(maximum_salary >= 0)",
        "Maximum salary must be greater than or equal to Zero.",
    )

    _check_positive_min_salary = models.Constraint(
        "CHECK(minimum_salary >= 0)",
        "Minimum salary must be greater than or equal to Zero.",
    )
