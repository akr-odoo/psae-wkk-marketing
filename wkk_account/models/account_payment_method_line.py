from odoo import fields, models


class AccountPaymentMethodLine(models.Model):
    _inherit = 'account.payment.method.line'

    receive_cheque = fields.Boolean()
