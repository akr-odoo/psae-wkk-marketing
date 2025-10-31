import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools import SQL, format_list

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection(
        selection=[('customer', 'Customer'), ('vendor', 'Vendor'), ('both', 'Both')], default='customer'
    )
    vendor_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('under_review', 'Under Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('modified', 'Modified'),
            ('expired_documents', 'Expired Documents'),
        ],
        default='draft',
        tracking=True,
        readonly=True,
        copy=False,
    )
    vendor_approval_ids = fields.One2many('approval.request', 'vendor_id')
    vendor_approvals_count = fields.Integer(compute='_compute_vendor_approvals_count', store=True)
    requires_approval = fields.Boolean(compute='_compute_requires_approval')

    def write(self, vals):
        if vals and ('vendor_state' not in vals or len(vals) > 1):
            vals.update({'vendor_state': 'modified'})
        return super().write(vals)

    @api.depends('vendor_approval_ids')
    def _compute_vendor_approvals_count(self):
        for partner in self:
            partner.vendor_approvals_count = len(partner.vendor_approval_ids)

    @api.depends_context('company')
    @api.depends('vendor_state', 'partner_type', 'vendor_approval_ids.request_status', 'company_id.vendor_require_approval')
    def _compute_requires_approval(self):
        for partner in self:
            partner.requires_approval = (
                (partner.company_id and partner.company_id.vendor_require_approval
                or self.env.company.vendor_require_approval)
                and partner.partner_type in ['vendor', 'both']
                and not partner._origin.vendor_approval_ids.filtered(lambda approval: approval.request_status in ['new', 'pending'])
                and partner.vendor_state != 'approved'
            )

    @api.model
    def _get_warning_notification(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'warning',
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'soft_reload',
                },
            },
        }

    def action_reset_vendor_state(self):
        self.ensure_one()
        if self.vendor_state == 'draft':
            raise UserError(_('Cannot reset vendors who are already in the draft state'))
        self.vendor_state = 'draft'

    def action_view_vendor_approvals(self):
        self.ensure_one()
        return self.vendor_approval_ids._get_records_action(name=_('Vendor Approval Request%(ps)s', ps='s' * (self.vendor_approvals_count > 1)))

    def action_request_vendor_approval(self):
        self.ensure_one()
        approval_category = self.env.company.vendor_approval_category_id
        title = _('Invalid Approval Request')
        if not approval_category:
            return self._get_warning_notification(
                title=title,
                message=_(
                    'There is no approval category set in settings of %(company)s company.',
                    company=self.env.company.name,
                ),
            )
        if not self.requires_approval:
            return self._get_warning_notification(
                title=title, message=_('The current paretner does not require approval')
            )
        if not self.env.company.vendor_require_approval:
            return self._get_warning_notification(
                title=title,
                message=_(
                    'Vendor approvals are not required on %(company)s company.',
                    company=self.env.company.name,
                ),
            )
        if pending_requests := self.vendor_approval_ids.filtered(lambda approval: approval.request_status in ['new', 'pending']).exists():
            return self._get_warning_notification(
                title=title,
                message=_(
                    'A vendor approval request has already been raised for this vendor (i.e., %(approval_names)s). Please manage existing approvals before attempting to create a new one.',
                    approval_names=format_list(
                        self.env, pending_requests.mapped('name')
                    ),
                ),
            )
        self.vendor_state = 'under_review'
        return self.env['approval.request'].create(
            {
                'reference': _('Vendor Approval Request of %(vendor)s', vendor=self.name),
                'vendor_id': self.id,
                'category_id': approval_category.id,
                'request_owner_id': self.env.user.id,
                'date': fields.Date.today(),
            }
        )._get_records_action(name=_('Vendor Approval Request'))

    @api.model
    def _cron_check_vendor_expired_documents(self, batch_size=500):
        today = fields.Date.context_today(self)
        domain = (
            Domain('partner_type', 'in', ('vendor', 'both'))
            & Domain('vendor_state', '!=', 'expired_documents')
            & Domain('document_ids', 'any', [('expiry_date', '<=', today)])
        )
        vendors = self.search(domain, limit=batch_size)
        remaining = len(vendors) if len(vendors) < batch_size else self.search_count(domain)
        self.env['ir.cron']._commit_progress(remaining=remaining)
        vendors.vendor_state = 'expired_documents'
        self.env['ir.cron']._commit_progress(len(vendors))

    def _get_vendor_notification_data(self, partner_model_id, user, note, summary, activity_id):
        self.ensure_one()
        return {
            'res_model_id': partner_model_id,
            'res_id': self.id,
            'user_id': user.id,
            'activity_type_id': activity_id,
            'note': note,
            'summary': summary,
            'automated': True,
        }

    @api.model
    def _get_res_partner_notification_ids(self):
        return self.env['ir.model']._get_id('res.partner'), self.env.ref('mail.mail_activity_data_todo').id

    @api.model
    def _cron_notify_vendor_document_expiry(self, batch_size=500):
        company = self.env.company
        default_days = company.document_expiry_notify_users_days
        default_users_to_notify = company.document_expiry_notify_user_ids
        partner_model_id, activity_id = self._get_res_partner_notification_ids()
        # SQL query as days to notify users may differ per contact due to multi-company
        query = SQL(
            '''
                SELECT
                    PARTNER.ID AS PARTNER_ID,
                    ARRAY_AGG(DOC.ID) AS DOCS
                FROM
                    DOCUMENTS_DOCUMENT DOC
                    JOIN RES_PARTNER PARTNER ON PARTNER.ID = DOC.PARTNER_ID
                    LEFT JOIN RES_COMPANY COMPANY ON COMPANY.ID = PARTNER.COMPANY_ID
                WHERE
                    DOC.EXPIRY_DATE - CAST(COALESCE(COMPANY.DOCUMENT_EXPIRY_NOTIFY_USERS_DAYS, %(days)s) || ' ' || 'DAY' AS INTERVAL) <= CURRENT_DATE
                    AND PARTNER.PARTNER_TYPE IN ('vendor', 'both')
                    AND NOT EXISTS (
                        SELECT
                            1
                        FROM
                            MAIL_ACTIVITY ACTIVITY
                        WHERE
                            ACTIVITY.RES_MODEL_ID = %(partner_model_id)s
                            AND ACTIVITY.ACTIVE = TRUE
                            AND ACTIVITY.RES_ID = PARTNER.ID
                            AND ACTIVITY.IS_DOCUMENT_EXPIRY_NOTIFICATION = TRUE
                    )
                GROUP BY
                    PARTNER.ID;
            ''',
            days=default_days,
            partner_model_id=partner_model_id
        )
        self.env.cr.execute(query)
        vendor_expired_docs = dict(self.env.cr.fetchall())
        vendors = list(vendor_expired_docs.keys())
        vendors_batch = self.browse(vendors[:batch_size]).exists()
        remaining = len(vendors) if len(vendors) < batch_size else self.search_count(domain=Domain('id', 'in', vendors))
        self.env['ir.cron']._commit_progress(remaining=remaining)
        summary = _('Documents Expired.')
        vals_list = []
        for vendor in vendors_batch:
            users_to_notify = vendor.company_id.document_expiry_notify_user_ids or default_users_to_notify
            expired_doc_ids = self.env['documents.document'].browse(vendor_expired_docs.get(vendor.id)).exists()
            if not users_to_notify:
                _logger.error(
                    _(
                        'No users found to notify of the expired document%(ps)s %(expired_docs)s for %(vendor_name)s',
                        ps='s' * (len(expired_doc_ids) > 1),
                        expired_docs=format_list(self.env, expired_doc_ids.mapped('name')),
                        vendor_name=vendor.name,
                    )
                )
                continue
            note = _('Identified document%(ps)s: %(expired_docs)s.', ps='s' * (len(expired_doc_ids) > 1), expired_docs=format_list(self.env, expired_doc_ids.mapped('name')))
            vals_list += [{**vendor._get_vendor_notification_data(partner_model_id, user, note, summary, activity_id), 'is_document_expiry_notification': True} for user in users_to_notify
            ]
        self.env['mail.activity'].create(vals_list)
        self.env['ir.cron']._commit_progress(len(vendors_batch))

    @api.model
    def _cron_notify_vendor_modified(self, batch_size=500):
        company = self.env.company
        default_users_to_notify = company.vendor_modification_notify_user_ids
        partner_model_id, activity_id = self._get_res_partner_notification_ids()
        domain = (
            Domain('partner_type', 'in', ['vendor', 'both'])
            & Domain('vendor_state', '=', 'modified')
            & Domain('activity_ids', 'not any', Domain('is_vendor_modified_notification', '=', True))
        )
        modified_vendors = self.search(domain=domain, limit=batch_size)
        remaining = len(modified_vendors) if len(modified_vendors) < batch_size else self.search_count(domain)
        self.env['ir.cron']._commit_progress(remaining=remaining)
        summary = _('Vendor Modified.')
        note = _('Check the vendor for modified information.')
        vals_list = []
        notified_of_vendors = 0
        for vendor in modified_vendors:
            users_to_notify = vendor.company_id.vendor_modification_notify_user_ids or default_users_to_notify
            if not users_to_notify:
                _logger.error(_('No users found to notify for the modified vendor %(vendor_name)s', vendor_name=vendor.name))
                continue
            vals_list += [{**vendor._get_vendor_notification_data(partner_model_id, user, note, summary, activity_id), 'is_vendor_modified_notification': True} for user in users_to_notify]
            notified_of_vendors += 1
        if not vals_list:
            return
        self.env['mail.activity'].create(vals_list)
        self.env['ir.cron']._commit_progress(notified_of_vendors)
