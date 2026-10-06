from odoo import models, fields, api
from itertools import groupby
from operator import itemgetter


class ls_status_report(models.Model):
    _name = 'ls.status.report'

    dealer_code = fields.Char()
    dealer_name = fields.Many2one('res.company')
    partner_id = fields.Many2one('res.partner')
    ls_status = fields.Selection([('y', 'Yes'), ('n', 'No')])
    region_id = fields.Many2one('ac.ars.region.region')
    zone_id = fields.Many2one('ac.ars.zone.zone')
    area_id = fields.Many2one('ac.ars.area.area')
    state_id = fields.Many2one('res.country.state')
    area_manager_id = fields.Many2one('res.partner', 'Area Manager')
    tpsm_id = fields.Many2one('res.partner', 'TPSM')

    def update_live_streaming_status_report(self):
        print("jvfjbfobnfoibnfib")


class LiveStreamToken(models.Model):
    _inherit = 'ac.ars.live.stream.token'

    def cron_live_streaming_status_report(self):
        ls_report = self.env['ls.status.report'].sudo()
        company_id = self.env['res.company'].sudo()
        live_streaming = self.env['ac.ars.live.streaming'].sudo().search([]).mapped('company_id.id')
        ls_report.search([]).unlink()
        for company in company_id.search([]):
            ls_status = 'y' if company.id in list(set(live_streaming)) else 'n'
            vals = {'dealer_code': company.dealer_code,
                    'dealer_name': company.id,
                    'partner_id': company.partner_id.id,
                    'ls_status': ls_status,
                    'region_id': company.region_id.id,
                    'zone_id': company.zone_id.id if company.zone_id else False,
                    'area_id': company.area_id.id if company.area_id else False,
                    'state_id': company.state_id.id if company.state_id else False,
                    'area_manager_id': company.region_id.manager.partner_id.id if company.region_id and company.region_id.manager else False,
                    'tpsm_id': company.tpsm_id.manager.partner_id.id if company.tpsm_id and company.tpsm_id.manager else False
                    }
            company.write({'is_status_config_done': True})
            res = ls_report.create(vals)
            print(res)


class LiveStreamTokenInherit(models.Model):
    _inherit = 'ac.ars.live.streaming'

    @api.model
    def get_count(self, **kwargs):
        lst = []
        ls_report = self.env['ls.status.report'].sudo()
        ls_data = ls_report.read_group(domain=[], fields=['dealer_code', 'ls_status'], groupby=['ls_status'])
        ls_active = [x for x in ls_data if "y" in x['ls_status']]
        ls_not_active = [x for x in ls_data if "n" in x['ls_status']]
        
        active_count = int(ls_active[0]['ls_status_count']) if ls_active else 0
        not_active_count = int(ls_not_active[0]['ls_status_count']) if ls_not_active else 0
        total_dealers = active_count + not_active_count
        
        a = {'id': '1', 'name': 'Total Dealers',
             'count': total_dealers}
        lst.append(a)
        b = {'id': '2', 'name': 'Live Streaming Dealers', 'count': active_count}
        lst.append(b)
        c = {'id': '3', 'name': 'Non-Live Streaming Dealers', 'count': not_active_count}
        lst.append(c)
        return lst

    # @api.model
    # def get_zone_count(self, **kwargs):
    #     zone_count = self.env['ac.ars.region.region'].sudo().search([])
    #     ls_report = self.env['ls.status.report'].sudo()
    #     lst = []
    #     if zone_count:
    #         zone_dict = {}
    #         for region in zone_count:
    #             zone_datas = ls_report.search([('region_id', '=', region.id)])
    #             zone_ls = zone_datas.filtered(lambda x: x.ls_status == 'y').ids
    #             zone_nls = zone_datas.filtered(lambda x: x.ls_status == 'n').ids
    #             r_dict = {'zone_id': region.id, 'zone_name': region.name, 'total_dealer': len(zone_count),
    #                       'ls_dealer': len(zone_ls), 'nls_dealer': len(zone_nls),
    #                       'success': "%.2f" % ((len(zone_ls) / len(zone_datas)) * 100) if zone_datas else 0}
    #             lst.append(r_dict)
    #             print(r_dict)
    #         return lst


