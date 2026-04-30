from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    project_type_id = fields.Many2one(related="project_id.project_type_id", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._update_project_type_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._update_project_type_vals(vals)
        return super().write(vals)

    @api.model
    def _update_project_type_vals(self, vals):
        if "project_id" in vals:
            project = self.env["project.project"].browse(vals.get("project_id")).exists()
            vals.update({"note": project.project_type_id.note_purchase, "partner_ref": project.project_reference})
