# -*- coding: utf-8 -*-
{
    'name': "HY-GDMS&LS INTEGRATION",
    'summary': """HY-GDMS&LS INTEGRATION""",
    'description': """Single Sign In and direct vehicle allocation from GDMS""",
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','portal','web','website',
                'calendar','contacts','hr','survey','mail','im_livechat'
                ,'ac_ars_cc_camera','ac_ars_live_stream_dashboard'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/base_hide_menu_groups.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'views/live_stream_token.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}