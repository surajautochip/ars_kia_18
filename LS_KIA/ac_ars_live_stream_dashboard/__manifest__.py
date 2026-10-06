# -*- coding: utf-8 -*-
{
    'name': "Live streaming Dashboard",
    'summary': """Dashboard for Live streaming """,
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'custom',
    'version': '0.1',
    'depends': ['base','ac_ars_cc_camera'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ac_ars_live_stream_dashboard/static/src/xml/LiveStreamDashboard.xml',
            'ac_ars_live_stream_dashboard/static/src/js/dashboard_live_stream.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}