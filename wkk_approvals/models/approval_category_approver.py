from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'

    model_id = fields.Many2one(related='category_id.model_id')
    model_name = fields.Char(related='model_id.model')
    apply_on_domain = fields.Char(help="Leave empty to apply on all records of the model.", compute="_compute_apply_on_domain", store=True, readonly=False)
    user_field = fields.Char(string='Field', help="User field from the record to assign as approver. If empty, uses the manually selected user here.", compute="_compute_user_field", store=True, readonly=False)

    @api.depends('model_id')
    def _compute_apply_on_domain(self):
        self.filtered(lambda r: not r.model_id).update({'apply_on_domain': False})

    @api.depends('model_id')
    def _compute_user_field(self):
        self.filtered(lambda r: not r.model_id).update({'user_field': False})

    @api.constrains('model_id', 'user_field')
    def _constrain_user_field(self):
        for record in self.filtered(lambda r: r.model_id and r.user_field):
            field_id = self._verify_field_path(record.model_name, record.user_field)
            if field_id:
                if field_id.type != 'many2one' or field_id.comodel_name != 'res.users':
                    raise UserError(
                        _("The field '%(field)s' is not a valid user field on model %(model)s",
                        field=record.user_field,
                        model=record.model_name)
                    )
            else:
                raise ValidationError(
                    _("'%(field)s' does not seem to be a valid field path on %(model)s",
                    field=record.user_field,
                    model=record.model_name)
                )

    def _verify_field_path(self, model_name, field_path):
        """ Verify if the given field path is valid for the model. Similar to _find_value_from_field_path but returns field object """
        model = self.sudo().env[model_name]
        field_path_models = field_path.rsplit('.', 1)
        if len(field_path_models) > 1:
            last_model_path, last_fname = field_path_models
            last_model = model.mapped(last_model_path)
        else:
            last_model, last_fname = model, field_path
        last_field = last_model._fields[last_fname]
        return last_field if last_field else None
