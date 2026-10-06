from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date, datetime, timedelta
import datetime
import csv
import io
import base64
import logging
import requests
import json
import odoo.exceptions
# import odoo.osv.osv

_logger = logging.getLogger(__name__)


def _unescape(text):
    _logger.info("Executing _unescape...")
    from urllib.parse import unquote_plus
    try:
        text = unquote_plus(text.encode('utf8'))
        return text
    except Exception as e:
        return text


class LiveStreamWizard(models.Model):
    _name = "live.stream.wizard"
    live_stream = fields.Many2one('ir.attachment', help="Live Stream Record")
    mail_report = fields.Many2one('ir.attachment', help="Live Stream  Mail Report")
    name = fields.Char(string="Token")
    start_date = fields.Datetime(string="Date")
    end_date = fields.Datetime(string="Date")
    company_id = fields.Many2one('res.company', "Company")
    report_type = fields.Selection([('stream_report', 'Live Stream Report'), ('mail_report', 'Mail Report')],
                                   default='stream_report')

    # def print_report(self):
    #     lines = self.getlines()
    #     _logger.info("heloooo"
    # 
    # def print_multi_report(self):
    #     company_reg = self.company_id.company_registry
    #     start_date = self.start_date
    #     end_date = self.end_date
    #     report_type = self.report_type
    #     self.call_report_data(company_reg, start_date, end_date, report_type)

    
    def print_report(self):
        _logger.info("Executing print_report...")
        if self.report_type == 'stream_report':
            if not self.live_stream:
                self.getlines()
            if not self.live_stream:
                raise UserError("Live Stream Report Is Not Generated")
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % (self.live_stream.id),
                'target': 'new',
            }
        if self.report_type == 'mail_report':
            if not self.mail_report:
                self.getlines()
            if not self.mail_report:
                raise UserError("Live Stream Report Is Not Generated")
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % (self.mail_report.id),
                'target': 'new',
            }

    
    def getlines(self):
        _logger.info("Executing getlines...")
        attachment = False
        fp = io.StringIO()
        writer = csv.writer(fp, quoting=csv.QUOTE_NONE, escapechar='\\')
        maindata = []
        stream_ids = False
        if self.report_type == 'stream_report':
            domain = [('company_id', '=', self.company_id.id),
                      ('date', '>=', self.start_date),
                      ('date', '<=', self.end_date)]
            stream_ids = self.env['ac.ars.live.streaming'].search(domain)
        if self.report_type == 'mail_report':
            domain = [('company_id', '=', self.company_id.id),
                      ('start_datetime', '>=', self.start_date),
                      ('start_datetime', '<=', self.end_date),
                      ('entry_type', '=', 'actual')]
            stream_ids = self.env['calendar.event'].search(domain)

        if self.report_type == 'stream_report':
            for record in stream_ids:
                if record.streaming_duration and record.streaming_duration == False:
                    stream_duration = str(' ')
                else:
                    stream_duration = str(record.streaming_duration)
                line_data = [str(record.cust_name), str(record.name), stream_duration, str(record.state),
                             str(record.views_duration), str(record.click_count)]
                maindata.append(line_data)
        if self.report_type == 'mail_report':
            for record in stream_ids:
                # mail_data = self.env['mail.mail'].search(domain)
                sale_order_id = self.env['sale.order'].search([('id', '=', record.res_id)])
                stream_ids = self.env['ac.ars.live.streaming'].search([('name', '=', record.token)])
                if stream_ids:
                    line_data = [str(record.name), str(record.token), str(sale_order_id.partner_id.name),
                                 str(stream_ids.streaming_duration), str(stream_ids.views_duration),
                                 str(stream_ids.click_count)]
                else:
                    line_data = [str(record.name), str(record.token), str(sale_order_id.partner_id.name), ' ', ' ', ' ']
                maindata.append(line_data)
        # _logger.info(maindata)
        if maindata:
            header = []
            if self.report_type == 'stream_report':
                header = ['Customer Name', 'Token', 'Streaming Duration', 'State', 'Views Duration', 'Count of Click']
            if self.report_type == 'mail_report':
                header = ['Vehicle No', 'Token', 'Customer Name', 'Streaming Duration', 'Views Duration',
                          'Count of Click']
            writer.writerow(header)
            for lineData in maindata:
                writer.writerow([_unescape(name) for name in lineData])
            fp.seek(0)
            data = fp.read()
            fp.close()
            attachment = self.generateAttachment(data)
            if self.report_type == 'mail_report':
                self.mail_report = attachment
            else:
                self.live_stream = attachment
        else:
            raise UserError("No Data Found Between " + self.start_date + " and " + self.end_date)

    # 
    # def call_report_datas(self, dealer_code):
    #
    #     ip_address = self.company_id.ip_address
    #     database = self.company_id.database
    #     user = self.company_id.user
    #     password = self.company_id.password
    #     payload = {"db": str(database),
    #                "user": str(user), "password": str(password),
    #                "dealer_code": str(dealer_code), }
    #     url = "http://" + ip_address + "/api/get_streaming_data"
    #     # response = requests.request("POST", url, params=details)
    #     data_json = json.dumps(payload)
    #     headers = {'Content-Type': 'application/json'}
    #     response = requests.post(url, data=data_json, headers=headers)
    #     _logger.info(response.text)
    #     if response.text:
    #         response = json.loads(response.text)
    #         _logger.info(response)
    #     # response = requests.get(url, params=details)

    
    def getdelershiplines(self, dealer_code):
        _logger.info("Executing getdelershiplines...")
        maindata = []
        cam_datas = []
        sms_mail = []
        stream_ids = False
        _logger.info(self)
        resourses = self.env['resource.resource'].search([('resource_category', '=', 'Bay')])
        for resourse in resourses:
            cam_data = [resourse.name, len(resourse.ip_address)]
            cam_datas.append(cam_data)
        company_id = self.env['res.company'].search([('dealer_code', '=', dealer_code)])
        domain = [('company_id', '=', company_id.id),
                  ('retrive', '=', False)]
        stream_ids = self.env['ac.ars.live.streaming'].search(domain)
        if stream_ids:
            for record in stream_ids:
                stream_record = [record.name, record.date, record.cust_name, record.stream_start_time,
                                 record.stream_end_time, record.state, record.vehicle_no, record.sms_status,
                                 record.mail_status]
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            # sms_mail = [record.sms_status,record.mail_status]
                if record.live_stream_ids:
                    for lines in record.live_stream_ids:
                        stream_lines = [lines.session, lines.start_time, lines.end_time]
                        stream_record.append(stream_lines)
                maindata.append(stream_record)
                if record.state == 'finished':
                    record.write({'retrive': True})
                elif record.state == 'progress':
                    current_time = fields.Datetime.from_string(fields.Datetime.now())
                    duration = current_time - datetime.datetime.strptime(record.date, DEFAULT_SERVER_DATETIME_FORMAT)
                    if duration.days and duration.days > 2:
                        record.write({'retrive': True})
            return (maindata, cam_datas)
        else:
            return (maindata, cam_datas)

    def generateAttachment(self, data):
        _logger.info("Executing generateAttachment...")
        attachment = False
        base64Data = base64.b64encode(data.encode('utf-8'))
        current_time = fields.Datetime.from_string(fields.Datetime.now())
        datas_fname = '{}_{}.csv'.format(self.name, str(current_time))
        try:
            resId = 0
            if self._context.get('gst_id'):
                resId = self._context.get('gst_id')
            attachment = self.env['ir.attachment'].create({
                'datas': base64Data,
                'type': 'binary',
                'res_model': 'live.stream.wizard',
                'res_id': resId,
                'db_datas': datas_fname,
                'datas_fname': datas_fname,
                'name': datas_fname
            }
            )
        except ValueError:
            return attachment
        return attachment
