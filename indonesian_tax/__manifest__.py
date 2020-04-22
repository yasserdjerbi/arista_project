# -*- coding: utf-8 -*-
{
    'name': 'Indonesian Tax',
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'summary': "Add capability to generate Indonesian tax invoices",
    'category': 'Localization',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': '''
        This module has features:
        ==========================

        1. Add capability for storing NPWP
        2. Faktur Pajak
    ''',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/faktur_pajak.xml',
        'views/invoice_inherit_view.xml',
        'views/partner_views.xml',
        'wizard/generate_faktur_view.xml',
        'report/efaktur_invoice_view.xml',
    ],
    'images': [
        # 'static/description/indonesian_tax_screenshot.png'
    ],
    'demo': [
    ],
    'price': 180.00,
    'currency': 'EUR',
    'application': False,
}
