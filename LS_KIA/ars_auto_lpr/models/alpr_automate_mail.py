from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import base64


class AlprAutomateMail(models.Model):
    _name = 'alpr.mail.conf'

    name = fields.Char()
    user_id = fields.Many2one('res.users', "User")
    email = fields.Char("Email Id")
    subject = fields.Text()
    email_body = fields.Html()

    def generateAttachment(self, enc_data, file_name):
        _logger.info("Executing generateAttachment...")
        date_today = str(datetime.now().date())
        datas_fname = '{}_{}.pdf'.format(file_name, date_today)
        try:
            attachment = self.env['ir.attachment'].create({
                'datas': enc_data,
                'type': 'binary',
                'res_model': 'mail.mail',
                'res_id': self.id,
                'db_datas': datas_fname,
                'datas_fname': datas_fname,
                'name': file_name + '_Report',
            }
            )
        except ValueError:
            return False
        return attachment

    
    def alpr_sheduled_mail(self):
        _logger.info("Executing alpr_sheduled_mail...")
        alpr_obj = self.env['alpr.mail.conf'].search([])
        for obj in alpr_obj:
            obj.sent_mail()


    
    def sent_mail(self):
        _logger.info("Executing sent_mail...")
        type= 'alpr_mail'
        mail_values = {
            'email_to': self.email,
            'subject': self.subject,
            'body_html': self.email_body,
        }
        report_obj=self.env['bay.count.wizard']
        data = report_obj.get_bay_count_data(type)
        attachment = self.generateAttachment(base64.b64encode(data),type)
        mail_obj = self.env['mail.mail'].create(mail_values)
        mail_obj.write({'attachment_ids': [(4, attachment.id)]})
        mail_obj.send()
