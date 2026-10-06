# -*- coding: utf-8 -*-

import xlsxwriter
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class AnalysisStreamingReport(models.TransientModel):
    _name = "analysis.streaming.report"
    _description = "Analysis Streaming Report"
    
    is_region = fields.Boolean("Is Region")
    region_id = fields.Many2one('ac.ars.region.region', string='Region')
    analysis_streaming_data = fields.Char('Name', size=256)
    file_name = fields.Binary('Report Name', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    
    def print_analysis_streaming_report(self):
        _logger.info("Executing print_analysis_streaming_report...")
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        
        format0 = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'silver', 'font_size': 14})
        format1 = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'silver'})
        format2 = workbook.add_format({'align': 'center'})
        
        sheet = workbook.add_worksheet('Analysis Streaming')
        sheet.merge_range(0, 0, 2, 4, 'Analysis Streaming Report', format0)

        sheet.write(4, 2, 'Region: '+ str(self.region_id.name or 'All'), format2)

        sheet.set_column(0, 1, 18)
        sheet.set_column(2, 2, 24)
        sheet.set_column(3, 4, 18)

        sheet.merge_range(6, 0, 7, 0, "No. of Workshops", format1)
        sheet.merge_range(6, 1, 7, 1, "No. of Bays \nwith Cameras", format1)
        sheet.merge_range(6, 2, 7, 2, "Total cars loaded in Live \nStreaming Bay", format1)
        sheet.merge_range(6, 3, 7, 3, "Total SMS / \nlink Sent", format1)
        sheet.merge_range(6, 4, 7, 4, "Total Customers \nwho viewed the \nlink", format1)
        total_workshop = total_bay = total_streaming = total_email = total_sms = total_viewed = 0
        if not self.is_region:
            total_workshop = self.env['res.company'].search_count([('parent_id','!=', False)])
            total_bay = len(self.env['ac.ars.live.streaming.settings'].search([]).mapped('live_stream_ids'))
            total_streaming = self.env['ac.ars.live.streaming'].search_count([])
            total_email = self.env['ac.ars.live.streaming'].search_count([('mail_status', 'in', ['sent', 'received'])])
            total_sms = self.env['ac.ars.live.streaming'].search_count([('sms_status', 'in', ['sent', 'received'])])
            total_viewed = len(self.env['ac.ars.live.streaming'].search([('is_viewing', '=', True)]))
        else:
            total_workshop = self.env['res.company'].search_count([('region_id','=', self.region_id.id),('parent_id','!=', False)])
            company_ids = self.env['res.company'].search([('region_id','=', self.region_id.id),('parent_id','!=', False)])
            total_bay = len(self.env['ac.ars.live.streaming.settings'].search([('company_id', 'in', company_ids.ids)]).mapped('live_stream_ids'))
            total_streaming = self.env['ac.ars.live.streaming'].search_count([('company_id', 'in', company_ids.ids)])
            total_email = self.env['ac.ars.live.streaming'].search_count([('company_id', 'in', company_ids.ids), ('mail_status', 'in', ['sent', 'received'])])
            total_sms = self.env['ac.ars.live.streaming'].search_count([('company_id', 'in', company_ids.ids), ('sms_status', 'in', ['sent', 'received'])])
            total_viewed = len(self.env['ac.ars.live.streaming'].search([('company_id', 'in', company_ids.ids), ('is_viewing', '=', True)]))

        sheet.write(8, 0, total_workshop, format2)
        sheet.write(8, 1, total_bay, format2)
        sheet.write(8, 2, total_streaming, format2)
        sheet.write(8, 3, str(total_sms) +' / '+ str(total_email), format2)
        sheet.write(8, 4, total_viewed, format2)
        workbook.close()
        fp.seek(0)
        
        filename = "Analysis_Streaming_Report.xlsx"
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(fp.read()),
            'res_model': self._name,
            'res_id': self.id
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new'
        }

    
    def analysis_streaming_print_report(self):
        _logger.info("Executing analysis_streaming_print_report...")
        return self.print_analysis_streaming_report()