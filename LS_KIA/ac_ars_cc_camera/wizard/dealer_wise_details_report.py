# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

import xlsxwriter
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class DealerStreamingDetailsReport(models.TransientModel):
    _name = "dealer.streaming.details.report"
    _description = "Dealer Streaming Details Report"

    company_id = fields.Many2one('res.company', string='Company Name')
    is_region = fields.Boolean("Is Region")
    region_id = fields.Many2one('ac.ars.region.region', string='Region')
    from_date = fields.Date(string='From Date', required=True,
                            default=lambda *a: datetime.strftime(datetime(date.today().year, date.today().month, 1),
                                                                 '%Y-%m-%d'))
    to_date = fields.Date(string='To Date', required=True, default=date.today().strftime('%Y-%m-%d'))
    dealer_streaming_data = fields.Char('Name', size=256)
    file_name = fields.Binary('Report Name', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    _sql_constraints = [
        ('check', 'CHECK((from_date <= to_date))', "To Date must be greater then From Date")
    ]

    @api.onchange('company_id')
    def onchange_company(self):
        _logger.info("Executing onchange_company...")
        if self.company_id and self.company_id.parent_id:
            self.region_id = self.company_id.region_id.id or False

    
    def dealer_streaming_detail_report(self,company):
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

        sheet = workbook.add_worksheet('Dealer Streaming Details')
        sheet.merge_range(0, 0, 2, 13, 'Dealer Streaming Details Report', format0)

        sheet.write(4, 2, 'From Date: ' + str(from_date), format2)
        sheet.write(4, 4, 'To Date: ' + str(to_date), format2)
        sheet.write(4, 6, 'Region: ' + str(region_id.name or ''), format2)

        sheet.set_column(0, 0, 7)
        sheet.set_column(1, 1, 14)
        sheet.set_column(2, 2, 24)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 18)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 18)
        sheet.set_column(7, 7, 24)
        sheet.set_column(8, 13, 18)

        sheet.merge_range(6, 0, 7, 0, "Sl no", format1)
        sheet.merge_range(6, 1, 7, 1, "Region", format1)
        sheet.merge_range(6, 2, 7, 2, "Dealer Name", format1)
        sheet.merge_range(6, 3, 7, 3, "Dealer Code", format1)
        sheet.merge_range(6, 4, 7, 4, "Location", format1)
        sheet.merge_range(6, 5, 7, 5, "Regd. No", format1)
        sheet.merge_range(6, 6, 7, 6, "Date", format1)
        sheet.merge_range(6, 7, 7, 7, "Customer \nname", format1)
        sheet.merge_range(6, 8, 7, 8, "Technician \nStart time", format1)
        sheet.merge_range(6, 9, 7, 9, "Technician \nEnd time", format1)
        sheet.merge_range(6, 10, 7, 10, "Customer \nViewed time", format1)
        sheet.merge_range(6, 11, 7, 11, "Customer \nBrowsing time", format1)
        sheet.merge_range(6, 12, 7, 12, "Customer \nReview", format1)
        sheet.merge_range(6, 13, 7, 13, "Feedback", format1)
        if not self.is_region:
            self.env.cr.execute("""select 
                  a.region_name
                , a.company_name
                , a.code
                , a.location
                , a.regd_no
                , a.date
                , a.customer                
                , a.feedback
                , a.review
                , a.tech_start
                , case when  a.tech_end::varchar is not null then a.tech_end::varchar else '' end as tech_end
                , case when b.start_time is not null then b.start_time else '00:00:00' end as start_time
                , case when b.view_duration is not null then b.view_duration else '00:00:00' end as view_duration
                from(select
                      case when reg.name is not null then reg.name else '' end as region_name
                    , rc.name as company_name
                    , rc.dealer_code as code
                    , case when rp.city is not null then rp.city else '' end as location
                    , case when l.vehicle_no is not null then l.vehicle_no else '' end as regd_no
                    , (select (to_char((l.date::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp2.tz from res_partner rp2 inner join res_users u on rp2.id = u.partner_id where u.id = (1)), 'DD-MM-YYYY') )) as date   
                    , l.cust_name as customer
                    , case when l.feedback is not null then l.feedback else '' end as feedback
                    , case when l.review is null then '0 Star' else l.review || ' Star' end as review
                    , (select (to_char((l.stream_start_time::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp2.tz from res_partner rp2 inner join res_users u on rp2.id = u.partner_id where u.id = (1)), 'HH:MI:SS AM') )) as tech_start                    
                    , (select (to_char((l.stream_end_time::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp2.tz from res_partner rp2 inner join res_users u on rp2.id = u.partner_id where u.id = (1)), 'HH:MI:SS AM') )) as tech_end    
                    , l.id
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    inner join res_partner rp on rp.id = rc.partner_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    ORDER BY rc.name asc
                )a
                left outer join (select
                      sum(ln.end_time - ln.start_time) as view_duration
                    , l.id
                    , (select (to_char((ln2.start_time::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), 'HH:MI:SS') ) as start_time 
                    from ac_ars_live_streaming_line ln2 where ln2.line_stream_id = ln.line_stream_id order by ln2.id asc limit 1)    
                    from ac_ars_live_streaming l
                    inner join ac_ars_live_streaming_line ln on l.id = ln.line_stream_id
                    left outer join res_company rc on rc.id = l.company_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY l.id,ln.line_stream_id,rc.name
                    ORDER BY l.id asc
                )b on a.id = b.id ORDER BY a.company_name,a.date """)
        else:
            self.env.cr.execute("""select 
                  a.region_name
                , a.company_name
                , a.code
                , a.location
                , a.regd_no
                , a.date
                , a.customer
                , a.feedback
                , a.review
                , a.tech_start
                , case when  a.tech_end::varchar is not null then a.tech_end::varchar else '' end as tech_end
                , case when b.view_duration is not null then b.view_duration else '00:00:00' end as view_duration
                , case when b.start_time is not null then b.start_time else '00:00:00' end as start_time
                , a.feedback as feedback
                from(select
                      case when reg.name is not null then reg.name else '' end as region_name
                    , rc.name as company_name
                    , rc.dealer_code as code
                    , case when rp.city is not null then rp.city else '' end as location
                    , case when l.vehicle_no is not null then l.vehicle_no else '' end as regd_no
                    , (select (to_char((l.date::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp2.tz from res_partner rp2 inner join res_users u on rp2.id = u.partner_id where u.id = (1)), 'DD-MM-YYYY') )) as date   
                    , l.cust_name as customer
                    , case when l.feedback is not null then l.feedback else '' end as feedback
                    , case when l.review is null then '0 Star' else l.review || ' Star' end as review
                    , (select (to_char((l.stream_start_time::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp2.tz from res_partner rp2 inner join res_users u on rp2.id = u.partner_id where u.id = (1)), 'HH:MI:SS AM') )) as tech_start                    
                    , (select (to_char((l.stream_end_time::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp2.tz from res_partner rp2 inner join res_users u on rp2.id = u.partner_id where u.id = (1)), 'HH:MI:SS AM') )) as tech_end 
                    , l.id
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    inner join res_partner rp on rp.id = rc.partner_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(self.region_id and self.region_id.id or 0) + """
                    ORDER BY rc.name asc
                )a
                left outer join (select
                      sum(ln.end_time - ln.start_time) as view_duration
                    , l.id
                    , (select (to_char((ln2.start_time::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 
                        (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), 'HH:MI:SS') ) as start_time 
                    from ac_ars_live_streaming_line ln2 where ln2.line_stream_id = ln.line_stream_id order by ln2.id asc limit 1)    
                    from ac_ars_live_streaming l
                    inner join ac_ars_live_streaming_line ln on l.id = ln.line_stream_id
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(self.region_id and self.region_id.id or 0) + """
                    GROUP BY l.id,ln.line_stream_id,rc.name
                    ORDER BY l.id asc
                )b on a.id = b.id ORDER BY a.company_name,a.date """)
        results = self._cr.dictfetchall()
        _logger.info('results', results)
        row = 8
        count = 1
        _logger.info("results",results)
        for result in results:
            sheet.write(row, 0, str(count))
            sheet.write(row, 1, str(result.get('region_name')))
            sheet.write(row, 2, str(result.get('company_name')))
            sheet.write(row, 3, str(result.get('code')))
            sheet.write(row, 4, str(result.get('location')))
            sheet.write(row, 5, str(result.get('regd_no')))
            sheet.write(row, 6, str(result.get('date')), format3)
            sheet.write(row, 7, str(result.get('customer')), format3)
            sheet.write(row, 8, str(result.get('tech_start')), format3)
            sheet.write(row, 9, str(result.get('tech_end')), format3)
            sheet.write(row, 10, str(result.get('start_time')), format3)
            sheet.write(row, 11, str(result.get('view_duration')), format3)
            sheet.write(row, 12, str(result.get('review')), format3)
            sheet.write(row, 13, str(result.get('feedback')), format3)
            count += 1
            row += 1
        workbook.close()
        fp.seek(0)
        
        filename = f"Customer_Wise_Report_{str(from_date)[:10]}_to_{str(to_date)[:10]}.xlsx"
        
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

    
    def print_dealer_streaming_detail(self):
        _logger.info("Executing print_dealer_streaming_detail...")
        company = self.company_id if self.company_id else False
        return self.dealer_streaming_detail_report(company)
