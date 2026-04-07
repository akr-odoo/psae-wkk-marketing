from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    project_reference = fields.Char(copy=False)
    referred_by = fields.Selection(
        [("employee", "Employee"), ("management", "Management"), ("third_party", "Third Party"), ("others", "Others")],
        copy=False,
    )
    referred_name = fields.Char(copy=False)
    referred_employee = fields.Many2one("hr.employee.public", copy=False)
    priority = fields.Selection(
        [("critical", "Critical"), ("high", "High"), ("medium", "Medium"), ("low", "Low")], copy=False
    )
    rfp_file_name = fields.Char(readonly=True)
    rfp_upload_file = fields.Binary(string="RFP Upload File")
    project_type_id = fields.Many2one("project.project")
    note_sale = fields.Html(string="T&C on Sale Order", copy=False)
    note_purchase = fields.Html(string="T&C on Purchase Order", copy=False)

    templated_project_ids = fields.One2many('project.project', 'project_type_id', 'Templated Projects')
    connected_sale_ids = fields.One2many('sale.order', 'project_id', 'Connected Sale Orders')
    connected_purchase_ids = fields.One2many('purchase.order', 'project_id', 'Connected Purchase Orders')

    @api.model_create_multi
    def create(self, vals_list):
        projects = self.env["project.project"]
        indices_processed = set()
        copy_from_template = self.env.context.get("copy_from_template")
        for (
            idx,
            vals,
        ) in enumerate(vals_list):
            if not vals.get("project_reference"):
                vals["project_reference"] = self.env["ir.sequence"].next_by_code("project.project")
            if not copy_from_template and (project_type_id := self.browse(vals.get("project_type_id")).exists()):
                projects += (
                    self.env["project.template.create.wizard"]
                    .create({
                        "template_id": project_type_id.id,
                        **{
                            fname: fvalue
                            for fname, fvalue in vals.items()
                            if fname in self.env["project.template.create.wizard"]._fields
                        },
                    })
                    ._create_project_from_template()
                )
                indices_processed.add(idx)
        return projects + super().create([vals for idx, vals in enumerate(vals_list) if idx not in indices_processed])

    def write(self, vals):
        res = super().write(vals)
        if 'note_sale' in vals:
            self.templated_project_ids.connected_sale_ids.filtered(lambda sale: sale.state == 'draft').note = self.note_sale
        if 'note_purchase' in vals:
            self.templated_project_ids.connected_purchase_ids.filtered(lambda purchase: purchase.state == 'draft').note = self.note_purchase
        return res

    def action_create_from_template(self, values=None, role_to_users_mapping=None):
        self.ensure_one()
        values = values or {}
        values.update({
            "project_type_id": self.id,
            "note_sale": self.note_sale,
            "note_purchase": self.note_purchase,
        })
        project = super().action_create_from_template(values, role_to_users_mapping)
        project.task_ids._compute_active()
        return project
