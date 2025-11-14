from odoo import _, Command, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_list


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'approval.mixin']

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    total_in_company_currency = fields.Monetary(
        compute='_compute_total_in_company_currency',
        currency_field='company_currency_id',
        store=True,
    )

    @api.constrains('partner_id', 'validity_date', 'date_order', 'order_line')
    def _check_approval_status(self):
        if self.filtered(lambda po: po.approval_status == 'approved') and not self.env.context.get("pass_approval_constraint"):
            raise ValidationError(_(
                "Approval already granted. Please cancel the approval status and request a new approval. %(names)s",
                names=format_list(self.env, self.mapped('name'))
            ))

    @api.depends('company_currency_id', 'currency_id', 'amount_total')
    def _compute_total_in_company_currency(self):
        for order in self:
            order.total_in_company_currency = order.currency_id._convert(
                order.amount_total, order.company_currency_id, order.company_id, order.date_order or fields.Date.today()
            )

    def init(self):
        super().init()
        """Setup method to initialize the sale order model into the model_approval_settings on each company if it doesnt exist"""
        companies = self.env['res.company'].sudo().search([]).filtered(
            lambda company: not company.model_approval_settings_ids.filtered(
                lambda setting: setting.model_name == 'sale.order'
            )
        )
        vals_list = [{
            'company_id': company.id,
            'model_name': 'sale.order',
            'approval_enabled': True,
        } for company in companies]
        if vals_list:
            self.env['model.approval.settings'].create(vals_list)

    def get_approval_request_vals(self):
        """Override to add sale-specific values to the approval request"""
        vals = super().get_approval_request_vals()
        return {
            **vals,
            'amount': self.amount_total,
            'reference': self.name,
            'date_start': fields.Date.today(),
            'date_end': self.commitment_date or fields.Date.today(),
            'currency_id': self.currency_id.id,
            'product_line_ids': [Command.create({
                'product_id': line.product_id.id,
                'description': line.name,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_total,
            }) for line in self.order_line],
        }

    def action_cancel(self):
        action = super().action_cancel()
        self.action_cancel_approval()
        return action

    def action_confirm(self):
        if self.filtered(lambda po: po.approval_status == 'approved'):
            return super(SaleOrder, self.with_context(pass_approval_constraint=True)).action_confirm()
        return super().action_confirm()
