from odoo import _, Command, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_list


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'approval.mixin']

    @api.constrains(
        'partner_id', 'partner_ref', 'currency_id', 'date_order',
        'date_planned', 'project_id', 'order_line', 'user_id',
        'origin', 'payment_term_id', 'fiscal_position_id',
    )
    def _check_approval_status(self):
        if self.filtered(lambda po: po.approval_status == 'approved'):
            raise ValidationError(_(
                "Approval already granted. Please cancel the approval status and request a new approval. %(names)s",
                names=format_list(self.env, self.mapped('name'))
            ))

    def init(self):
        super().init()
        """Setup method to initialize the purchase order model into the model_approval_settings on each company if it doesnt exist"""
        companies = self.env['res.company'].sudo().search([]).filtered(
            lambda company: not company.model_approval_settings_ids.filtered(
                lambda setting: setting.model_name == 'purchase.order'
            )
        )
        vals_list = [{
            'company_id': company.id,
            'model_name': 'purchase.order',
            'approval_enabled': True,
        } for company in companies]
        if vals_list:
            self.env['model.approval.settings'].create(vals_list)

    def get_approval_request_vals(self):
        """Override to add purchase-specific values to the approval request"""
        vals = super().get_approval_request_vals()
        return {
            **vals,
            'amount': self.amount_total,
            'reference': self.name,
            'date_start': fields.Date.today(),
            'date_end': self.date_planned or fields.Date.today(),
            'currency_id': self.currency_id.id,
            'product_line_ids': [Command.create({
                'product_id': line.product_id.id,
                'description': line.name,
                'quantity': line.product_qty,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_total,
            }) for line in self.order_line],
        }

    def button_cancel(self):
        action = super().button_cancel()
        self.action_cancel_approval()
        return action
