from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    company_currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    total_in_company_currency = fields.Monetary(
        compute="_compute_total_in_company_currency",
        currency_field="company_currency_id",
        store=True,
    )

    @api.depends("company_currency_id", "currency_id", "amount_total")
    def _compute_total_in_company_currency(self):
        for order in self:
            order.total_in_company_currency = order.currency_id._convert(
                order.amount_total, order.company_currency_id, order.company_id, order.date_order or fields.Date.today()
            )
