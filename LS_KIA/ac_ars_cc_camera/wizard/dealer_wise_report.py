# -*- coding: utf-8 -*-

import xlsxwriter
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class DealerStreamingReport(models.TransientModel):
    _name = "dealer.streaming.report"
    _description = "Dealer Streaming Report"
    
    company_id = fields.Many2one('res.company', string='Company Name')
    is_region = fields.Boolean("Is Region")
    region_id = fields.Many2one('ac.ars.region.region', string='Region')
    from_date = fields.Date(string='From Date', required=True,
        default=lambda *a: datetime.strftime(datetime(date.today().year, date.today().month, 1), '%Y-%m-%d'))
    to_date = fields.Date(string='To Date', required=True, default=date.today().strftime('%Y-%m-%d'))
    dealer_streaming_data = fields.Char('Name', size=256)
    file_name = fields.Binary('Report Name', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    _sql_constraints = [
        ('check','CHECK((from_date <= to_date))',"To Date must be greater then From Date")
    ]

    @api.onchange('company_id')
    def onchange_company(self):
        _logger.info("Executing onchange_company...")
        if self.company_id and self.company_id.parent_id:
            self.region_id = self.company_id.region_id.id or False

    
    def print_dealer_streaming_report(self,company):
        _logger.info("Executing print_dealer_streaming_report...")
        if company:
            company_id = company
            region_id = company_id.region_id

        if self.from_date and self.to_date:
            from_date = self.from_date + ' ' + '00:00:00'
            to_date = self.to_date + ' ' + '23:59:59'
        else:
            current_date = str(datetime.now().date())
            from_date = current_date + ' ' + '00:00:00'
            to_date = current_date + ' ' + '23:59:59'
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        
        format0 = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'silver', 'font_size': 14})
        format1 = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'silver'})
        format2 = workbook.add_format({'bold': True, 'align': 'left'})
        format3 = workbook.add_format({'align': 'right'})

        sheet = workbook.add_worksheet('Dealer Streaming')
        sheet.merge_range(0, 0, 2, 9, 'Dealer Streaming Report', format0)

        sheet.write(4, 2, 'From Date: '+ str(from_date), format2)
        sheet.write(4, 4, 'To Date: '+ str(to_date), format2)
        sheet.write(4, 6, 'Region: '+ str(region_id.name or ''), format2)

        sheet.set_column(0, 0, 7)
        sheet.set_column(1, 1, 14)
        sheet.set_column(2, 2, 24)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 18)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 18)
        sheet.set_column(9, 9, 18)

        sheet.merge_range(6, 0, 7, 0, "Sl no", format1)
        sheet.merge_range(6, 1, 7, 1, "Region", format1)
        sheet.merge_range(6, 2, 7, 2, "Dealer Name", format1)
        sheet.merge_range(6, 3, 7, 3, "Dealer Code", format1)
        sheet.merge_range(6, 4, 7, 4, "Location", format1)
        sheet.merge_range(6, 5, 7, 5, "Vendor", format1)
        sheet.merge_range(6, 6, 7, 6, "No. of Bays \nwith Cameras", format1)
        sheet.merge_range(6, 7, 7, 7,"Total cars loaded in \nLive Streaming Bay", format1)
        sheet.merge_range(6, 8, 7, 8, "Total SMS / \nlink Sent", format1)
        sheet.merge_range(6, 9, 7, 9, "Total Customers  \nwho viewed the link", format1)
        if not self.is_region:
            self.env.cr.execute("""select
                  a.region_name
                , a.company_name
                , a.code
                , a.location
                , a.count
                , case when b.count_view > 0 then b.count_view else 0 end as count_view
                , case when c.count_mail is not null then c.count_mail else '0' end as count_mail
                , case when d.count_sms is not null then d.count_sms else '0' end as count_sms
                from(select
                      rc.name as company_name
                    , case when reg.name is not null then reg.name else '' end as region_name
                    , rc.dealer_code as code
                    , case when rp.city is not null then rp.city else '' end as location
                    , count(l.id) as count
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    inner join res_partner rp on rp.id = rc.partner_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY rc.name,region_name,code,location
                    ORDER BY rc.name asc
                )a
                left outer join(select
                      count(l.is_viewing) as count_view
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.is_viewing = true
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY company_name
                    ORDER BY company_name asc
                )b
                on a.company_name = b.company_name
                left outer join(select
                      count(l.id) as count_mail
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.mail_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY company_name
                    ORDER BY company_name asc
                )c
                on(a.company_name = c.company_name or b.company_name = c.company_name)
                left outer join(select
                      count(l.id) as count_sms
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.sms_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY company_name
                    ORDER BY company_name asc
                )d
                on(a.company_name = d.company_name or b.company_name = d.company_name or c.company_name = d.company_name)""")
        else:
            self.env.cr.execute("""select
                  a.region_name
                , a.company_name
                , a.code
                , a.location
                , a.count
                , case when b.count_view > 0 then b.count_view else 0 end as count_view
                , case when c.count_mail is not null then c.count_mail else '0' end as count_mail
                , case when d.count_sms is not null then d.count_sms else '0' end as count_sms
                from(select
                      rc.name as company_name
                    , case when reg.name is not null then reg.name else '' end as region_name
                    , rc.dealer_code as code
                    , case when rp.city is not null then rp.city else '' end as location
                    , count(l.id) as count
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    inner join res_partner rp on rp.id = rc.partner_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """+str(self.region_id and self.region_id.id or 0)+"""
                    GROUP BY rc.name,region_name,code,location
                    ORDER BY rc.name asc
                )a
                left outer join(select
                      count(l.is_viewing) as count_view
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.is_viewing = true
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """+str(self.region_id and self.region_id.id or 0)+"""
                    GROUP BY company_name
                    ORDER BY company_name asc
                )b
                on a.company_name = b.company_name
                left outer join(select
                      count(l.id) as count_mail
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.mail_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """+str(self.region_id and self.region_id.id or 0)+"""
                    GROUP BY company_name
                    ORDER BY company_name asc
                )c
                on(a.company_name = c.company_name or b.company_name = c.company_name)
                left outer join(select
                      count(l.id) as count_sms
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.sms_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """+str(self.region_id and self.region_id.id or 0)+"""
                    GROUP BY company_name
                    ORDER BY company_name asc
                )d
                on(a.company_name = d.company_name or b.company_name = d.company_name or c.company_name = d.company_name)""")
        results = self._cr.dictfetchall()
        row = 8
        count = 1
        for result in results:
            total_bay = len(self.env['ac.ars.live.streaming.settings'].search([('company_id.dealer_code', '=', result.get('code'))]).mapped('live_stream_ids'))
            sheet.write(row, 0, str(count))
            sheet.write(row, 1, str(result.get('region_name')))
            sheet.write(row, 2, str(result.get('company_name')))
            sheet.write(row, 3, str(result.get('code')))
            sheet.write(row, 4, str(result.get('location')))
            sheet.write(row, 5, str('Autochip'))
            sheet.write(row, 6, total_bay, format3)
            sheet.write(row, 7, str(result.get('count')), format3)
            sheet.write(row, 8, str(result.get('count_sms'))+ ' / ' +str(result.get('count_mail')), format3)
            sheet.write(row, 9, str(result.get('count_view')), format3)
            count += 1
            row += 1
        workbook.close()
        fp.seek(0)
        
        filename = f"Dealer_Streaming_Report_{str(from_date)[:10]}_to_{str(to_date)[:10]}.xlsx"
        
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

    
    def dealer_streaming_print_report(self):
        _logger.info("Executing dealer_streaming_print_report...")
        company = self.company_id if self.company_id else False
        return self.print_dealer_streaming_report(company)