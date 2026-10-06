# -*- coding: utf-8 -*-
from odoo import fields, models, api, tools, _
from datetime import datetime


class BayCountWizard(models.TransientModel):
    _name = 'bay.count.wizard'
    _description = "Bay Count Wizard"

    
    def get_bay_count_data(self, type):
        _logger.info("Executing get_bay_count_data...")
        data = {}
        datas = {}
        bay_list = []
        current_date = str(datetime.now().date())
        self_tz = self.with_context(tz='Asia/Kolkata')
        bays = self.env['alpr.bay.vehicle.log'].read_group([], fields=[], groupby=['bay_id'])
        slot_time = ['09 A.M - 10 A.M', '10 A.M - 11 A.M', '11 A.M - 12 P.M', '12 P.M - 01 P.M', '01 P.M - 02 P.M',
                     '02 P.M - 03 P.M',
                     '03 P.M - 04 P.M', '04 P.M - 05 P.M', '05 P.M - 06 P.M', '06 P.M - 07 P.M']
        for bay in bays:
            bay_list.append(bay.get('bay_id')[1])
            bay_logs = {}
            plate_list = []
            for log in self.env['alpr.bay.vehicle.log'].search(
                    [('entry_type', '=', 'in'), ('bay_id', '=', bay.get('bay_id')[0]),
                     ('log_date', '=', current_date)]):
                if log.vehicle_number not in plate_list:
                    plate_list.append(log.vehicle_number)

                if log.vehicle_number not in bay_logs:
                    bay_logs[log.vehicle_number] = log
                else:
                    bay_logs[log.vehicle_number] |= log

            bay_slot = {}
            c1 = c2 = c3 = c4 = c5 = c6 = c7 = c8 = c9 = c10 = 0
            for number in plate_list:
                for bay_log in bay_logs.get(number)[-1]:
                    create_date = fields.Datetime.context_timestamp(self_tz,
                                                                    fields.Datetime.from_string(bay_log.create_date))
                    if str(create_date)[11:16] >= '09:00' and str(create_date)[11:16] < '10:00':
                        c1 += 1
                    if str(create_date)[11:16] >= '10:00' and str(create_date)[11:16] < '11:00':
                        c2 += 1
                    if str(create_date)[11:16] >= '11:00' and str(create_date)[11:16] < '12:00':
                        c3 += 1
                    if str(create_date)[11:16] >= '12:00' and str(create_date)[11:16] < '13:00':
                        c4 += 1
                    if str(create_date)[11:16] >= '13:00' and str(create_date)[11:16] < '14:00':
                        c5 += 1
                    if str(create_date)[11:16] >= '14:00' and str(create_date)[11:16] < '15:00':
                        c6 += 1
                    if str(create_date)[11:16] >= '15:00' and str(create_date)[11:16] < '16:00':
                        c7 += 1
                    if str(create_date)[11:16] >= '16:00' and str(create_date)[11:16] < '17:00':
                        c8 += 1
                    if str(create_date)[11:16] >= '17:00' and str(create_date)[11:16] < '18:00':
                        c9 += 1
                    if str(create_date)[11:16] >= '18:00' and str(create_date)[11:16] < '19:00':
                        c10 += 1
            bay_slot.update({'09 A.M - 10 A.M': c1, '10 A.M - 11 A.M': c2, '11 A.M - 12 P.M': c3, '12 P.M - 01 P.M': c4,
                             '01 P.M - 02 P.M': c5,
                             '02 P.M - 03 P.M': c6, '03 P.M - 04 P.M': c7, '04 P.M - 05 P.M': c8, '05 P.M - 06 P.M': c9,
                             '06 P.M - 07 P.M': c10})
            datas.update({bay.get('bay_id')[1]: bay_slot})
        data.update({
            'bay_list': bay_list,
            'slot_time': slot_time,
            'bay_status': datas
        })
        if type == 'alpr_mail':
            result, format = self.env.ref('ars_auto_lpr.action_menu_bay_status').with_context(
                landscape=True).render_qweb_pdf(self.ids, data)
            return result
        return self.env.ref('ars_auto_lpr.action_menu_bay_status').with_context(landscape=True).report_action([],
                                                                                                              data=data,
                                                                                                              config=False)
