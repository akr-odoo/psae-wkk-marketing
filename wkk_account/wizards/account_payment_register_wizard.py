from odoo import fields, models


class AccountPaymentRegisterWizard(models.TransientModel):
    _inherit = 'account.payment.register'

    cheque_number = fields.Char(copy=False)
    cheque_due_date = fields.Date(copy=False)
    cheque_amount = fields.Float(copy=False)
    cheque_bank_id = fields.Many2one('res.bank', copy=False)
    cheque_memo = fields.Char(copy=False)
    notification_user_ids = fields.Many2many('res.users', copy=False)
    notify_days_before = fields.Float(copy=False)
    receive_cheque = fields.Boolean(related='payment_method_line_id.receive_cheque', store=True)

    def _update_cheque_vals(self):
        self.ensure_one()
        return {
            'cheque_number': self.cheque_number,
            'cheque_due_date': self.cheque_due_date,
            'cheque_amount': self.cheque_amount,
            'cheque_bank_id': self.cheque_bank_id,
            'cheque_memo': self.cheque_memo,
            'notification_user_ids': self.notification_user_ids,
            'notify_days_before': self.notify_days_before,
        }

    def _create_payment_vals_from_wizard(self, batch_result):
        return {
            **super()._create_payment_vals_from_wizard(batch_result),
            **self._update_cheque_vals(),
        }

    def _create_payment_vals_from_batch(self, batch_result):
        return {
            **super()._create_payment_vals_from_wizard(batch_result),
            **self._update_cheque_vals(),
        }
