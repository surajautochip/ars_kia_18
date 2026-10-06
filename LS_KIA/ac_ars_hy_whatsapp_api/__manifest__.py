# -*- coding: utf-8 -*-
{
    'name': "WebX HY-AutoEver Whatsapp API",
    'summary': """WebX HY-AutoEver Whatsapp API""",
    'description': """Send Whatsapp to Customer """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'ac_ars_cc_camera'],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_log.xml',
        'views/whatsapp_config.xml',
        'views/whatsapp_api_menu.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
