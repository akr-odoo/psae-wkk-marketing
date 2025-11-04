from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import format_list


class HrVersion(models.Model):
    _inherit = "hr.version"

    @api.constrains("wage")
    def _constrains_wage(self):
        if records := self.filtered(
            lambda version: version.job_id.minimum_salary
            and version.job_id.maximum_salary
            and version.wage
            and not (version.job_id.minimum_salary
            <= version.wage
            <= version.job_id.maximum_salary)
        ):
            raise ValidationError(
                _(
                    "Employee wage exceeds minimum and maximum of the job. Found %(employees)s",
                    employees=format_list(
                        self.env,
                        records.mapped(
                            lambda ver: f"{ver.employee_id.name} ({ver.job_id.minimum_salary}, {ver.job_id.maximum_salary})"
                        ),
                    ),
                )
            )
