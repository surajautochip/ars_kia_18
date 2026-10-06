# -*- coding: utf-8 -*-
{
    'name': "Vehicle Tracking",

    'summary': """
        Odoo Module for automatic license plate recognition.""",

    'description': """
        Automatically Recognize License Plates from Videos and Images.
    """,

    'author': "Autochip India Pvt Ltd",
    'website': "https://www.autochip.in",
    'category': 'Tools',
    'version': '18.0',
    'depends': [
        'base', 'ac_ars_ip_camera', 'sale_stock', 'resource'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/alpr_vehicle_tracking_view.xml',
        'wizard/bay_status_slot_view.xml',
        'views/alpr_view.xml',
        'views/alpr_mail_conf.xml',
        'views/resource_category.xml',
        'views/tracking_dashbord.xml',
        'views/assets.xml',
        'views/res_config.xml',
        'views/alpr_online_server.xml',
        'report/report_vehicle_tracking_view.xml',
        'report/report_bay_status_slot_view.xml',
        'data/data.xml',
        'menus/menu.xml',
    ],
    'qweb': [
        'static/src/xml/alpr.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'ars_auto_lpr/static/src/scss/alpr.scss',
            'ars_auto_lpr/static/src/js/alpr_owl.js',
            'ars_auto_lpr/static/src/js/vehicle_tracking_dashboard.js',
            'ars_auto_lpr/static/src/xml/vehicle_tracking_dashboard.xml',
        ],
    },
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
