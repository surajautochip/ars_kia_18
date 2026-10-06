# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

import xlsxwriter
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class RegionStreamingReport(models.TransientModel):
    _name = "region.streaming.report"
    _description = "Region Streaming Report"

    company_id = fields.Many2one('res.company', string='Company Name')
    is_region = fields.Boolean("Is Region")
    region_id = fields.Many2one('ac.ars.region.region', string='Region')
    from_date = fields.Date(string='From Date', required=True,
                            default=lambda *a: datetime.strftime(datetime(date.today().year, date.today().month, 1),
                                                                 '%Y-%m-%d'))
    to_date = fields.Date(string='To Date', required=True, default=date.today().strftime('%Y-%m-%d'))
    region_streaming_data = fields.Char('Name', size=256)
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

    
    def print_region_streaming_report(self, company, region):
        _logger.info("Executing print_region_streaming_report...")
        if region:
            is_region = True
            region_id = region
        else:
            is_region = False
            region_id = company.region_id
        if company:
            company_id = company
            # region_id = company_id.region_id
        if self.from_date and self.to_date:
            from_date = self.from_date + ' ' + '00:00:00'
            to_date = self.to_date + ' ' + '23:59:59'
            month = datetime.strptime(self.from_date, '%Y-%m-%d').strftime('%m')
            year = datetime.strptime(self.from_date, '%Y-%m-%d').strftime('%Y')
            month_start = datetime.strftime(datetime(int(year), int(month), 1), '%Y-%m-%d') + ' ' + '00:00:00'
        else:
            current_date = str(datetime.now().date())
            month_start = datetime.strftime(datetime(date.today().year, date.today().month, 1),
                                            '%Y-%m-%d') + ' ' + '00:00:00'
            from_date = current_date + ' ' + '00:00:00'
            to_date = current_date + ' ' + '23:59:59'
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        
        format0 = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'silver', 'font_size': 14})
        format1 = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'silver'})
        format2 = workbook.add_format({'bold': True, 'align': 'left'})
        format3 = workbook.add_format({'align': 'right'})

        sheet = workbook.add_worksheet('Region Streaming')
        sheet.merge_range(0, 0, 2, 11, 'Region Streaming Report', format0)

        sheet.write(4, 2, 'From Date: ' + str(from_date), format2)
        sheet.write(4, 4, 'To Date: ' + str(to_date), format2)
        sheet.write(4, 6, 'Region: ' + str(region_id.name or ''), format2)

        sheet.set_column(0, 0, 7)
        sheet.set_column(1, 1, 14)
        sheet.set_column(2, 2, 24)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 18)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 18)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 11, 18)

        sheet.merge_range(6, 0, 7, 0, "Sl no", format1)
        sheet.merge_range(6, 1, 7, 1, "Region", format1)
        sheet.merge_range(6, 2, 7, 2, "Dealer Name", format1)
        sheet.merge_range(6, 3, 7, 3, "Dealer Code", format1)
        sheet.merge_range(6, 4, 7, 4, "Location", format1)
        sheet.merge_range(6, 5, 7, 5, "No. of Bays \nwith Cameras", format1)
        sheet.merge_range(6, 6, 7, 6, "Total cars loaded in \nLive Streaming Bay", format1)
        sheet.merge_range(6, 7, 7, 7, "Total SMS / \nlink Sent", format1)
        sheet.merge_range(6, 8, 7, 8, "MTD Total SMS/ \nLink Sent", format1)
        sheet.merge_range(6, 9, 7, 9, "Total Customers who \nviewed the link", format1)
        sheet.merge_range(6, 10, 7, 10, "MTD Total customers \nwho viewed the link", format1)
        sheet.merge_range(6, 11, 7, 11, "Total \nBrowsing time", format1)
        if not self.is_region and not is_region:
            self.env.cr.execute("""select
                  a.region_name
                , a.company_name
                , a.code
                , a.location
                , a.count
                , case when c.count_view > 0 then c.count_view else 0 end as count_view
                , case when b.view_duration is not null then b.view_duration else '00:00:00' end as total_duration
                , case when d.count_mail is not null then d.count_mail else '0' end as count_mail
                , case when e.count_sms is not null then e.count_sms else '0' end as count_sms
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
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY rc.name,region_name,code,location
                    ORDER BY rc.name asc
                )a
                left outer join(select
                      sum(ln.end_time - ln.start_time) as view_duration
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    inner join ac_ars_live_streaming_line ln on l.id = ln.line_stream_id
                    left outer join res_company rc on rc.id = l.company_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY company_name
                    ORDER BY company_name asc
                )b
                on a.company_name = b.company_name
                left outer join(select
                      count(l.is_viewing) as count_view
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.is_viewing = true
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY company_name
                    ORDER BY company_name asc
                )c
                on(a.company_name = c.company_name or  b.company_name = c.company_name)
                left outer join(select
                      count(l.id) as count_mail
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.mail_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY company_name
                    ORDER BY company_name asc
                )d
                on(a.company_name = d.company_name or b.company_name = d.company_name or c.company_name = d.company_name)
                left outer join(select
                      count(l.id) as count_sms
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.sms_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    GROUP BY company_name
                    ORDER BY company_name asc
                )e
                on(a.company_name = e.company_name or b.company_name = e.company_name or c.company_name = e.company_name or d.company_name = e.company_name)""")
        else:
            self.env.cr.execute("""select
                  a.region_name
                , a.company_name
                , a.code
                , a.location
                , case when f.count is not null then f.count else '0' end as count
                , case when c.count_view > 0 then c.count_view else 0 end as count_view
                , case when b.view_duration is not null then b.view_duration else '00:00:00' end as total_duration
                , case when d.count_mail is not null then d.count_mail else '0' end as count_mail
                , case when e.count_sms is not null then e.count_sms else '0' end as count_sms
                , case when f.montly_sms_count is not null then f.montly_sms_count else '0' end as montly_sms_count 
                , case when f.monthly_mail_count is not null then f.monthly_mail_count else '0' end as monthly_mail_count
                , case when f.montly_view_count is not null then f.montly_view_count else '0' end as montly_view_count
                from(select
                    rc.name as company_name, rc.dealer_code as code
                    , case when reg.name is not null then reg.name else '' end as region_name
                    , case when rp.city is not null then rp.city else '' end as location
                    , count(ls.id) as count
                    from res_company rc
                    left outer join ac_ars_live_streaming ls on ls.company_id = rc.id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    inner join res_partner rp on rp.id = rc.partner_id
                    where ls.company_id in (select distinct(id) from res_company
                    where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY rc.name,region_name,code,location
                    ORDER BY rc.name asc
                )a
                left outer join(select
                    sum(ln.end_time - ln.start_time) as view_duration
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    inner join ac_ars_live_streaming_line ln on l.id = ln.line_stream_id
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )b
                on a.company_name = b.company_name
                left outer join(select
                      count(l.is_viewing) as count_view
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.is_viewing = true
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )c
                on(a.company_name = c.company_name or  b.company_name = c.company_name)
                left outer join(select
                      count(l.id) as count_mail
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.mail_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )d
                on(a.company_name = d.company_name or b.company_name = d.company_name or c.company_name = d.company_name)
                left outer join(select
                      count(l.id) as count_sms
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.sms_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )e
                on(a.company_name = e.company_name or b.company_name = e.company_name or c.company_name = e.company_name or d.company_name = e.company_name)
                left outer join(
                select mst.montly_sms_count,mmt.monthly_mail_count,mvt.montly_view_count,
                case when mmt.company_name is not null then mmt.company_name else mst.company_name end as company_name,
                case when tlv.count is not null then tlv.count else '0' end as count
                from (  select count(mail_status) as monthly_mail_count,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where mail_status = 'sent' and ls.date between '""" + str(month_start) + """' and '""" + str(to_date) + """'
                        group by rs.name) mmt
                        full outer join (
                        select count(sms_status) as montly_sms_count ,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where sms_status = 'sent' and ls.date between '""" + str(month_start) + """' and '""" + str(to_date) + """'
                        group by rs.name) mst on mst.company_name = mmt.company_name
                        left outer join(
                        select count(is_viewing) as montly_view_count ,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where is_viewing = True and ls.date between '""" + str(month_start) + """' and '""" + str(to_date) + """'
                        group by rs.name) mvt on mvt.company_name = mmt.company_name or mvt.company_name = mst.company_name
                        left outer join(
                        select count(ls.id) as count ,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where ls.date between '"""+str(from_date) + """' and '"""+str(to_date) + """'
                        group by rs.name) tlv on tlv.company_name = mmt.company_name or tlv.company_name = mst.company_name 
                        or tlv.company_name = mvt.company_name
                )f 
                on(a.company_name = f.company_name or b.company_name = f.company_name or 
                c.company_name = f.company_name or d.company_name = f.company_name or e.company_name = f.company_name)
                """)
            _logger.info("""select
                  a.region_name
                , a.company_name
                , a.code
                , a.location
                , case when f.count is not null then f.count else '0' end as count
                , case when c.count_view > 0 then c.count_view else 0 end as count_view
                , case when b.view_duration is not null then b.view_duration else '00:00:00' end as total_duration
                , case when d.count_mail is not null then d.count_mail else '0' end as count_mail
                , case when e.count_sms is not null then e.count_sms else '0' end as count_sms
                , case when f.montly_sms_count is not null then f.montly_sms_count else '0' end as montly_sms_count 
                , case when f.monthly_mail_count is not null then f.monthly_mail_count else '0' end as monthly_mail_count
                , case when f.montly_view_count is not null then f.montly_view_count else '0' end as montly_view_count
                from(select
                    rc.name as company_name, rc.dealer_code as code
                    , case when reg.name is not null then reg.name else '' end as region_name
                    , case when rp.city is not null then rp.city else '' end as location
                    , count(ls.id) as count
                    from res_company rc
                    left outer join ac_ars_live_streaming ls on ls.company_id = rc.id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    inner join res_partner rp on rp.id = rc.partner_id
                    where ls.company_id in (select distinct(id) from res_company
                    where id = """ + str(company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY rc.name,region_name,code,location
                    ORDER BY rc.name asc
                )a
                left outer join(select
                    sum(ln.end_time - ln.start_time) as view_duration
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    inner join ac_ars_live_streaming_line ln on l.id = ln.line_stream_id
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )b
                on a.company_name = b.company_name
                left outer join(select
                      count(l.is_viewing) as count_view
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.is_viewing = true
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )c
                on(a.company_name = c.company_name or  b.company_name = c.company_name)
                left outer join(select
                      count(l.id) as count_mail
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.mail_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )d
                on(a.company_name = d.company_name or b.company_name = d.company_name or c.company_name = d.company_name)
                left outer join(select
                      count(l.id) as count_sms
                    , rc.name as company_name
                    from ac_ars_live_streaming l
                    left outer join res_company rc on rc.id = l.company_id
                    left outer join ac_ars_region_region reg on reg.id = rc.region_id
                    where l.date >= '""" + from_date + """' and l.date <= '""" + to_date + """'
                    and l.sms_status in ('sent', 'received')
                    and l.company_id in (select distinct(id) from res_company where id = """ + str(
                company_id and company_id.id or 0) + """
                    or parent_id = """ + str(company_id and company_id.id or 0) + """)
                    and reg.id = """ + str(region_id and region_id.id or 0) + """
                    GROUP BY company_name
                    ORDER BY company_name asc
                )e
                on(a.company_name = e.company_name or b.company_name = e.company_name or c.company_name = e.company_name or d.company_name = e.company_name)
                left outer join(
                select mst.montly_sms_count,mmt.monthly_mail_count,mvt.montly_view_count,
                case when mmt.company_name is not null then mmt.company_name else mst.company_name end as company_name,
                case when tlv.count is not null then tlv.count else '0' end as count
                from (  select count(mail_status) as monthly_mail_count,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where mail_status = 'sent' and ls.date between '""" + str(month_start) + """' and '""" + str(to_date) + """'
                        group by rs.name) mmt
                        full outer join (
                        select count(sms_status) as montly_sms_count ,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where sms_status = 'sent' and ls.date between '""" + str(month_start) + """' and '""" + str(to_date) + """'
                        group by rs.name) mst on mst.company_name = mmt.company_name
                        left outer join(
                        select count(is_viewing) as montly_view_count ,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where is_viewing = True and ls.date between '""" + str(month_start) + """' and '""" + str(to_date) + """'
                        group by rs.name) mvt on mvt.company_name = mmt.company_name or mvt.company_name = mst.company_name
                        left outer join(
                        select count(ls.id) as count ,rs.name as company_name from ac_ars_live_streaming ls 
                        left join res_company rs on ls.company_id = rs.id
                        where ls.date between '"""+str(from_date) + """' and '"""+str(to_date) + """'
                        group by rs.name) tlv on tlv.company_name = mmt.company_name or tlv.company_name = mst.company_name 
                        or tlv.company_name = mvt.company_name
                )f 
                on(a.company_name = f.company_name or b.company_name = f.company_name or 
                c.company_name = f.company_name or d.company_name = f.company_name or e.company_name = f.company_name)
                """)

        results = self._cr.dictfetchall()
        row = 8
        count = 1
        _logger.info("results",results)

        for result in results:
            total_bay = len(self.env['ac.ars.live.streaming.settings'].search(
                [('company_id.dealer_code', '=', result.get('code'))]).mapped('live_stream_ids'))
            sheet.write(row, 0, str(count))
            sheet.write(row, 1, str(result.get('region_name')))
            sheet.write(row, 2, str(result.get('company_name')))
            sheet.write(row, 3, str(result.get('code')))
            sheet.write(row, 4, str(result.get('location')))
            sheet.write(row, 5, total_bay, format3)
            sheet.write(row, 6, str(result.get('count')), format3)
            sheet.write(row, 7, str(result.get('count_sms')) + ' / ' + str(result.get('count_mail')), format3)
            sheet.write(row, 8, str(result.get('montly_sms_count')) + ' / ' + str(result.get('monthly_mail_count')),
                        format3)
            sheet.write(row, 9, str(result.get('count_view')), format3)
            sheet.write(row, 10, str(result.get('montly_view_count')), format3)
            sheet.write(row, 11, str(result.get('total_duration')), format3)
            count += 1
            row += 1
        workbook.close()
        fp.seek(0)
        
        filename = f"Region_Streaming_Report_{str(from_date)[:10]}_to_{str(to_date)[:10]}.xlsx"
        
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

    
    def region_streaming_print_report(self):
        _logger.info("Executing region_streaming_print_report...")
        comapny = self.company_id if self.company_id else False
        region = self.region_id if self.region_id else False
        return self.print_region_streaming_report(comapny, region)
