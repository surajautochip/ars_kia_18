# -*- coding: utf-8 -*-
{
    'name': "Status Dashboard",
    'summary': """Status Dashboard""",
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'ac_ars_cc_camera'],
    'data': [
        'security/ir.model.access.csv',
        'views/status_dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ac_ars_status_dashboard/static/src/xml/status_dashboard.xml',
            'ac_ars_status_dashboard/static/src/js/status_dashboard.js',
            'ac_ars_status_dashboard/static/src/css/dashboard_style.css',
        ],
    },
}