# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class AcArsAllocationData(models.Model):
    _name = 'ac.ars.allocation.data'
    _description = 'Allocation Data'
    _rec_name = 'dms_ro_no'

    dms_ro_no = fields.Char("RO Number")
    partner_id = fields.Many2one('res.partner', 'Customer')
    user_id = fields.Many2one('res.users', 'User')
    company_id = fields.Many2one('res.company', 'Company')
    
    # Bay Planner Fields
    date_start = fields.Datetime("Start Date")
    date_end = fields.Datetime("End Date")
    resource_id = fields.Many2one('resource.resource', "Service Bay", domain=[('resource_category', '=', 'Bay')])
    state = fields.Selection([
        ('queue', 'In Queue'),
        ('scheduled', 'Scheduled'),
        ('live', 'Live Stream'),
        ('hold', 'Paused'),
        ('done', 'Completed')
    ], default='queue', string="Status")
    
    def write(self, vals):
        res = super(AcArsAllocationData, self).write(vals)
        if 'state' in vals:
            tokens = self.env['ac.ars.live.stream.token'].sudo().search([
                ('dms_ro_number', 'in', self.ids), 
                ('state', '=', 'valid')
            ])
            if vals['state'] == 'hold':
                for token in tokens:
                    token.ac_ars_live_streaming_pause('other', 'Paused from Bay Planner')
            elif vals['state'] not in ('live', 'hold', 'queue'):
                for token in tokens:
                    token.finish_live_stream()
        return res

    def action_resume_broadcast(self):
        self.ensure_one()
        _logger.info("action_resume_broadcast CALLED for ID: %s, RO: %s", self.id, self.dms_ro_no)
        
        token_obj = self.env['ac.ars.live.stream.token'].search([('dms_ro_number', '=', self.id)], limit=1)
        if token_obj and token_obj.status == 'hold':
            token_obj.ac_ars_live_streaming_resume()
            
        self.write({'state': 'live'})
        _logger.info("State updated back to 'live' from hold")



    def action_start_broadcast(self):
        self.ensure_one()
        _logger.info("=========================================")
        _logger.info("action_start_broadcast CALLED for ID: %s, RO: %s", self.id, self.dms_ro_no)
        self.write({'state': 'live'})
        _logger.info("State updated to 'live'")

        # Generate live stream link dynamically via token model
        token_obj = self.env['ac.ars.live.stream.token'].search([('dms_ro_number', '=', self.id)], limit=1)
        if not token_obj:
            token_values = {
                'user_id': self.env.user.id,
                'date': fields.Date.today(),
                'state': 'valid',
                'status': 'live',
                'company_id': self.env.company.id,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'dms_ro_number': self.id,
                'resource': self.resource_id.id if self.resource_id else False,
                'token': f"TOKEN-{self.id}",
                'url': "",
            }
            token_obj = self.env['ac.ars.live.stream.token'].sudo().create(token_values)
            _logger.info("Created Current LS Data (ac.ars.live.stream.token) ID: %s", token_obj.id)
        
        # ACTUALLY CALL PHP TO GET URL
        _logger.info("Generating live stream link...")
        res = token_obj.generate_live_stream_link()
        livestream_link = token_obj.url
        _logger.info("Generated Live Stream URL: %s", livestream_link)

        # START THE CAMERA STREAM EXPLICITLY
        _logger.info("Starting live stream proxy via NodeJS...")
        token_obj.ac_ars_live_streaming_camera_start()

        # 1. Send Email (Native Odoo 18 Mail)
        mail_rec = False
        _logger.info("Checking partner email: Partner ID=%s, Email=%s", self.partner_id.id if self.partner_id else None, self.partner_id.email if self.partner_id else None)
        if self.partner_id and self.partner_id.email:
            mail_values = {
                'subject': f"Live Stream Started for your vehicle: {self.dms_ro_no or 'N/A'}",
                'body_html': f"""
                    <div style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2 style="color: #EA0029;">Your Vehicle is Live!</h2>
                        <p>Dear {self.partner_id.name},</p>
                        <p>Your vehicle is currently being serviced and you can watch the live stream by clicking the button below:</p>
                        <a href="{livestream_link}" style="background-color: #EA0029; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 10px;">Watch Live Stream</a>
                    </div>
                """,
                'email_to': self.partner_id.email,
                'author_id': self.env.user.partner_id.id,
            }
            try:
                _logger.info("Creating mail.mail record...")
                mail_rec = self.env['mail.mail'].sudo().create(mail_values)
                if token_obj:
                    token_obj.sudo().write({'email_id': mail_rec.id})
                _logger.info("mail.mail record created. Calling send()...")
                mail_rec.send()
                _logger.info("Successfully sent Broadcast Email to %s", self.partner_id.email)
            except Exception as e:
                _logger.error("Failed to send Broadcast Email: %s", str(e))
        else:
            _logger.warning("Email not sent: No partner attached or partner has no email address.")

        # 2. Send SMS (Custom ac.ars.sms_api Integration)
        phone = False
        if self.partner_id:
            phone = self.partner_id.mobile or self.partner_id.phone
        
        _logger.info("Checking partner phone: Phone=%s", phone)
        if phone:
            try:
                _logger.info("Creating ac.ars.sms.record...")
                # Use custom SMS API module
                sms = self.env['ac.ars.sms.record'].sudo().create({
                    'name': self.partner_id.name,
                    'phone': phone,
                    'regno': self.dms_ro_no or '',
                    'url': livestream_link,
                    'company_id': self.env.company.id,
                })
                if token_obj:
                    token_obj.sudo().write({'sms_id': sms.id})
                _logger.info("ac.ars.sms.record created. Calling sent_an_sms()...")
                res = sms.sent_an_sms()
                if res:
                    _logger.info("Successfully sent Broadcast SMS to %s via ac_ars_sms_api", phone)
                else:
                    _logger.error("Failed to send Broadcast SMS: Check sms.record state: %s | Reason: %s", sms.stage, sms.failed_reason)
                    
                # 3. Send WhatsApp
                _logger.info("Checking WhatsApp configuration...")
                whatsapp_config = self.env['ac.ars.whatsapp.config'].sudo().search([('company_id', '=', self.env.company.id)], limit=1)
                if not whatsapp_config:
                    whatsapp_config = self.env['ac.ars.whatsapp.config'].sudo().search([], limit=1) # Fallback to global
                    
                if whatsapp_config:
                    _logger.info("Calling send_whatsapp()...")
                    whatsapp_config.send_whatsapp(self.partner_id.name, phone, self.dms_ro_no or '', livestream_link)
                    _logger.info("Successfully executed send_whatsapp to %s", phone)
                else:
                    _logger.warning("No WhatsApp configuration found for company.")
                    
            except Exception as e:
                _logger.error("Exception when sending Custom SMS/WhatsApp: %s", str(e))
        else:
            _logger.warning("SMS/WhatsApp not sent: Partner has no mobile or phone number.")
                
        _logger.info("=========================================")
        return True

    def delete_ac_ars_allocation_data(self):
        _logger.info("Executing delete_ac_ars_allocation_data...")
        if self.stage_id.name == 'New':
            sale_order = self.env['sale.order'].sudo().search([('dms_ro_number', '=', self.id)])
            self.project_task_id.unlink()
            self.vehicle_id.unlink()
            sale_order.unlink()
            return True
        else:
            return False

    @api.model
    def get_bay_planner_data(self, start_date=None, end_date=None, planner_id=None):
        # Fetch all planners for the dropdown
        planners = self.env['planner.calender'].search([('company_id', 'in', self.env.companies.ids)])
        planner_list = [{'id': p.id, 'name': p.name} for p in planners]

        # Determine active planner
        active_planner = None
        if planner_id:
            active_planner = self.env['planner.calender'].browse(planner_id)
        elif planners:
            active_planner = planners[0]

        bays = []

        if active_planner:
            # Fetch Bays
            for bay in active_planner.member_ids:
                bays.append({
                    'id': bay.id,
                    'name': bay.name,
                    'spec': "Standard Service",
                    'tech': bay.user_id.name if bay.user_id else "Unassigned"
                })

        # Fetch Allocations
        domain = []
        if start_date and end_date:
            domain = [
                '|',
                ('date_start', '=', False),
                '&',
                ('date_start', '>=', start_date + ' 00:00:00'),
                ('date_start', '<=', end_date + ' 23:59:59')
            ]
        
        domain.append(('company_id', 'in', self.env.companies.ids))
        alloc_records = self.search(domain)
        allocations = []
        for alloc in alloc_records:
            allocations.append({
                'id': alloc.id,
                'bay_id': alloc.resource_id.id if alloc.resource_id else False,
                'reg': alloc.dms_ro_no or "Unknown",
                'model': alloc.partner_id.name if alloc.partner_id else "Customer",
                'status': alloc.state or 'queue',
                'date_start': str(alloc.date_start) if alloc.date_start else False,
                'date_end': str(alloc.date_end) if alloc.date_end else False,
            })

        return {
            'planners': planner_list,
            'active_planner_id': active_planner.id if active_planner else False,
            'bays': bays,
            'allocations': allocations
        }

