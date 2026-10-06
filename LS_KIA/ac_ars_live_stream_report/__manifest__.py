# -*- coding: utf-8 -*-
{
    'name': "Live Stream Report",
    'summary': """Live Streaming Report""",
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'ac_ars_cc_camera'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/live_streaming_report.xml',
        'wizard/ls_status_report.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
