# -*- coding: utf-8 -*-
import requests
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class AcArsWhatsappConfig(models.Model):
    _name = 'ac.ars.whatsapp.config'
    _description = 'WhatsApp Configuration'

    temp_name = fields.Text("Message Template", help="Use {name}, {regno}, {url} as placeholders")
    company_id = fields.Many2one('res.company')
    
    # IMIConnect Fields
    key = fields.Char("Key")
    url = fields.Char("URL")
    
    state = fields.Selection([('valid', 'Outgoing'), ('invalid', 'Invalid'), ('exception', 'Exception')])
    exception = fields.Char("Exception")

    def send_whatsapp(self, customer_name, customer_phone, plate_no, url_link):
        _logger.info("Executing send_whatsapp (IMIConnect)...")
        try:
            req_url = self.url or 'https://hooks.imiconnect.in/events/EMDDSABHQY'
            api_key = self.key or "902430dc-e034-11e9-9e4e-025282c394f2"
            
            headers = {
                "key": api_key, 
                "Content-Type": "application/json"
            }
            
            payload = {
                'Temp_Name': 'svc_servicebay', 
                'corr_id': 'N1200', 
                'msisdn': str(customer_phone).strip() if customer_phone else ''
            }
            
            params = [
                str(customer_name) if customer_name else "", 
                str(plate_no) if plate_no else "", 
                str(url_link) if url_link else ""
            ]
            payload.update({"params": params})
            
            req_payload = json.dumps(payload)
            
            _logger.info("Sending WhatsApp to: %s with payload: %s", customer_phone, req_payload)
            x = requests.post(url=req_url, data=req_payload, headers=headers)
            
            _logger.info("WhatsApp Response: %s", x.text)
            
            # Log the message
            self.env['ac.ars.whatsapp.log'].sudo().create({
                'name': customer_name,
                'mobile': customer_phone,
                'send_date': fields.Datetime.now(),
                'state': 'sent' if x.status_code in [200, 201] else 'exception',
                'description': req_payload,
                'exception': x.text if x.status_code not in [200, 201] else '',
                'whatsapp_config': self.id,
                'company_id': self.company_id.id
            })
            
            return x.text
        except Exception as e:
            _logger.exception("Error while sending WhatsApp")
            return str(e)


class AcArsWhatsappLog(models.Model):
    _name = 'ac.ars.whatsapp.log'
    _description = 'WhatsApp Log'

    name = fields.Char()
    code = fields.Char()
    transid = fields.Char()
    description = fields.Text()
    send_date = fields.Datetime()
    mobile = fields.Char()
    state = fields.Selection([('outgoing', 'Outgoing'), ('sent', 'Sent'), ('received', 'Received'),
                              ('exception', 'Delivery Failed'), ('cancel', 'Cancelled')])
    exception = fields.Text()
    partner_id = fields.Many2one('res.partner')
    whatsapp_config = fields.Many2one('ac.ars.whatsapp.config')
    user_id = fields.Many2one('res.users')
    company_id = fields.Many2one('res.company')
