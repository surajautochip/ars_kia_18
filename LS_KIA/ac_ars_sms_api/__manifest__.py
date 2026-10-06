# -*- coding: utf-8 -*-
{
    'name': "SMS Integration",

    'summary': """Sent a SMS using API Integration""",

    'description': """
        SMS Integration
    """,

    'author': "Autochip India Pvt Ltd",
    'website': "http://www.autochipindia.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/live_streaming_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
