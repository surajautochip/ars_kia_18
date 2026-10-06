# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import requests
import re

_logger = logging.getLogger(__name__)

class AcArsSmsRecord(models.Model):
    _name = 'ac.ars.sms.record'
    _description = 'SMS Record'
    
    name = fields.Char(string="Customer Name")
    phone = fields.Char(string="Phone Number")
    date = fields.Datetime(string="Date")
    token = fields.Many2one('ac.ars.live.streaming')
    company_id = fields.Many2one('res.company', "Company")
    failed_reason = fields.Char()
    body = fields.Html()
    response = fields.Html()
    url = fields.Text()
    regno = fields.Char()
    stage = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('exception', 'Delivery Failed'),
        ('cancel', 'Cancelled'),
        ('not_found', 'Not Found')])

    def sent_an_sms(self):
        _logger.info("Executing sent_an_sms...")
        for record in self:
            company = record.company_id.id
            phone = record.phone
            name = record.name
            url_decode = record.url
            regno = record.regno
            try:
                pattern = r"^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$"
                if phone and re.match(pattern, phone):
                    domain = [('company_id', '=', company), ('active', '=', True)]
                    ac_ars_sms_api_rec = self.env['ac.ars.sms.configure'].search(domain, limit=1)
                    if not ac_ars_sms_api_rec:
                        ac_ars_sms_api_rec = self.env['ac.ars.sms.configure'].search([('active', '=', True), ('sms_global', '=', True)], limit=1)
                        
                    if ac_ars_sms_api_rec:
                        values = ac_ars_sms_api_rec.sent_sms(phone, name, url_decode, regno)
                        record.body = values.get('body')
                        record.response = values.get('response')
                        record.stage = 'sent'
                        return True
                    else:
                        record.stage = 'not_found'
                        return False
                else:
                    record.stage = 'exception'
                    record.failed_reason = "***Invalid Number***"
                    return False
            except Exception as e:
                record.stage = 'exception'
                record.failed_reason = str(e)
                return False

class AcArsSmsConfigure(models.Model):
    _name = 'ac.ars.sms.configure'
    _description = 'SMS Configure'

    name = fields.Char()
    phone = fields.Char()
    active = fields.Boolean()
    rest_api = fields.Boolean()
    message = fields.Text()
    ac_ars_sms_api = fields.Text()
    company_id = fields.Many2one('res.company', "Company")
    val_ids = fields.One2many('ac.ars.sms.configure.line', 'values_id')
    sms_global = fields.Boolean()

    def test_sms_connection(self):
        for rec in self:
            response_vals = rec.sent_sms(rec.phone or '1234567890', rec.name or 'Test Name', '', '')
            response = response_vals.get('response', 'No response')
            url_built = response_vals.get('body', '')
            raise UserError(f"Test Connection Result:\n\nURL Built:\n{url_built}\n\nResponse:\n{response}")

    def sent_sms(self, phone, name, url_decode, regno):
        _logger.info("Executing sent_sms...")
        vals = {}
        message = self.message or ""
        if name and 'customer_name' in message:
            message = message.replace('customer_name', name)
        if regno and 'regno' in message:
            message = message.replace('regno', regno)
        if url_decode and 'url_decode' in message:
            message = message.replace('url_decode', url_decode)
            
        url = (self.ac_ars_sms_api or "").strip()
        is_twilio = 'api.twilio.com' in url
        twilio_auth = None
        twilio_data = {}
        twilio_sid = ""
        twilio_token = ""
        
        if self.val_ids:
            separator = '?' if '?' not in url else '&'
            for idx, params in enumerate(self.val_ids):
                p_val = (params.value or "").strip()
                p_name = (params.name or "").strip()
                
                # Resolve dynamic values
                if p_val == 'phone':
                    resolved_val = phone
                elif p_val == 'message':
                    resolved_val = message
                else:
                    resolved_val = p_val

                if is_twilio:
                    if p_name == 'AccountSid':
                        twilio_sid = resolved_val
                    elif p_name == 'AuthToken':
                        twilio_token = resolved_val
                    elif p_name == 'From':
                        twilio_data['From'] = resolved_val
                    elif p_name == 'To':
                        twilio_data['To'] = resolved_val
                    elif p_name == 'Body':
                        twilio_data['Body'] = resolved_val
                else:
                    param_sep = separator if idx == 0 else '&'
                    url = f"{url}{param_sep}{p_name}={resolved_val}"
                    
        if is_twilio:
            twilio_auth = (twilio_sid, twilio_token)
            response = self.api_call(url, auth=twilio_auth, data=twilio_data)
        else:
            response = self.api_call(url)
        response_text = response.text if hasattr(response, 'text') else str(response)
        _logger.info("--- SMS GATEWAY DEBUG ---")
        _logger.info("Constructed URL: %s", url)
        _logger.info("Gateway Response: %s", response_text)
        _logger.info("-------------------------")
        vals.update({"body": url, "response": response_text})
        return vals

    def api_call(self, url, auth=None, data=None):
        _logger.info("Executing api_call...")
        if url:
            try:
                if auth and data:
                    # Twilio style
                    response = requests.post(url, auth=auth, data=data)
                elif self.rest_api:
                    response = requests.post(url)
                else:
                    response = requests.get(url)
                return response
            except Exception as error:
                return error
        return None

    def get_mail_status(self):
        _logger.info("Executing get_mail_status...")
        live_streaming_ids = self.env['ac.ars.live.streaming'].search([])
        for li in live_streaming_ids:
            if not li.sms_status and li.name:
                # Replaced SQL injection with Odoo ORM equivalent. 
                # Note: this matches exact word logic or subset in body
                sms_rec = self.env['ac.ars.sms.record'].search([('body', 'ilike', li.name)], limit=1)
                if sms_rec:
                    li.sms_status = sms_rec.stage
            if not li.mail_status and li.name:
                mail_rec = self.env['mail.mail'].search([('body_html', 'ilike', li.name)], limit=1)
                if mail_rec:
                    li.mail_status = mail_rec.state

class AcArsSmsConfigureLine(models.Model):
    _name = 'ac.ars.sms.configure.line'
    _description = 'SMS Configure Line'
    
    name = fields.Char()
    value = fields.Char()
    values_id = fields.Many2one('ac.ars.sms.configure')
