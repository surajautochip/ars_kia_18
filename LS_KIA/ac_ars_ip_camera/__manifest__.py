# -*- coding: utf-8 -*-
{
    'name': "ARS IP Camera (Modular)",

    'summary': """ IP Camera Details & Configuration for ARS Ecosystem """,

    'description': """
        Standalone module managing IP Cameras and configurations.
        Uses ac_ars modular ecosystem standards.
    """,

    'author': "Autochip India Pvt Ltd",
    'website': "http://www.autochip.in",

    'category': 'Operations',
    'version': '18.0.1.0',

    'depends': ['base', 'mail'],

    'data': [
        'security/ip_cam_security.xml',
        'security/ir.model.access.csv',
        'data/cam_exp_info_email.xml',
        'wizard/get_video.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/camera_records.xml',
        'views/menu.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'ac_ars_ip_camera/static/src/js/booking_stage_mask.js',
            'ac_ars_ip_camera/static/src/css/ars_password.css',
            'ac_ars_ip_camera/static/src/xml/booking_stage_mask.xml',
            'ac_ars_ip_camera/static/src/components/live_streaming/live_streaming.js',
            'ac_ars_ip_camera/static/src/components/live_streaming/live.xml',
            'ac_ars_ip_camera/static/src/components/live_streaming/live.css',
        ],
    },

    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
}
