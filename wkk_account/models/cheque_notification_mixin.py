from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class ChequeNotificationMixin(models.AbstractModel):
    _name = 'cheque.notification.mixin'

    notification_user_ids = fields.Many2many('res.users', copy=False)
    notify_days_before = fields.Float(copy=False)
    users_notified = fields.Boolean(copy=False)
    cheque_notification_date = fields.Date(compute='_compute_cheque_notification_date', store=True)

    @api.depends('notify_days_before', 'cheque_due_date')
    def _compute_cheque_notification_date(self):
        for payment in self:
            payment.cheque_notification_date = payment.cheque_due_date and payment.cheque_due_date - relativedelta(days=payment.notify_days_before)

    @api.model
    def _get_cheque_notification_domain(self):
        return fields.Domain('notification_user_ids', '!=', False) & fields.Domain('users_notified', '=', False) & fields.Domain('cheque_notification_date', '<=', fields.Date.context_today(self))
