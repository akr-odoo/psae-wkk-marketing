from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ModelApprovalSettings(models.Model):
    _name = 'model.approval.settings'
    _description = 'Model Approval Settings'
    _rec_name = 'model_name'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    model_id = fields.Many2one('ir.model', string='Model', ondelete='cascade')  # TODO: domain only for categories that are same model or not set at all
    model_name = fields.Char(store=True, compute='_compute_model_name', inverse='_inverse_model_name')
    model_description = fields.Char(related="model_id.name")
    approval_enabled = fields.Boolean(string='Enable Approval')
    approval_category_id = fields.Many2one('approval.category', string='Approval Category')

    _unique_model_per_company = models.Constraint(
        'UNIQUE(company_id, model_name)',
        'Only one approval setting per model per company is allowed'
    )

    @api.depends('model_id.model')
    def _compute_model_name(self):
        for record in self.filtered('model_id'):
            record.model_name = record.model_id.model

    def _inverse_model_name(self):
        for record in self:
            if record.model_name:
                model = self.env['ir.model'].search([('model', '=', record.model_name)], limit=1)
                if model:
                    record.model_id = model.id
                else:
                    raise ValidationError(_("Model '%s' not found.") % record.model_name)
            else:
                record.model_id = False
