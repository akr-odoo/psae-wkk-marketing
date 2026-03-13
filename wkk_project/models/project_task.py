from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    invisible_project_stage_ids = fields.Many2many(
        "project.project.stage", help="Project stages in which the task is not visible"
    )
    project_stage_id = fields.Many2one(related="project_id.stage_id", string="Project State", store=True)
    active = fields.Boolean(compute='_compute_active', store=True, copy=True, readonly=False)

    @api.depends('project_id', 'project_stage_id', 'invisible_project_stage_ids')
    def _compute_active(self):
        for task in self:
            task.active = not (task.project_stage_id and task.invisible_project_stage_ids and task.project_stage_id in task.invisible_project_stage_ids)
