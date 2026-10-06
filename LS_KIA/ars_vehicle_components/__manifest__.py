# -*- coding: utf-8 -*-
{
    'name': "ARS Vehicle Components",
    'summary': """ """,
    'description': """ """,
    'author': "Autochip India",
    'website': "http://www.autochip.in",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','product'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}