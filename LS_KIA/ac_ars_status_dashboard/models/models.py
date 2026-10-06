import locale
import datetime, calendar
from calendar import monthrange
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class StatusDashboard(models.Model):
    _inherit = 'ac.ars.live.streaming'

    # @api.model
    # def get_count(self,**kwargs):
    #     total_company = self.env['res.company'].search([])
    #     length_company = len(total_company)
    #     live_streaming = self.env['ac.ars.live.streaming'].read_group([], fields=['company_id'], groupby=['company_id'])
    #     lenth_streaming = len(live_streaming)
    #     return [lenth_streaming,length_company]

    @api.model
    def get_count(self, **kwargs):
        lst = []
        total_company = self.env['res.company'].sudo().search([])
        length_company = len(total_company)
        live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id.id')
        lenth_streaming = len(live_streaming)
        a, b, c = {}, {}, {}
        a = {'id': '1', 'name': 'Total Dealers', 'count': length_company}
        lst.append(a)
        b = {'id': '2', 'name': 'Live Streaming Dealers', 'count': lenth_streaming}
        lst.append(b)
        c = {'id': '3', 'name': 'Non-Live Streaming Dealers', 'count': length_company - lenth_streaming}
        lst.append(c)
        return lst

    @api.model
    def get_streaming_count(self, **kwargs):
        streaming_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id.id')
        return streaming_count

    @api.model
    def get_zone_count(self, **kwargs):
        zone_count = self.env['ac.ars.region.region'].sudo().search([])
        ls_report = self.env['ls.status.report'].sudo()
        lst = []
        if zone_count:
            for region in zone_count:
                # zone_company = self.env['res.company'].sudo().search([('region_id', '=', region.id)])
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.region_id.id == region.id)
                zone_datas = ls_report.search([('region_id', '=', region.id)])
                manager_ls = zone_datas.filtered(lambda x: x.ls_status == 'y').ids
                manager_nls = zone_datas.filtered(lambda x: x.ls_status == 'n').ids
                r_dict = {'zone_id': region.id, 'zone_name': region.name, 'total_dealer': len(zone_datas),
                          'ls_dealer': len(manager_ls), 'nls_dealer': len(manager_nls),
                          'success': "%.2f" % ((len(manager_ls) / len(zone_datas)) * 100) if zone_datas else 0}
                #                 r_dict = {'zone_id': region.id,'zone_name': region.name,'total_dealer': len(zone_company),'ls_dealer':len(live_streaming),'success':"%.2f" % ((len(live_streaming)/len(zone_company))*100) if zone_company else 0}

                lst.append(r_dict)

        return lst

    @api.model
    def get_manager_count(self, **kwargs):
        manager_count = self.env['ac.ars.region.region'].sudo().search([]).mapped('manager')
        ls_report = self.env['ls.status.report'].sudo()
        lst = []
        if manager_count:
            for manager in manager_count:
                # manager_company = self.env['res.company'].sudo().search([('region_id.manager', '=', manager.id)])
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.region_id.manager.id == manager.id)
                manager_datas = ls_report.search([('area_manager_id', '=', manager.partner_id.id)])
                manager_ls = manager_datas.filtered(lambda x: x.ls_status == 'y').ids
                manager_nls = manager_datas.filtered(lambda x: x.ls_status == 'n').ids
                r_dict = {'manager_id': manager.id, 'manager_name': manager.name, 'total_dealer': len(manager_datas),
                          'ls_dealer': len(manager_ls), 'nls_dealer': len(manager_nls),
                          'success': "%.2f" % ((len(manager_ls) / len(manager_datas)) * 100) if manager_datas else 0}
                lst.append(r_dict)
        return lst

    @api.model
    def get_area_count(self, **kwargs):
        ls_report = self.env['ls.status.report'].sudo()
        area_count = self.env['ac.ars.area.area'].sudo().search([])
        lst = []
        if area_count:
            for area in area_count:
                # area_company = self.env['res.company'].sudo().search([('area_id', '=', area.id)])
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.area_id.id == area.id)
                area_datas = ls_report.search([('area_id', '=', area.id)])
                area_ls = area_datas.filtered(lambda x: x.ls_status == 'y').ids
                area_nls = area_datas.filtered(lambda x: x.ls_status == 'n').ids
                r_dict = {'area_id': area.id, 'area_name': area.name, 'total_dealer': len(area_datas),
                          'ls_dealer': len(area_ls), 'nls_dealer': len(area_nls),
                          'success': "%.2f" % ((len(area_ls) / len(area_datas)) * 100) if area_datas else 0}
                # r_dict = {'area_id': area.id,'area_name': area.name,'total_dealer': len(area_company),'ls_dealer':len(live_streaming),'success':"%.2f" % ((len(live_streaming)/len(area_company))*100) if area_company else 0}

                lst.append(r_dict)

        return lst

    @api.model
    def get_state_count(self, **kwargs):
        ls_report = self.env['ls.status.report'].sudo()
        state_count = self.env['res.country.state'].sudo().search([('country_id.code', '=', 'IN')])
        lst = []
        if state_count:
            for state in state_count:
                # tot_company = self.env['res.company'].sudo().search([])
                # state_company = tot_company.filtered(lambda x: x.state_id.id == state.id).ids
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.state_id.id == state.id)
                state_datas = ls_report.search([('state_id', '=', state.id)])
                state_ls = state_datas.filtered(lambda x: x.ls_status == 'y').ids
                state_nls = state_datas.filtered(lambda x: x.ls_status == 'n').ids
                r_dict = {'state_id': state.id, 'state_name': state.name, 'total_dealer': len(state_datas),
                          'ls_dealer': len(state_ls), 'nls_dealer': len(state_nls),
                          'success': "%.2f" % (
                                  (len(state_ls) / len(state_datas)) * 100) if state_datas else 0}

                lst.append(r_dict)

        return lst

    @api.model
    def get_tpsm_count(self, **kwargs):
        ls_report = self.env['ls.status.report'].sudo()
        tpsm_count = self.env['ac.ars.territory.territory'].sudo().search([]).mapped('manager')
        lst = []
        if tpsm_count:
            for tpsm in tpsm_count:
                tpsm_datas = ls_report.search([('tpsm_id', '=', tpsm.partner_id.id)])
                tpsm_ls = tpsm_datas.filtered(lambda x: x.ls_status == 'y').ids
                tpsm_nls = tpsm_datas.filtered(lambda x: x.ls_status == 'n').ids
                r_dict = {'tpsm_id': tpsm.id, 'tpsm_name': tpsm.name, 'total_dealer': len(tpsm_datas),
                          'ls_dealer': len(tpsm_ls), 'nls_dealer': len(tpsm_nls),
                          'success': "%.2f" % (
                                  (len(tpsm_ls) / len(tpsm_datas)) * 100) if tpsm_datas else 0}
                lst.append(r_dict)
        return lst

    @api.model
    def get_zone_count_graph(self, **kwargs):
        ls_report = self.env['ls.status.report'].sudo()
        zone_count = self.env['ac.ars.region.region'].sudo().search([])
        graph_list = []
        # drill_down_data = []
        drill_down_list = []
        if zone_count:
            for region in zone_count:
                # zone_company = self.env['res.company'].sudo().search([('region_id', '=', region.id)])
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.region_id.id == region.id)
                zone_datas = ls_report.search([('region_id', '=', region.id)])
                zone_ls = zone_datas.filtered(lambda x: x.ls_status == 'y').ids
                zone_nls = zone_datas.filtered(lambda x: x.ls_status == 'n').ids
                graph_list.append(
                    {'name': region.name, 'y': (len(zone_ls) / len(zone_datas)) * 100 if zone_datas else 0,
                     'drilldown': region.name})
                drill_down_data = []
                drill_down_data.append(
                    ['Dealers', (len(zone_ls) / len(zone_datas)) * 100 if zone_datas else 0])
                drill_down_data.append(['Non_Dealers', (len(zone_nls) / len(zone_datas)) * 100 if zone_datas else 0])
                drill_down_list.append({'name': region.name, 'id': region.name, 'data': drill_down_data})

        # return [current_year,opportunities_data,opportunities_stage_data,filter_string]

        return [graph_list, drill_down_list]

    #         return graph_list

    @api.model
    def get_manager_count_graph(self, **kwargs):
        manager_count = self.env['ac.ars.region.region'].sudo().search([]).mapped('manager')
        ls_report = self.env['ls.status.report'].sudo()
        graph_list = []
        drill_down_list = []
        if manager_count:
            for manager in manager_count:
                # manager_company = self.env['res.company'].sudo().search([('region_id.manager', '=', manager.id)])
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.region_id.manager.id == manager.id)
                manager_datas = ls_report.search([('area_manager_id', '=', manager.partner_id.id)])
                manager_ls = manager_datas.filtered(lambda x: x.ls_status == 'y').ids
                manager_nls = manager_datas.filtered(lambda x: x.ls_status == 'n').ids
                graph_list.append({'name': manager.name,
                                   'y': (len(manager_ls) / len(manager_datas)) * 100 if manager_datas else 0,
                                   'drilldown': manager.name})
                drill_down_data = []
                drill_down_data.append(
                    ['Dealers', (len(manager_ls) / len(manager_datas)) * 100 if manager_datas else 0])
                drill_down_data.append(
                    ['Non_Dealers', (len(manager_nls) / len(manager_datas)) * 100 if manager_datas else 0])
                drill_down_list.append({'name': manager.name, 'id': manager.name, 'data': drill_down_data})

        return [graph_list, drill_down_list]

    #         return graph_list

    @api.model
    def get_area_count_graph(self, **kwargs):
        area_count = self.env['ac.ars.area.area'].sudo().search([])
        ls_report = self.env['ls.status.report'].sudo()
        graph_list = []
        drill_down_list = []
        if area_count:
            for area in area_count:
                # area_company = self.env['res.company'].sudo().search([('area_id', '=', area.id)])
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.area_id.id == area.id)
                area_datas = ls_report.search([('area_id', '=', area.id)])
                area_ls = area_datas.filtered(lambda x: x.ls_status == 'y').ids
                area_nls = area_datas.filtered(lambda x: x.ls_status == 'n').ids
                graph_list.append(
                    {'name': area.name, 'y': (len(area_ls) / len(area_datas)) * 100 if area_datas else 0,
                     'drilldown': area.name})
                drill_down_data = []
                drill_down_data.append(
                    ['Dealers', (len(area_ls) / len(area_datas)) * 100 if area_datas else 0])
                drill_down_data.append(['Non_Dealers', ((len(area_nls)) / len(
                    area_datas)) * 100 if area_datas else 0])
                drill_down_list.append({'name': area.name, 'id': area.name, 'data': drill_down_data})

        return [graph_list, drill_down_list]

    #         return graph_list

    @api.model
    def get_state_count_graph(self, **kwargs):
        state_count = self.env['res.country.state'].sudo().search([('country_id.code', '=', 'IN')])
        graph_list = []
        drill_down_list = []
        ls_report = self.env['ls.status.report'].sudo()
        if state_count:
            for state in state_count:
                # tot_company = self.env['res.company'].sudo().search([])
                # state_company = tot_company.filtered(lambda x: x.state_id.id == state.id)
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.state_id.id == state.id)
                state_datas = ls_report.search([('state_id', '=', state.id)])
                state_ls = state_datas.filtered(lambda x: x.ls_status == 'y').ids
                state_nls = state_datas.filtered(lambda x: x.ls_status == 'n').ids
                graph_list.append(
                    {'name': state.name, 'y': (len(state_ls) / len(state_datas)) * 100 if state_datas else 0,
                     'drilldown': state.name})
                drill_down_data = []
                drill_down_data.append(
                    ['Dealers', (len(state_ls) / len(state_datas)) * 100 if state_datas else 0])
                drill_down_data.append(['Non_Dealers', (len(state_nls) / len(
                    state_datas)) * 100 if state_datas else 0])
                drill_down_list.append({'name': state.name, 'id': state.name, 'data': drill_down_data})
        return [graph_list, drill_down_list]

    @api.model
    def get_company_count_graph(self, **kwargs):
        lst = []
        # total_company = self.env['res.company'].sudo().search([])
        # length_company = len(total_company)
        # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id.id')
        # lenth_streaming = len(live_streaming)
        ls_report = self.env['ls.status.report'].sudo()
        # ls_data = ls_report.read_group(domain=[], fields=['company_id', 'ls_status'], groupby=['ls_status'])
        ls_data = ls_report.read_group(domain=[], fields=['dealer_code', 'ls_status'], groupby=['ls_status'])
        ls_active = [x for x in ls_data if "y" in x['ls_status']]
        ls_not_active = [x for x in ls_data if "n" in x['ls_status']]
        
        active_count = int(ls_active[0]['ls_status_count']) if ls_active else 0
        not_active_count = int(ls_not_active[0]['ls_status_count']) if ls_not_active else 0
        
        total_dealers = active_count + not_active_count
        a = {'name': 'Total Dealers', 'y': total_dealers, 'drilldown': 'Total Dealers'}
        lst.append(a)
        
        b = {'name': 'LS Dealers', 'y': active_count, 'drilldown': 'LS Dealers'}
        lst.append(b)
        
        c = {'name': 'Non-LS Dealers', 'y': not_active_count, 'drilldown': 'Non-LS Dealers'}
        lst.append(c)
        return lst

    #         print(graph_list)
    #         return graph_list

    @api.model
    def get_tpsm_count_graph(self, **kwargs):
        tpsm_count = self.env['ac.ars.territory.territory'].sudo().search([]).mapped('manager')
        ls_report = self.env['ls.status.report'].sudo()
        graph_list = []
        drill_down_list = []
        if tpsm_count:
            for tpsm in tpsm_count:
                # manager_company = self.env['res.company'].sudo().search([('region_id.manager', '=', manager.id)])
                # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id').filtered(
                #     lambda x: x.region_id.manager.id == manager.id)
                tpsm_datas = ls_report.search([('tpsm_id', '=', tpsm.partner_id.id)])
                tpsm_ls = tpsm_datas.filtered(lambda x: x.ls_status == 'y').ids
                tpsm_nls = tpsm_datas.filtered(lambda x: x.ls_status == 'n').ids
                graph_list.append({'name': tpsm.name,
                                   'y': (len(tpsm_ls) / len(tpsm_datas)) * 100 if tpsm_datas else 0,
                                   'drilldown': tpsm.name})
                drill_down_data = []
                drill_down_data.append(
                    ['Dealers', (len(tpsm_ls) / len(tpsm_datas)) * 100 if tpsm_datas else 0])
                drill_down_data.append(
                    ['Non_Dealers', (len(tpsm_nls) / len(tpsm_datas)) * 100 if tpsm_datas else 0])
                drill_down_list.append({'name': tpsm.name, 'id': tpsm.name, 'data': drill_down_data})

        return [graph_list, drill_down_list]

    @api.model
    def show_total_zone(self, **kwargs):
        zone = kwargs.get('zone', False)
        total_company = self.env['res.company'].search([('region_id', '=', int(zone))])
        partner_id = total_company.mapped('partner_id').ids
        return partner_id

    @api.model
    def show_total_company(self, **kwargs):
        ls_report = self.env['ls.status.report'].sudo()
        id = kwargs.get('id', False)
        if int(id) == 1:  # Total Dealers
            # total_company = self.env['res.company'].search([]).ids
            company_ids = self.env.companies.ids
            partner_ids = ls_report.search([('company_id', 'in', company_ids)]).mapped('partner_id')
        elif int(id) == 2:
            # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id.id')
            # total_company = self.env['res.company'].search([('id', 'in', live_streaming)]).ids
            company_ids = self.env.companies.ids
            partner_ids = ls_report.search([('ls_status', '=', 'y'), ('company_id', 'in', company_ids)]).mapped('partner_id')
        else:
            # live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id.id')
            # total_company = self.env['res.company'].search([('id', 'not in', live_streaming)]).ids
            company_ids = self.env.companies.ids
            partner_ids = ls_report.search([('ls_status', '=', 'n'), ('company_id', 'in', company_ids)]).mapped('partner_id')
        return partner_ids.ids

    @api.model
    def show_total_area(self, **kwargs):
        area = kwargs.get('area', False)
        total_company = self.env['res.company'].search([('area_id', '=', int(area))])
        partner_id = total_company.mapped('partner_id').ids
        return partner_id

    @api.model
    def show_total_state(self, **kwargs):
        state = kwargs.get('state', False)
        total_company = self.env['res.company'].sudo().search([])
        fil_com = total_company.filtered(lambda x: x.state_id.id == int(state))
        fil_com = fil_com.mapped('partner_id').ids
        return fil_com

    @api.model
    def show_total_manager(self, **kwargs):
        manager = kwargs.get('manager', False)
        total_company = self.env['res.company'].sudo().search([])
        fil_com = total_company.filtered(lambda x: x.region_id.manager.id == int(manager))
        fil_com = fil_com.mapped('partner_id').ids
        return fil_com

    @api.model
    def show_total_tpsm(self, **kwargs):
        tpsm = kwargs.get('tpsm', False)
        total_company = self.env['res.company'].sudo().search([])
        fil_com = total_company.filtered(lambda x: x.tpsm_id.manager.id == int(tpsm))
        fil_com = fil_com.mapped('partner_id').ids
        return fil_com

    @api.model
    def show_total_streaming_zone(self, **kwargs):
        zone = kwargs.get('zone', False)
        c_td = kwargs.get('c_td', False)
        if int(c_td) == 3:
            streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            total_company = streaming_company_count.filtered(lambda x: x.region_id.id == int(zone))
        else:
            company = self.env['res.company'].sudo().search([('region_id.id', '=', zone)])
            streaming_company = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            streaming_company_count = streaming_company.filtered(lambda x: x.region_id.id == int(zone)).ids
            total_company = company.filtered(lambda x: x.id not in streaming_company_count)

        #         streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
        #         total_company = streaming_company_count.filtered(lambda x:x.region_id.id == int(zone)).ids
        partner_id = total_company.mapped('partner_id').ids
        return partner_id

    @api.model
    def show_total_streaming_area(self, **kwargs):
        area = kwargs.get('area', False)
        a_td = kwargs.get('a_td', False)
        if int(a_td) == 3:
            streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            total_company = streaming_company_count.filtered(lambda x: x.area_id.id == int(area))
        else:
            company = self.env['res.company'].sudo().search([('area_id.id', '=', area)])
            streaming_company = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            streaming_company_count = streaming_company.filtered(lambda x: x.area_id.id == int(area)).ids
            total_company = company.filtered(lambda x: x.id not in streaming_company_count)

        #         streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
        #         total_company = streaming_company_count.filtered(lambda x:x.area_id.id == int(area)).ids
        partner_id = total_company.mapped('partner_id').ids
        return partner_id

    @api.model
    def show_total_streaming_state(self, **kwargs):
        state = kwargs.get('state', False)
        s_td = kwargs.get('s_td', False)
        if int(s_td) == 3:
            streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            total_company = streaming_company_count.filtered(lambda x: x.state_id.id == int(state))
        else:
            all_company = self.env['res.company'].sudo().search([])
            company = all_company.filtered(lambda x: x.state_id.id == int(state))
            streaming_company = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            streaming_company_count = streaming_company.filtered(lambda x: x.state_id.id == int(state)).ids
            total_company = company.filtered(lambda x: x.id not in streaming_company_count)
        #         streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
        #         total_company = streaming_company_count.filtered(lambda x:x.state_id.id == int(state)).ids
        partner_id = total_company.mapped('partner_id').ids
        return partner_id

    @api.model
    def show_total_streaming_manager(self, **kwargs):
        manager = kwargs.get('manager', False)
        m_td = kwargs.get('m_td', False)
        if int(m_td) == 3:
            streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            total_company = streaming_company_count.filtered(lambda x: x.region_id.manager.id == int(manager))

        else:
            company = self.env['res.company'].sudo().search([('region_id.manager.id', '=', manager)])
            streaming_company = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            streaming_company_count = streaming_company.filtered(lambda x: x.region_id.manager.id == int(manager)).ids
            total_company = company.filtered(lambda x: x.id not in streaming_company_count)

        partner_id = total_company.mapped('partner_id')
        #         streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
        #         total_company = streaming_company_count.filtered(lambda x:x.region_id.manager.id == int(manager)).ids
        return partner_id.ids

    @api.model
    def show_total_streaming_tpsm(self, **kwargs):
        tpsm = kwargs.get('tpsm', False)
        tpsm_td = kwargs.get('tpsm_td', False)
        if int(tpsm_td) == 3:
            streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            total_company = streaming_company_count.filtered(lambda x: x.tpsm_id.manager.id == int(tpsm))
        else:
            all_company = self.env['res.company'].sudo().search([])
            company = all_company.filtered(lambda x: x.tpsm_id.manager.id == int(tpsm))
            streaming_company = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
            streaming_company_count = streaming_company.filtered(lambda x: x.tpsm_id.manager.id == int(tpsm)).ids
            total_company = company.filtered(lambda x: x.id not in streaming_company_count)
        #         streaming_company_count = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id')
        #         total_company = streaming_company_count.filtered(lambda x:x.state_id.id == int(state)).ids
        partner_id = total_company.mapped('partner_id').ids
        return partner_id
