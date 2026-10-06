# -*- coding: utf-8 -*-
import json
import requests
import logging
import pytz
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class live_stream_token(models.Model):
    _inherit = 'ac.ars.live.stream.token'

    dms_response = fields.Text()
    update_on = fields.Datetime('Update On')
    end_time = fields.Datetime()

    def get_dms_login_token(self, payload={}):
        _logger.info("Executing get_dms_login_token...")
        dms_url = self.env['ir.config_parameter'].sudo().get_param('dms.url')
        try:
            user = self.env.user
            headers = {'Content-Type': 'application/json'}
            dealer_code = self.company_id.dealer_code
            payload.update({'user_id': user.dms_uid, 'dealer_no': dealer_code})
            dms_url += '/api/selectUserToken'
            data_json = json.dumps(payload)
            dms_token = requests.post(url=dms_url, data=data_json, headers=headers)
            # dms_ = self.env['ir.config_parameter'].sudo().get_param('dms.user.token')
            response = json.dumps(dms_token.json())
            return json.loads(response)
        except Exception as e:
            _logger.info(f"Error while generate token {e}")
            return False

    def send_live_stream_link(self, rate=None, command=None, feedback=None):
        _logger.info("Executing send_live_stream_link...")
        dms_url = self.env['ir.config_parameter'].sudo().get_param('dms.url') or ''
        user_tz = pytz.timezone(self.env.context.get('tz') or self.user_id.tz or 'UTC')
        payload = {}
        try:
            user = self.user_id
            now = fields.Datetime.from_string(fields.Datetime.now())
            now = (now.replace(tzinfo=pytz.utc).astimezone(user_tz)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            dms_res = ''
            self.update_on = now
            if user.dms_auth_token:
                headers = {'Content-Type': 'application/json', 'Authorization': user.dms_auth_token}
                dealer_code = self.company_id.dealer_code
                payload.update({'dlr_no': dealer_code,
                                'ro_no': self.dms_ro_number.dms_ro_no,
                                'reg_no': self.plan_event_id.name,
                                'cust_name': self.partner_id.name,
                                'mobile_no': self.partner_id.phone,
                                'email_id': self.partner_id.email,
                                'start_time': str(self.event_id.start) if self.event_id.start else '',
                                'end_time': '' if self.state in ('draft', 'valid') else str(self.update_on),
                                'start_date': str(self.event_id.start.date()) if self.event_id.start else '',
                                'schedule_status': 'O' if self.state in ('draft', 'valid') else str('D'),
                                'ls_url': self.url,
                                'rating_added': 'N' if rate is None else 'Y',
                                'ls_ratings': command if command is not None else False,
                                'ls_comments': feedback if feedback is not None else False
                                })
                dms_url += '/api/createLsForRo'
                data_json = json.dumps(payload)
                # _logger.info('\nURL & JSON',dms_url,data_json)
                dms_token = requests.post(url=dms_url, data=data_json, headers=headers)
                response = json.dumps(dms_token.json())
                dms_res = json.loads(response)
                self.dms_response = dms_res
                _logger.info(f"Successfully updated DMS server {dms_res}")
                # _logger.info("\nDMS Status\n",dms_res)
                return {'status': True, 'message': f"Successfully updated DMS server {dms_res}"}
            else:
                # _logger.info("\nDMS Status\n", dms_res)
                self.dms_response = "Valid authentication token not found"
                return {'status': False, 'message': "Valid authentication token not found"}
        except Exception as e:
            # _logger.info("\nDMS Status\n", e)
            self.dms_response = str(e)
            _logger.error(f"Error while connecting to the server {e}")
            return {'status': False, 'message': f"Error while connecting to the server {e}"}

    def finish_live_stream(self):
        _logger.info("Executing finish_live_stream...")
        res = super(live_stream_token, self).finish_live_stream()
        # now = fields.Datetime.from_string(fields.Datetime.now())
        self.end_time = fields.Datetime.from_string(fields.Datetime.now())
        self.send_live_stream_link()
        return res
