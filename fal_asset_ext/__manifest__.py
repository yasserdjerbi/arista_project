# -*- coding: utf-8 -*-
{
    "name": "Account Asset Extension",
    "version": "13.1.1.0.0",
    'license': 'OPL-1',
    'sequence': 33,
    'summary': 'Extends Asset functionality to match falinwa expectation (Enterprise)',
    'category': 'Accounting & Finance',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    "description": """
    Module to improve Account Asset module.
    """,
    "depends": ['account_asset'],
    'data': [
        'views/account_asset_view.xml',
        'wizard/fal_multi_confirm_asset_wizard_view.xml',
        'data/data.xml'
    ],
    'images': [
        'static/description/fal_asset_ext_screenshot.png'
    ],
    'css': [],
    'js': [
    ],
    'installable': True,
    'active': False,
    'application': False,
    'price': 270.00,
    'currency': 'EUR',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
