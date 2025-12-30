# -*- coding: utf-8 -*-

import json
from datetime import timedelta
from urllib.parse import urljoin

import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from requests.exceptions import HTTPError


class BioTimeServer(models.Model):
    _name = 'biotime.server'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'BioTime Server'

    name = fields.Char(string='Server Name', help='Name of Server ex: UAE company A server', required=True)
    server_ip = fields.Char(help='External IP address', required=True)
    port = fields.Integer(string='Port Number', help='Port to reach server', required=True, default=80)
    admin_username = fields.Char(help='Admin username of the BioTime 8.5 server')
    admin_password = fields.Char(help='Admin password of the BioTime 8.5 server')
    department_code = fields.Char(required=True)
    area_code = fields.Char(required=True)
    tz_offset = fields.Integer('UTC timezone difference', help='ex: +4, -2', required=True)
    active = fields.Boolean(default=True)
    duplicate_threshold = fields.Integer(default=60, help='Number of seconds to consider two punches as duplicates')
    authentication_payload = fields.Json()
    jwt_token = fields.Char()

    last_attendance_sync = fields.Datetime()

    url = fields.Char(compute='_compute_url')

    @api.constrains('active')
    def _constraint_unique_server(self):
        if self.search_count([]) > 1:
            raise ValidationError(_('You can not have more than one active server at a time'))

    @api.depends('server_ip', 'port')
    def _compute_url(self):
        for record in self:
            record.url = 'http://{}:{}'.format(record.server_ip, record.port)

    def get_jwt_token(self, raise_alert=True):
        self.ensure_one()

        headers = {'Content-Type': 'application/json'}

        try:
            payload = json.loads(self.authentication_payload) if self.authentication_payload else {'username': self.admin_username, 'password': self.admin_password}
            url_path = self.env['ir.config_parameter'].sudo().get_param('zkteco_biopro_attendance.zkteco_auth_endpoint', '/jwt-api-token-auth/')
            response = requests.post(urljoin(self.url, url_path), json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            response = response.json()

            if response.get('token'):
                self.jwt_token = response.get('token')
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success !'),
                        'message': _('Connected successfully'),
                        'sticky': True,
                        'type': 'success',
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
            else:
                msg = _('Could not connect to server {}'.format(self.name))

        except Exception as e:
            msg = _('Could not connect to server {}: {}'.format(self.name, e))

        if raise_alert:
            raise UserError(msg)

    @api.model
    def _get_asset_from_server(self, asset_type='employee', page=1, page_size=100, attendance_list=None):
        if not attendance_list:
            attendance_list = []
        headers = self._generate_jwt_headers(self.jwt_token)

        endpoint = '/personnel/api/employees/'
        query_params = '?page={}&page_size={}'.format(page, page_size)

        if asset_type == 'transaction':
            endpoint = '/iclock/api/transactions/'

            # only query fingerprint punches not already synced
            # Timezone timedelta manipulation. On odoo time is stored in UTC whereas on biotime it will be local time
            if self.last_attendance_sync:
                biotime_last_attendance_sync = self.last_attendance_sync + timedelta(hours=self.tz_offset)
                request_start_time = biotime_last_attendance_sync.strftime('%Y-%m-%d+%H:%M:%S')
                query_params += '&start_time={}'.format(request_start_time)

        try:
            response = requests.get(self.url + endpoint + query_params, headers=headers, timeout=30)
            response.raise_for_status()
            response = response.json()

            if response.get('data'):
                attendance_list += response.get('data')

            # recursively get all attendances across pages
            if response.get('next'):
                attendance_list = self._get_asset_from_server(asset_type, page + 1, page_size, attendance_list)
        except HTTPError as e:
            self.message_post(body=_('Error when trying to get assets:\n %s') % str(e))
        except Exception as e:
            self.message_post(body=_('Error when trying to get %s records:\n %s') % (asset_type, str(e)))

        return attendance_list

    def _generate_jwt_headers(self, jwt_token):
        prefix = self.env['ir.config_parameter'].sudo().get_param('zkteco_biopro_attendance.zkteco_prefix', 'JWT')
        return {
            'Authorization': prefix + ' {}'.format(jwt_token), 'Content-Type': 'application/json'
        }
