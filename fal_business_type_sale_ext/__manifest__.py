# -*- coding: utf-8 -*-
{
    'name': 'Sale Business Type',
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'sequence': 20,
    'summary': 'Add business type object in sales',
    'category': 'Sale',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description':
    '''
        Sale Business Type
        ====================

        Add business type in sales to manage multiple sequence
    ''',
    'depends': [
        'sale_management',
        'fal_business_type_invoice_ext',
    ],
    'data': [
        'security/sale_business_security.xml',
        'views/business_type_views.xml',
        'views/sale_views.xml',
    ],
    'images': [
        'static/description/sale_business_type_screenshot.png'
    ],
    'demo': [
    ],
    'price': 270.00,
    'currency': 'EUR',
    'application': False,
}
