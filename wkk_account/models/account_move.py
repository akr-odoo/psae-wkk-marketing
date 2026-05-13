from odoo import _, Command, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_list


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'approval.mixin']

    @api.constrains(
        'name', 'move_type', 'purchase_vendor_bill_id', 'invoice_date', 'date',
        'invoice_payment_term_id', 'currency_id', 'invoice_date_due', 'source_id',
        'invoice_line_ids', 'line_ids', 'partner_id', 'invoice_incoterm_id',
        'incoterm_location', 'fiscal_position_id', 'preferred_payment_method_line_id',
        'auto_post', 'ref', 'invoice_user_id', 'team_id', 'partner_bank_id',
        'payment_reference', 'delivery_date', 'campaign_id', 'medium_id',
    )
    def _check_approval_status(self):
        if self.filtered(lambda am: am.move_type in ['out_invoice', 'in_invoice'] and am.approval_status == 'approved') and not self.env.context.get("pass_approval_constraint"):
            raise ValidationError(_(
                    "Approval already granted. Please cancel the approval status and request a new approval. %(names)s",
                    names=format_list(self.env, self.mapped('name'))
                )
            )

    def init(self):
        super().init()
        """Setup method to initialize the account move model into the model_approval_settings on each company if it doesnt exist"""
        companies = self.env['res.company'].sudo().search([]).filtered(
            lambda company: not company.model_approval_settings_ids.filtered(
                lambda setting: setting.model_name == 'account.move'
            )
        )
        vals_list = [{
            'company_id': company.id,
            'model_name': 'account.move',
            'approval_enabled': True,
        } for company in companies]
        if vals_list:
            self.env['model.approval.settings'].create(vals_list)

    @api.depends('move_type')
    def _compute_requires_approval(self):
        """Override to add move type-specific logic for determining if approval is required"""
        super()._compute_requires_approval()
        for record in self:
            record.requires_approval = record.move_type in ['out_invoice', 'in_invoice']

    def get_approval_request_vals(self):
        """Override to add purchase-specific values to the approval request"""
        vals = super().get_approval_request_vals()
        return {
            **vals,
            'amount': self.amount_total,
            'reference': self.name,
            'date_start': fields.Date.today(),
            'date_end': self.invoice_date_due or fields.Date.today(),
            'currency_id': self.currency_id.id,
            'product_line_ids': [Command.create({
                'product_id': line.product_id.id,
                'description': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_total,
            }) for line in self.invoice_line_ids],
        }

    def action_post(self):
        if self.filtered(lambda am: am.move_type in ['out_invoice', 'in_invoice'] and am.approval_status == 'approved'):
            return super(AccountMove, self.with_context(pass_approval_constraint=True)).action_post()
        return super().action_post()

    def button_draft(self):
        if self.filtered(lambda am: am.move_type in ['out_invoice', 'in_invoice'] and am.approval_status == 'approved'):
            return super(AccountMove, self.with_context(pass_approval_constraint=True)).button_draft()
        return super().button_draft()

    def button_cancel(self):
        action = super().button_cancel()
        self.action_cancel_approval()
        return action

    def action_print_delivery_note(self):
        self.ensure_one()
        return self.env.ref('wkk_account.action_report_delivery_note_invoice').report_action(self)
