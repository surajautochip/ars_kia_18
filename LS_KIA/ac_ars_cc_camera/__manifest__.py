# -*- coding: utf-8 -*-
{
    'name': "Live Streaming",
    'summary': """live streaming based on the Ip cameras
        """,
    'description': """
    """,
    'author': "Autochip India PVT LTD",
    'website': "http://www.autochip.in",
    'category': 'CC Camera',
    'version': '0.1',
    'depends': ['base', 'contacts', 'sale', 'resource', 'im_livechat', 'project',
                'ac_ars_ip_camera', 'mail', 'ac_ars_sms_api', 'board', 'calendar', 'fleet'],
    'data': [
        'security/camera_security.xml',
        'security/ir.model.access.csv',
        'data/fetchstream_data.xml',
        'data/server_status_mail.xml',
        'data/auto_token_expire.xml',
        'data/ac_ars_live_streaming_mail_template.xml',
        'data/status_mail_template.xml',
        'wizard/ac_ars_live_streaming_report.xml',
        'wizard/region_wise_report_view.xml',
        'wizard/dealer_wise_report_view.xml',
        'wizard/dealer_wise_details_report_view.xml',
        'wizard/hq_analysis_report_view.xml',
        'wizard/server_configuration.xml',
        'wizard/pause_reason.xml',

        'views/views.xml',
        'views/templates.xml',
        'views/ac_ars_live_streaming.xml',
        'views/dashbord.xml',
        'views/region.xml',
        'views/ac_ars_live_stream_token.xml',
        'views/ac_ars_allocation_data.xml',
        'views/live_stream_report.xml',
        'views/menu.xml',
        'views/planner_calendar_views.xml',

    ],
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ac_ars_cc_camera/static/src/components/bay_planner/bay_planner.scss',
            'ac_ars_cc_camera/static/src/components/bay_planner/bay_planner.js',
            'ac_ars_cc_camera/static/src/components/bay_planner/bay_planner.xml',
        ],
    },
}
