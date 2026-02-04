from odoo import _, api, fields, models


class AccountBatchPayment(models.Model):
    _name = 'account.batch.payment'
    _inherit = ['account.batch.payment', 'cheque.notification.mixin']

    cheque_number = fields.Char(copy=False)
    cheque_due_date = fields.Date(copy=False)
    cheque_amount = fields.Float(copy=False)
    cheque_bank_id = fields.Many2one('res.bank', copy=False)
    cheque_memo = fields.Char(copy=False)

    @api.model
    def _get_cheque_notification_domain(self):
        return super()._get_cheque_notification_domain() & fields.Domain('state', 'in', ['sent', 'reconciled'])

    @api.model
    def _cron_notify_cheque_due_date(self, batch_size=500):
        domain = self._get_cheque_notification_domain()
        batch_payments = self.search(domain, limit=batch_size)
        remaining = len(batch_payments) if len(batch_payments) < batch_size else self.search_count(domain)
        self.env['ir.cron']._commit_progress(remaining=remaining)
        note = _('Reminder for cheque due date.')
        summary = _('Cheque Collection Nearing')
        vals_list = [
            {
                'res_model_id': self.env['ir.model']._get_id('account.batch.payment'),
                'res_id': batch_payment.id,
                'user_id': user.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'note': note,
                'summary': summary,
                'automated': True,
            } for batch_payment in batch_payments for user in batch_payment.notification_user_ids
        ]
        self.env['mail.activity'].create(vals_list)
        batch_payments.users_notified = True
        batch_payments.payment_ids.users_notified = True
        self.env['ir.cron']._commit_progress(len(batch_payments))
