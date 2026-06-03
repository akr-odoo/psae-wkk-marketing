from random import randint

from odoo import fields, models


class ApprovalFolderTag(models.Model):
    _name = "approval.folder.tag"
    _description = "Approval Folder Tag"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(required=True, copy=False)
    color = fields.Integer(default=_get_default_color)
