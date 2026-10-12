# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class AcArsLiveStreamDashboard(models.Model):
    _inherit = 'ac.ars.live.streaming'

    def get_customer_viewed_records(self, year, company):
        _logger.info("Executing get_customer_viewed_records...")
        cr = self.env.cr
        cr.execute("""SELECT count(ls.id) as live_count, TO_CHAR(ls.date, 'Month') as date_month,
                                date_part('year', ls.date) as date_year
                                FROM ac_ars_live_streaming ls 
                                JOIN ac_ars_live_streaming_line ls_line ON ls.id = ls_line.line_stream_id
                                WHERE date_part('year', ls.date) = %s
                                GROUP BY date_part('month', ls.date), date_month, date_year
                                ORDER BY date_part('month', ls.date)""", (year,))
        data = cr.fetchall()
        return data

    @api.model
    def get_live_stream_records(self):
        _logger.info("Executing get_live_stream_records...")
        cr = self.env.cr
        year = date.today().year
        company = self.env.company
        res = []
        cr.execute("""SELECT TO_CHAR(date, 'Month') as date_month, count(id) as live_count, is_viewing,
                        date_part('year', date) as date_year
                        FROM ac_ars_live_streaming WHERE date_part('year', date) = %s
                        GROUP BY is_viewing, date_part('month', date), date_month, date_year
                        ORDER BY date_part('month', date)""", (year,))
        data = cr.fetchall()

        ls_vw_data = []
        values = set(map(lambda x: x[0], data))
        newlist = [[y for y in data if y[0] == x] for x in values]

        t_cv_count, t_n_cv_count, total_count = 0, 0, 0
        for ls_month_data in newlist:
            cv_count, n_cv_count, t_count = 0, 0, 0
            ls_vw_month = None
            for ls in ls_month_data:
                ls_vw_month = ls[0]
                if ls[2] == True:
                    cv_count += ls[1]
                else:
                    n_cv_count += ls[1]
                t_count += ls[1]
            t_cv_count += cv_count
            t_n_cv_count += n_cv_count
            total_count += t_count
            ls_vw_data.append([ls_vw_month, t_count, cv_count if cv_count else 0, n_cv_count if n_cv_count else 0])

        res.append({
            'company': company.name, 'year': year, 'res': ls_vw_data,
            't_cv_count': t_cv_count, 't_n_cv_count': t_n_cv_count, 'total_count': total_count
        })
        return res

    @api.model
    def get_dashboard_stats(self):
        """Return MTD, LMTD, and 6-month bar chart data for the dashboard."""
        _logger.info("Executing get_dashboard_stats...")
        cr = self.env.cr
        company = self.env.company
        today = date.today()

        # --- Build company ID list (current + all child companies) ---
        company_ids = [company.id]
        cr.execute("SELECT id FROM res_company WHERE parent_id = %s", (company.id,))
        for row in cr.fetchall():
            company_ids.append(row[0])
        company_ids_tuple = tuple(company_ids)

        # --- MTD: current month, 1st to today ---
        mtd_start = today.replace(day=1)
        today_end = today + timedelta(days=1)
        cr.execute("""
            SELECT
                COUNT(t.id) AS total,
                SUM(CASE WHEN ls.is_viewing = TRUE THEN 1 ELSE 0 END) AS viewed,
                SUM(CASE WHEN ls.is_viewing = TRUE THEN 0 ELSE 1 END) AS not_viewed
            FROM ac_ars_live_stream_token t
            LEFT JOIN ac_ars_live_streaming ls ON t.token = ls.name
            WHERE t.company_id IN %s
              AND t.date >= %s AND t.date < %s
        """, (company_ids_tuple, mtd_start, today_end))
        mtd_row = cr.fetchone() or (0, 0, 0)
        mtd_total = mtd_row[0] or 0
        mtd_viewed = mtd_row[1] or 0
        mtd_not_viewed = mtd_row[2] or 0

        # --- LMTD: last month, 1st to same day as today ---
        last_month_today = today - relativedelta(months=1)
        lmtd_start = last_month_today.replace(day=1)
        lmtd_end = last_month_today
        lmtd_end_plus_one = lmtd_end + timedelta(days=1)
        cr.execute("""
            SELECT
                COUNT(t.id) AS total,
                SUM(CASE WHEN ls.is_viewing = TRUE THEN 1 ELSE 0 END) AS viewed,
                SUM(CASE WHEN ls.is_viewing = TRUE THEN 0 ELSE 1 END) AS not_viewed
            FROM ac_ars_live_stream_token t
            LEFT JOIN ac_ars_live_streaming ls ON t.token = ls.name
            WHERE t.company_id IN %s
              AND t.date >= %s AND t.date < %s
        """, (company_ids_tuple, lmtd_start, lmtd_end_plus_one))
        lmtd_row = cr.fetchone() or (0, 0, 0)
        lmtd_total = lmtd_row[0] or 0
        lmtd_viewed = lmtd_row[1] or 0
        lmtd_not_viewed = lmtd_row[2] or 0

        # --- Response Rate ---
        mtd_rate = round((mtd_viewed / mtd_total * 100), 1) if mtd_total > 0 else 0.0
        lmtd_rate = round((lmtd_viewed / lmtd_total * 100), 1) if lmtd_total > 0 else 0.0

        def pct_change(curr, prev):
            if prev == 0:
                return '+100%' if curr > 0 else '0%'
            change = round(((curr - prev) / prev) * 100, 1)
            return ('+' if change >= 0 else '') + str(change) + '%'

        # --- 6-month bar chart ---
        bar_months = []
        for i in range(5, -1, -1):
            month_date = today - relativedelta(months=i)
            m_start = month_date.replace(day=1)
            m_end = (m_start + relativedelta(months=1)) - timedelta(days=1)
            m_end_plus_one = m_end + timedelta(days=1)
            cr.execute("""
                SELECT COUNT(t.id) FROM ac_ars_live_stream_token t
                WHERE t.company_id IN %s AND t.date >= %s AND t.date < %s
            """, (company_ids_tuple, m_start, m_end_plus_one))
            count = (cr.fetchone() or (0,))[0] or 0
            bar_months.append({
                'label': month_date.strftime('%b'),
                'count': count,
            })

        # --- Camera stats from ac.ars.ip.camera ---
        try:
            cameras = self.env['ac.ars.ip.camera'].sudo().search([
                ('company_id', 'in', company_ids)
            ])
            total_cameras = len(cameras)
            online_cameras = len(cameras.filtered(lambda c: c.status == 'online'))
            offline_cameras = total_cameras - online_cameras
            camera_list = [{
                'name': c.cam_name or c.name or 'Camera',
                'status': c.status or 'offline',
                'ip': c.name or '',
            } for c in cameras[:6]]
        except Exception as e:
            _logger.warning("Camera stats error: %s", e)
            total_cameras, online_cameras, offline_cameras, camera_list = 0, 0, 0, []

        # --- Utilization Analysis ---
        # 1. Total Stream Hours (MTD)
        cr.execute("""
            SELECT SUM(EXTRACT(EPOCH FROM (end_date - start_date))) / 3600.0
            FROM ac_ars_camera_records
            WHERE company_id IN %s
              AND start_date >= %s AND start_date <= %s
        """, (company_ids_tuple, mtd_start, today + timedelta(days=1)))
        stream_hours_mtd = cr.fetchone()[0] or 0.0
        stream_hours_mtd = round(stream_hours_mtd, 1)

        # 2. Bay Usage (MTD)
        cr.execute("""
            SELECT r.name, COUNT(a.id)
            FROM ac_ars_allocation_data a
            JOIN resource_resource r ON a.resource_id = r.id
            WHERE a.company_id IN %s
              AND a.date_start >= %s AND a.date_start <= %s
            GROUP BY r.name
            ORDER BY COUNT(a.id) DESC
            LIMIT 3
        """, (company_ids_tuple, mtd_start, today + timedelta(days=1)))
        bay_data = cr.fetchall()
        
        cr.execute("""
            SELECT COUNT(id)
            FROM ac_ars_allocation_data
            WHERE company_id IN %s
              AND date_start >= %s AND date_start <= %s
        """, (company_ids_tuple, mtd_start, today + timedelta(days=1)))
        total_allocations = cr.fetchone()[0] or 1 # avoid div by zero
        
        bay_list = []
        for bay in bay_data:
            pct = int(round((bay[1] / total_allocations) * 100))
            bay_list.append({'name': bay[0], 'pct': pct})

        return {
            'company': company.name,
            'dealer_code': company.dealer_code or '',
            'today': today.strftime('%d %b %Y'),
            'month': today.strftime('%B %Y'),
            'mtd': {
                'total': mtd_total,
                'viewed': mtd_viewed,
                'not_viewed': mtd_not_viewed,
                'rate': mtd_rate,
            },
            'lmtd': {
                'total': lmtd_total,
                'viewed': lmtd_viewed,
                'not_viewed': lmtd_not_viewed,
                'rate': lmtd_rate,
            },
            'change': {
                'total': pct_change(mtd_total, lmtd_total),
                'viewed': pct_change(mtd_viewed, lmtd_viewed),
                'not_viewed': pct_change(mtd_not_viewed, lmtd_not_viewed),
                'rate': pct_change(mtd_rate, lmtd_rate),
            },
            'bar_months': bar_months,
            'cameras': {
                'total': total_cameras,
                'online': online_cameras,
                'offline': offline_cameras,
                'list': camera_list,
            },
            'utilization': {
                'stream_hours': stream_hours_mtd,
                'cam_utilization_pct': int(round((online_cameras / total_cameras * 100) if total_cameras > 0 else 0)),
                'bay_list': bay_list,
            },
        }

    def dashboard_query(self, s_date, e_date, company):
        _logger.info("Executing dashboard_query...")
        query = """SELECT to_char(date,'YYYY-MM-DD'), COUNT(*) AS Count, is_viewing AS CV
                    FROM ac_ars_live_streaming
                    WHERE date between %s and %s
                    and company_id in (select id from res_company where id = %s or parent_id = %s)
                    GROUP BY to_char(date,'YYYY-MM-DD'), is_viewing
                    ORDER BY to_char(date,'YYYY-MM-DD') ASC"""
        return query

    @api.model
    def get_live_stream_records_by_optional(self, args, company_id=None):
        _logger.info("Executing get_live_stream_records_by_optional...")
        today = date.today()
        today_str = today.strftime("%Y-%m-%d %H:%M:%S")
        date_time_obj = datetime.strptime(str(today_str), '%Y-%m-%d %H:%M:%S')
        days_count = int(args) / 7
        cr = self.env.cr
        s_date = date_time_obj + timedelta(days=1)
        dy_cnt_add, ac_ls_data, ac_cv_count, ac_n_cv_count, ac_days = 0, [], [], [], []
        company = company_id if company_id else self.env.company

        while dy_cnt_add != int(args):
            t_count, cv_count, n_cv_count = 0, 0, 0
            ls_date = s_date - timedelta(days=int(days_count))
            query = self.dashboard_query(ls_date, s_date, company)
            cr.execute(query, (str(ls_date.date()), str(s_date.date()), company.id, company.id))
            data = cr.fetchall()
            for o in data:
                if o[2] == True:
                    cv_count += o[1]
                else:
                    n_cv_count += o[1]
                t_count += o[1]
            ac_ls_data.append(t_count)
            ac_cv_count.append(cv_count if cv_count else 0)
            ac_n_cv_count.append(n_cv_count if n_cv_count else 0)
            ac_days.append(str(ls_date.strftime("%B")[:3]) + "/" + str(ls_date.day))
            s_date = ls_date
            dy_cnt_add += days_count

        return {
            'ac_ls_data': ac_ls_data, 'ac_cv_count': ac_cv_count,
            'ac_n_cv_count': ac_n_cv_count, 'ac_days': ac_days
        }

    @api.model
    def show_total_link_sent(self, args):
        _logger.info("Executing show_total_link_sent...")
        company = [self.env.company.id]
        today = date.today()
        cr = self.env.cr
        cr.execute("SELECT id FROM res_company where parent_id = %s", (company[0],))
        data = cr.fetchall()
        for ls in data:
            company.append(ls[0])
        stop_date = today - timedelta(days=int(args))
        today_end = today + timedelta(days=1)
        domain = [('date', '<', today_end), ('date', '>=', stop_date), ('company_id', 'in', company)]
        return domain

    @api.model
    def show_customer_viewed_record(self, args):
        _logger.info("Executing show_customer_viewed_record...")
        company = [self.env.company.id]
        today = date.today()
        cr = self.env.cr
        cr.execute("SELECT id FROM res_company where parent_id = %s", (company[0],))
        data = cr.fetchall()
        for ls in data:
            company.append(ls[0])
        stop_date = today - timedelta(days=int(args) + int(args) / 7)
        today_end = today + timedelta(days=1)
        domain = [('date', '<', today_end), ('date', '>=', stop_date),
                  ('company_id', 'in', company), ('is_viewing', '=', True)]
        return domain

    @api.model
    def show_customer_not_viewed_record(self, args):
        _logger.info("Executing show_customer_not_viewed_record...")
        company = [self.env.company.id]
        today = date.today()
        cr = self.env.cr
        cr.execute("SELECT id FROM res_company where parent_id = %s", (company[0],))
        data = cr.fetchall()
        for ls in data:
            company.append(ls[0])
        stop_date = today - timedelta(days=int(args) + int(args) / 7)
        today_end = today + timedelta(days=1)
        domain = [('date', '<', today_end), ('date', '>=', stop_date),
                  ('company_id', 'in', company), ('is_viewing', '=', False)]
        return domain
