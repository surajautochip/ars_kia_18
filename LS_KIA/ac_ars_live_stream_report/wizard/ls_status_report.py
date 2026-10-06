import io
import base64
from collections import defaultdict
import xlsxwriter
from odoo import models, fields, api, _
from datetime import date, datetime, timedelta, time
from odoo.exceptions import UserError, ValidationError

class LiveStreamStatusReport(models.TransientModel):
    _name = "ls.utilization.report"

    company_id = fields.Many2one('res.company', 'Dealer Name', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    expected_ls_per_day = fields.Integer(default=3)
    expected_working_days = fields.Integer()
    expected_ls_link = fields.Integer()
    from_date = fields.Date("Start Date")
    to_date = fields.Date("End Date")
    dealers_list = fields.Boolean()
    ls_dealers_list = fields.Boolean(default=True)
    region_wise_list = fields.Boolean()
    zone_wise_list = fields.Boolean()

    @api.onchange('from_date', 'to_date')
    def get_working_days(self):
        if self.from_date and self.to_date:
            if self.from_date < self.to_date:
                days = (self.to_date - self.from_date).days + 1
                working_days = sum(1 for i in range(days) if (self.from_date + timedelta(days=i)).weekday() != 6)
                self.expected_working_days = working_days
                self.expected_ls_link = working_days * self.expected_ls_per_day
            else:
                raise ValidationError(f"Start date '{self.from_date}' should be greater than End date '{self.to_date}'")

    def bay_planner_cam_details(self, company):
        bay_planner = self.env['planner.calender'].search([('resource_category.code', '=', 'BAY'),
                                                           ('company_id', '=', company.id)])
        cam_data = []
        bay_data = set()
        for bay in bay_planner.member_ids:
            bay_data.add(bay.name)
            cam_data.extend(bay.ip_address.mapped('name'))
        return {'bay_data': len(bay_data), 'cam_data': len(cam_data)}

    def get_dealer_wise_report(self, ls_report_data):
        res = []
        for d in ls_report_data:
            d['LS_View_Percentage'] = round((d['View_Count'] / d['Total_LS_Count']) * 100, 2) if d['Total_LS_Count'] else 0
            den = (self.expected_ls_link * d['no_of_bays'])
            d['Utilization'] = round((d['Total_LS_Count'] / den) * 100, 2) if den else 0
            res.append(d)
        return res

    def get_dealer_data(self):
        dealers_list = []
        dealer_list = self.env['ls.status.report'].search([])
        for dlr in dealer_list:
            dealers_list.append({
                'dealer_name': dlr.dealer_name.name,
                'Ls_status': dlr.ls_status,
                'Region': dlr.region_id.name,
                'Zone': dlr.zone_id.name,
                'Area': dlr.area_id.name,
                'State': dlr.state_id.name,
                'Area_Manager': dlr.area_manager_id.name,
                'TPSM': dlr.tpsm_id.name
            })
        return dealers_list

    def _group_by_key(self, report_data, dealers_data, group_key, all_keys):
        # group dealers by group_key
        dealer_group = defaultdict(lambda: {'Total_Workshop': 0, 'LS_Active_Workshop': 0, 'LS_INActive_Workshop': 0})
        for d in dealers_data:
            k = d.get(group_key)
            if not k: continue
            dealer_group[k]['Total_Workshop'] += 1
            if d.get('Ls_status') == 'y':
                dealer_group[k]['LS_Active_Workshop'] += 1
            elif d.get('Ls_status') == 'n':
                dealer_group[k]['LS_INActive_Workshop'] += 1

        # group report_data by group_key
        report_group = defaultdict(lambda: {
            'Live_Streaming_Workshop': 0, 'Total_BAY': 0, 'Total_CAM': 0, 'SUM_Total_Link': 0,
            'SUM_Total_SMS_Sent': 0, 'SUM_Total_Email_Sent': 0, 'SUM_CVL': 0, 'SUM_CNVL': 0
        })
        for r in report_data:
            k = r.get(group_key)
            if not k: continue
            report_group[k]['Live_Streaming_Workshop'] += 1
            report_group[k]['Total_BAY'] += r.get('no_of_bays', 0)
            report_group[k]['Total_CAM'] += r.get('no_of_cam', 0)
            report_group[k]['SUM_Total_Link'] += r.get('Total_LS_Count', 0)
            report_group[k]['SUM_Total_SMS_Sent'] += r.get('Total_SMS_Link_Send', 0)
            report_group[k]['SUM_Total_Email_Sent'] += r.get('Total_Email_Link_Send', 0)
            report_group[k]['SUM_CVL'] += r.get('View_Count', 0)
            report_group[k]['SUM_CNVL'] += r.get('Not_View_Count', 0)

        res = []
        for k in all_keys:
            d_grp = dealer_group.get(k, {'Total_Workshop': 0, 'LS_Active_Workshop': 0, 'LS_INActive_Workshop': 0})
            r_grp = report_group.get(k, {
                'Live_Streaming_Workshop': 0, 'Total_BAY': 0, 'Total_CAM': 0, 'SUM_Total_Link': 0,
                'SUM_Total_SMS_Sent': 0, 'SUM_Total_Email_Sent': 0, 'SUM_CVL': 0, 'SUM_CNVL': 0
            })
            
            ls_perc = round((d_grp['LS_Active_Workshop'] / d_grp['Total_Workshop'] * 100), 2) if d_grp['Total_Workshop'] else 0
            cv_perc = round((r_grp['SUM_CVL'] / r_grp['SUM_Total_Link'] * 100), 2) if r_grp['SUM_Total_Link'] else 0
            target_sms = self.expected_ls_link * r_grp['Total_BAY']
            util_perc = round((r_grp['SUM_Total_SMS_Sent'] / target_sms * 100), 2) if target_sms else 0
            
            row = {
                group_key: k,
                'Total_Workshop': d_grp['Total_Workshop'],
                'LS_Active_Workshop': d_grp['LS_Active_Workshop'],
                'LS_INActive_Workshop': d_grp['LS_INActive_Workshop'],
                'LS_Percentage': ls_perc,
                'Live_Streaming_Workshop': r_grp['Live_Streaming_Workshop'],
                'Total_BAY': r_grp['Total_BAY'],
                'Total_CAM': r_grp['Total_CAM'],
                'SUM_Total_Link': r_grp['SUM_Total_Link'],
                'SUM_Total_SMS_Sent': r_grp['SUM_Total_SMS_Sent'],
                'SUM_Total_Email_Sent': r_grp['SUM_Total_Email_Sent'],
                'SUM_CVL': r_grp['SUM_CVL'],
                'SUM_CNVL': r_grp['SUM_CNVL'],
                'Customer_Viewed_Percentage': cv_perc,
                'Target_SMS_Link': target_sms,
                'Utilization_Percentage': util_perc
            }
            res.append(row)
        return res

    def get_region_wise_report(self, ls_report_data, dealer_list):
        regions = [r.name for r in self.env['region.region'].sudo().search([])]
        return self._group_by_key(ls_report_data, dealer_list, 'Region', regions)

    def get_zone_wise_report(self, ls_report_data, dealer_list):
        zones = [z.name for z in self.env['zone.zone'].sudo().search([])]
        return self._group_by_key(ls_report_data, dealer_list, 'Zone', zones)

    def get_status_report_data(self):
        live_streaming_dealers = self.env['live.streaming'].sudo().search([]).mapped('company_id')
        dealer_list = []
        for dealer in live_streaming_dealers.filtered(lambda x: x.active == True):
            bay_cam_dat = self.bay_planner_cam_details(dealer)
            dealer_list.append({
                'dealer_name': dealer.name,
                'dealer_code': dealer.dealer_code,
                'Region': dealer.region_id.name,
                'Zone': dealer.zone_id.name,
                'TPSM': dealer.tpsm_id.name,
                'no_of_bays': bay_cam_dat['bay_data'],
                'no_of_cam': bay_cam_dat['cam_data'],
                'Total_LS_Count': 0, 'View_Count': 0, 'Not_View_Count': 0,
                'Total_SMS_Link_Send': 0, 'Total_Email_Link_Send': 0
            })
            
        dealer_dict = {d['dealer_name']: d for d in dealer_list}

        if self.from_date and self.to_date:
            domain = [('date', '>=', self.from_date), ('date', '<=', self.to_date)]
            ls_data = self.env['live.streaming'].sudo().search(domain)
            for data in ls_data:
                name = data.company_id.name
                if name in dealer_dict:
                    dealer_dict[name]['Total_LS_Count'] += 1
                    if data.is_viewing:
                        dealer_dict[name]['View_Count'] += 1
                    else:
                        dealer_dict[name]['Not_View_Count'] += 1
                    if data.sms_status in ('sent', 'received'):
                        dealer_dict[name]['Total_SMS_Link_Send'] += 1
                    if data.mail_status in ('sent', 'received'):
                        dealer_dict[name]['Total_Email_Link_Send'] += 1
            
            ls_report_data = list(dealer_dict.values())
            for d in ls_report_data:
                d['Target_SMS_Link'] = self.expected_ls_link * d['no_of_bays']

            report_dict = {}
            dealer_list_df = self.sudo().get_dealer_data()
            if self.dealers_list:
                report_dict['dealer_list'] = dealer_list_df
            if self.ls_dealers_list:
                report_dict['dealer_wise_report'] = self.sudo().get_dealer_wise_report(ls_report_data)
            if self.region_wise_list:
                report_dict['region_wise_report'] = self.sudo().get_region_wise_report(ls_report_data, dealer_list_df)
            if self.zone_wise_list:
                report_dict['zone_ls_report_df'] = self.sudo().get_zone_wise_report(ls_report_data, dealer_list_df)
            return report_dict

    def print_xls_report(self):
        data_frame = self.get_status_report_data()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        bold = workbook.add_format({'bold': True})

        def write_sheet(name, dict_list):
            if not dict_list: return
            ws = workbook.add_worksheet(name)
            headers = list(dict_list[0].keys())
            for i, h in enumerate(headers):
                ws.write(0, i, h, bold)
            for row_idx, row_dict in enumerate(dict_list, 1):
                for col_idx, h in enumerate(headers):
                    val = row_dict.get(h, '')
                    if val is None: val = ''
                    ws.write(row_idx, col_idx, val)

        if 'dealer_list' in data_frame:
            write_sheet('Dealer List', data_frame['dealer_list'])
        if 'dealer_wise_report' in data_frame:
            write_sheet('WorkShop', data_frame['dealer_wise_report'])
        if 'region_wise_report' in data_frame:
            write_sheet('Region', data_frame['region_wise_report'])
        if 'zone_ls_report_df' in data_frame:
            write_sheet('Zone', data_frame['zone_ls_report_df'])

        workbook.close()
        output.seek(0)
        data = base64.encodebytes(output.read())
        
        doc_id = self.env['ir.attachment'].create({
            'datas': data, 
            'name': f'LS_Report_{str(self.from_date)}to{str(self.to_date)}.xlsx',
            'res_model': self._name,
            'res_id': self.id
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{doc_id.id}?download=true',
            'target': 'current',
        }
