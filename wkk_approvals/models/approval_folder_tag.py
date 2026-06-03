from odoo import fields, models


class ApprovalFolderTag(models.Model):
    _name = "approval.folder.tag"
    _description = "Approval Folder Tag"

    name = fields.Char(required=True, copy=False)
