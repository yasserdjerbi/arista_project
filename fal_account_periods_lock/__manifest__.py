# -*- coding: utf-8 -*-
{
    'name': "Account Periods Lock",
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'summary': "Resurface Fiscal Year.",
    'sequence': 20,
    'category': 'Accounting & Finance',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': """
        Resurface Fiscal Year function of odoo 9.
        ============================================
        Odoo have a better fiscal year management and lock on Odoo9.
        Here CLuedoo try to revive it.
    """,
    'depends': ['account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/fal_account_periods_lock_view.xml',
    ],
    'images': [
        'static/description/1_screenshot.png'
    ],
    'demo': [
        'data/fal_account_periods_lock_demo.xml'
    ],
    'price': 450.00,
    'currency': 'EUR',
    'application': False,
}