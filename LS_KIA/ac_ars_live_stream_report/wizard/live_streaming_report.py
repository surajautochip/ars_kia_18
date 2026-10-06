import io
import base64
import calendar
from datetime import date
import xlsxwriter
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LiveStreamingReportWizard(models.TransientModel):
    _name = 'live.stream.report'
    _description = 'Live Streaming SQL Report'

    from_date = fields.Date(required=False)
    to_date = fields.Date(required=False)
    company_id = fields.Many2one('res.company', string='Dealer', required=False)
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    dealer_count = fields.Integer('Total Number of Dealership')
    expected_ls_per_date = fields.Integer(default=3)
    period_type = fields.Selection([
        ('date', 'Custom Date'),
        ('month', 'Monthly'),
        ('quarter', 'Quarterly'),
        ('year', 'Annual'),
    ], default='month', required=True)

    def _year_selection(self):
        current_year = fields.Date.from_string(fields.Date.today()).year
        return [(str(y), str(y)) for y in range(current_year - 5, current_year + 1)]

    year = fields.Selection(
        selection=_year_selection,
        string='Year',
        required=True,
        default=lambda self: str(fields.Date.from_string(fields.Date.today()).year)
    )

    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month')

    quarter = fields.Selection([
        ('1', 'Q1 (Jan–Mar)'),
        ('2', 'Q2 (Apr–Jun)'),
        ('3', 'Q3 (Jul–Sep)'),
        ('4', 'Q4 (Oct–Dec)'),
    ], string='Quarter')

    def _get_date_range(self):
        today = date.today()
        year = int(self.year)

        if self.period_type == 'month':
            if not self.month:
                raise UserError(_("Please select Month"))
            month = int(self.month)
            last_day = calendar.monthrange(year, month)[1]
            return date(year, month, 1), date(year, month, last_day)

        if self.period_type == 'quarter':
            if not self.quarter:
                raise UserError(_("Please select Quarter"))
            q = int(self.quarter)
            start_month = (q - 1) * 3 + 1
            end_month = start_month + 2
            last_day = calendar.monthrange(year, end_month)[1]
            return date(year, start_month, 1), date(year, end_month, last_day)

        if self.period_type == 'year':
            return date(year, 1, 1), date(year, 12, 31)

        if not self.from_date or not self.to_date:
            raise UserError(_("Please select From and To dates"))

        return self.from_date, self.to_date

    def action_export_excel(self):
        from_date, to_date = self._get_date_range()
        today = date.today()
        params = {
            'from_date': from_date,
            'to_date': to_date,
            'is_today': from_date == today,
        }
        dealer_filter = ""
        if self.company_id:
            dealer_filter = "AND lsr.dealer_name = %(company_id)s"
            params['company_id'] = self.company_id.id

        sql = f"""
                WITH bay_count_cte AS (
                    SELECT
                        pc.company_id,
                        COUNT(DISTINCT rr.id) AS bay_count,
                        COUNT(DISTINCT cam.ip_camera_id) AS cam_count
                    FROM resource_resource rr
                    JOIN resource_category rsc 
                        ON rr.resource_category = rsc.id
                        AND rsc.code = 'BAY'
                    JOIN planner_calender pc 
                        ON rr.planner_calender_id = pc.id
                    LEFT JOIN ip_camera_resource_resource_rel cam 
                        ON rr.id = cam.resource_resource_id
                    WHERE cam.ip_camera_id IS NOT NULL and rr.active = true
                    GROUP BY pc.company_id
                ),
                latest_cam_exp AS (
                    SELECT
                        camexp.ip_cam_id,
                        camexp.duration,
                        ROW_NUMBER() OVER (
                            PARTITION BY camexp.ip_cam_id
                            ORDER BY camexp.create_date DESC
                        ) AS rn
                    FROM ip_camera_exp camexp
                ),
                camera_status_cte AS (
                    SELECT
                        pc.company_id,
                        COUNT(DISTINCT CASE 
                            WHEN ipcam.status = 'online' 
                            THEN cam.ip_camera_id 
                        END) AS online_cam_count,
                        COUNT(DISTINCT CASE 
                            WHEN ipcam.status = 'offline' 
                            THEN cam.ip_camera_id 
                        END) AS offline_cam_count,
                        COUNT(DISTINCT CASE 
                            WHEN ipcam.status IS NULL 
                              OR ipcam.status NOT IN ('online','offline')
                            THEN cam.ip_camera_id 
                        END) AS unknown_cam_count,
                        STRING_AGG(
                            DISTINCT CASE 
                                WHEN ipcam.status = 'offline'
                                 AND lce.rn = 1
                                THEN lce.duration
                            END,
                            ', '
                        ) AS offline_duration,
                        STRING_AGG(
                            DISTINCT CASE 
                                WHEN (ipcam.status IS NULL 
                                   OR ipcam.status NOT IN ('online','offline'))
                                 AND lce.rn = 1
                                THEN lce.duration
                            END,
                            ', '
                        ) AS unknown_duration
                    FROM resource_resource rr
                    JOIN resource_category rsc 
                        ON rr.resource_category = rsc.id
                        AND rsc.code = 'BAY'
                    JOIN planner_calender pc 
                        ON rr.planner_calender_id = pc.id
                    LEFT JOIN ip_camera_resource_resource_rel cam 
                        ON rr.id = cam.resource_resource_id
                    LEFT JOIN ip_camera ipcam 
                        ON ipcam.id = cam.ip_camera_id
                    LEFT JOIN latest_cam_exp lce 
                        ON lce.ip_cam_id = ipcam.id
                        AND lce.rn = 1
                    GROUP BY pc.company_id
                ),
                onboard_date_cte AS (
                    SELECT 
                        company_id, 
                        MIN(date) AS onboard_date
                    FROM live_streaming
                    GROUP BY company_id
                ),
                lsln_duration AS (
                    SELECT
                        lsl.line_stream_id,
                        EXTRACT(EPOCH FROM (lsl.end_time - lsl.start_time)) AS duration_secs
                    FROM live_streaming_line lsl
                    JOIN live_streaming ls
                        ON lsl.line_stream_id = ls.id
                    WHERE lsl.start_time IS NOT NULL
                      AND lsl.end_time IS NOT NULL
                      AND ls.date >= %(from_date)s
                        AND ls.date <  (%(to_date)s::date + INTERVAL '1 day')
                ),
                live_stream_summary AS (
                    SELECT
                        ls.company_id,
                        COUNT(DISTINCT ls.id) AS total_streams,
                        COUNT(DISTINCT ls.id) FILTER (WHERE ls.sms_status IN ('sent', 'received')) AS ls_rec_sms,
                        COUNT(DISTINCT ls.id) FILTER (WHERE ls.mail_status IN ('sent', 'received')) AS ls_rec_email,
                        COUNT(DISTINCT ls.id) FILTER (WHERE ls.is_viewing = TRUE) AS ls_cv_record,
                        COUNT(DISTINCT ls.id) FILTER (WHERE ls.is_viewing = FALSE) AS ls_cnv_record,
                        COUNT(lsln_duration.line_stream_id) AS click_count,
                        CONCAT(
                            FLOOR(SUM(lsln_duration.duration_secs) / 3600), ' hr, ',
                            FLOOR(MOD(SUM(lsln_duration.duration_secs), 3600) / 60), ' mnt, ',
                            FLOOR(MOD(SUM(lsln_duration.duration_secs), 60)), ' sec'
                        ) AS total_views_duration
                    FROM live_streaming ls
                    LEFT JOIN lsln_duration
                           ON lsln_duration.line_stream_id = ls.id
                    WHERE ls.date >= %(from_date)s
                        AND ls.date <  (%(to_date)s::date + INTERVAL '1 day')
                    GROUP BY ls.company_id
                )
                SELECT 
                    lsr.dealer_code,
                    rc1.name AS dealer_name,
                    zo.name AS zone,
                    rg.name AS region, 
                    DATE(odc.onboard_date) AS onboard_date,
                    COALESCE(bcc.bay_count, 0) AS bay_count,
                    COALESCE(bcc.cam_count, 0) AS cam_count,
                    COALESCE(csc.online_cam_count, 0) AS online_cam_count,
                    COALESCE(csc.offline_cam_count, 0) AS offline_cam_count,
                    COALESCE(csc.unknown_cam_count, 0) AS unknown_cam_count,
                    COALESCE(csc.offline_duration, '-') AS offline_duration,
                    COALESCE(csc.unknown_duration, '-') AS unknown_duration,
                    COALESCE(lsr_sum.total_streams, 0) AS total_streams,
                    COALESCE(lsr_sum.ls_rec_sms, 0) AS ls_rec_sms,
                    COALESCE(lsr_sum.ls_rec_email, 0) AS ls_rec_email,
                    COALESCE(lsr_sum.ls_cv_record, 0) AS ls_cv_record,
                    COALESCE(lsr_sum.ls_cnv_record, 0) AS ls_cnv_record,
                    COALESCE(lsr_sum.click_count, 0) AS click_count,
                    COALESCE(lsr_sum.total_views_duration, '0 hr, 0 mnt, 0 sec') AS total_views_duration
                FROM ls_status_report lsr
                LEFT JOIN res_company rc1 ON lsr.dealer_name = rc1.id
                LEFT JOIN res_partner rp1 ON lsr.partner_id = rp1.id
                LEFT JOIN region_region rg ON lsr.region_id = rg.id
                LEFT JOIN zone_zone zo ON lsr.zone_id = zo.id
                LEFT JOIN area_area ar ON lsr.area_id = ar.id
                LEFT JOIN res_country_state rcs ON lsr.state_id = rcs.id
                LEFT JOIN res_partner rp2 ON lsr.area_manager_id = rp2.id
                LEFT JOIN res_partner rp3 ON lsr.tpsm_id = rp3.id
                LEFT JOIN bay_count_cte bcc ON rc1.id = bcc.company_id
                LEFT JOIN camera_status_cte csc ON rc1.id = csc.company_id
                LEFT JOIN onboard_date_cte odc ON rc1.id = odc.company_id
                LEFT JOIN live_stream_summary lsr_sum ON rc1.id = lsr_sum.company_id
                WHERE lsr.ls_status = 'y' {dealer_filter}
        """

        self.env.cr.execute(sql, params)
        rows = self.env.cr.fetchall()
        cols = [d[0] for d in self.env.cr.description]

        if not rows:
            return

        column_mapping = {
            'dealer_code': 'W/S Code',
            'region': 'Region',
            'zone': 'Zone',
            'dealer_name': 'Dealer Name',
            'bay_count': 'No. Of Bays with Camera',
            'cam_count': 'Total Number of Camera',
            'online_cam_count': 'No. of Cameras Online',
            'offline_cam_count': 'No. of Camera Offline',
            'unknown_cam_count': 'No. of Camera (Non-Operational/unknown)',
            'offline_duration': 'No. of Days Camera has been offline',
            'unknown_duration': 'No. of Days Camera has under Unknown category',
            'total_streams': 'Total Cars Loaded in LS Bay',
            'ls_rec_sms': 'Total SMS Link Sent',
            'ls_rec_email': 'Total E-mail Sent',
            'ls_cv_record': 'Total Customer Viewed Link',
            'ls_cnv_record': 'Total Customer Not Viewed Link',
            'click_count': 'Customer Clicks',
            'total_views_duration': 'Total Duration of Live Streaming (Hrs)',
            'onboard_date': 'Rollout Completion Date'
        }

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Live Streaming Report')
        bold = workbook.add_format({'bold': True})

        headers = ['Sl No'] + [column_mapping.get(c, c) for c in cols]
        for i, h in enumerate(headers):
            worksheet.write(0, i, h, bold)

        for row_num, row_data in enumerate(rows, 1):
            worksheet.write(row_num, 0, row_num)
            for col_num, cell_data in enumerate(row_data, 1):
                if hasattr(cell_data, 'strftime'):
                    cell_data = cell_data.strftime('%Y-%m-%d')
                worksheet.write(row_num, col_num, cell_data)
        
        workbook.close()
        output.seek(0)
        
        attachment = self.env['ir.attachment'].create({
            'name': f'LS_Dump_{str(from_date)}to{str(to_date)}.xlsx',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new'
        }
