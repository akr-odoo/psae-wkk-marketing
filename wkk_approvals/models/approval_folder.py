from odoo import api, fields, models


class ApprovalFolder(models.Model):
    _name = 'approval.folder'
    _description = 'Approval Folder'

    name = fields.Char(required=True)
    description = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    category_ids = fields.One2many('approval.category', 'folder_id')
    category_count = fields.Integer(compute='_compute_category_count')
    tag_ids = fields.Many2many("approval.folder.tag")

    @api.depends('category_ids')
    def _compute_category_count(self):
        for folder in self:
            folder.category_count = len(folder.category_ids)
