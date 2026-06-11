from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_print_delivery_note(self):
        self.ensure_one()
        return self.env.ref('wkk_account.action_report_delivery_note_invoice').report_action(self)
