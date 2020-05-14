# -*- coding: utf-8 -*-
{
    'name': 'Purchase Business Type',
    'version': '13.2.1.0.0',
    'license': 'OPL-1',
    'summary': 'Add business type object in purchase',
    'category': 'Purchase',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description':
    '''
        Purchase Business Type
        ====================

        Add business type in purchase to manage multiple sequence
    ''',
    'depends': [
        'purchase',
        'fal_business_type_invoice_ext',
    ],
    'data': [
        'security/purchase_business_security.xml',
        'views/business_type_views.xml',
        'views/purchase_views.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 0.00,
    'currency': 'EUR',
    'application': False,
}
