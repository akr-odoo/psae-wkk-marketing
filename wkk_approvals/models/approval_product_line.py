from odoo import api, fields, models


class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    currency_id = fields.Many2one(related='approval_request_id.currency_id')
    price_unit = fields.Monetary()
    price_total = fields.Monetary()
    price_subtotal = fields.Monetary()
    has_product_price = fields.Boolean(compute='_compute_has_product_price', store=True)

    @api.depends('price_unit', 'price_total', 'price_subtotal')
    def _compute_has_product_price(self):
        for line in self:
            line.has_product_price = bool(line.price_unit or line.price_total or line.price_subtotal)
