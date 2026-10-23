

{
    'name': "Custom Login Background",
    'version': '18.0.1.0',
    'summary': """This module assists in configuring a background image for the login page and hide other odoo elements""",
    'description': """Module helps to set background image in Login page.""",
    "author": "Metro Ict Limited",
    "website": "https://odoo.co.ke",
    "support": "support@odoo.co.ke",
    "license": "LGPL-3",
    'category': 'Tools',
    "price": 0.00,
    "currency": "USD",
    'depends': ['base', 'portal', 'web'],
    'data': [
        'views/res_company.xml',
        'views/web_login.xml',
    ],
    "images": [
        "static/description/banner.gif",
        "static/description/icon.png",
    ],
    'sequence': 1,
    "application": True,
    "installable": True
}
