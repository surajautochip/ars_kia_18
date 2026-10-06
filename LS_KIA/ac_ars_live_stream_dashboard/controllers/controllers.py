# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import http
from odoo.http import request


class LiveStreamDashboard(http.Controller):
    @http.route('/ls_dashboard/data', type='json', auth='none')
    def DashBoardData(self, **kw):
        _logger.info("Executing DashBoardData...")
        cr = request.env.cr
        
        company = kw.get('company')
        option = kw.get('option')
        
        company_id = request.env['res.company'].sudo().search([('name', '=', company)])
        _logger.info("company %s", company_id)
        request.env.cr.execute("""
            select date_part('year', ls.date) as date_year,TO_CHAR(ls.date, 'Month') as date_month,count(ls.id) as live_count
                        from ac_ars_live_streaming ls left join res_company rc on rc.id = ls.company_id
                        where ls.date >=  to_char(CURRENT_DATE - INTERVAL '6 months', 'YYYY-MM-01')::date
                        and ls.company_id in (select id from res_company where id = """ + str(
            company_id.id) + """ or parent_id = """ + str(company_id.id) + """)
                        group by date_part('month', ls.date),date_month,date_year
                        order by date_part('year', ls.date),date_part('month', ls.date)
            """)
        all_data = cr.dictfetchall()
        ls_data, ls_count, total_c = [], [], 0
        for data in all_data:
            total_c += data['live_count']
            ls_data.extend([{'ls_month': data['date_month'][0:3] + "-" + str(data['date_year'])[2:4],
                             'ls_count': data['live_count']}])
        live_stream_data = request.env['ac.ars.live.streaming']
        args = [company_id, ], int(option)
        d_data = live_stream_data.sudo().get_live_stream_records_by_optional(int(option), company_id)
        c_total = self.customer_viewed_data(company_id.id)
        circle_val = (c_total / total_c) * 100 if c_total != 0 or total_c != 0 else 0
        _logger.info("%s, 100", circle_val)
        return {'ls_data': ls_data, 'd_data': d_data, 'circle_val': str(round(circle_val)) + ",100"}

    def customer_viewed_data(self, company):
        _logger.info("Executing customer_viewed_data...")
        cr = request.env.cr
        request.env.cr.execute("""
                    select date_part('year', date) as date_year,TO_CHAR(date, 'Month') as date_month,count(id) as live_count
                                from ac_ars_live_streaming where date >=  to_char(CURRENT_DATE - INTERVAL '6 months', 'YYYY-MM-01')::date
                                and is_viewing = true and company_id in (select id from res_company where id = """ + str(
                                company) + """ or parent_id = """ + str(company) + """)
                                group by date_part('month', date),date_month,date_year
                                order by date_part('year', date),date_part('month', date)
                    """)
        all_data = cr.dictfetchall()
        total_c = 0
        for data in all_data:
            total_c += data['live_count']
        return total_c
