# -*- coding: utf-8 -*-
{
    'name': 'Invoice Business Type',
    'version': '13.2.1.0.0',
    'license': 'OPL-1',
    'summary': 'Add business type object in Invoice',
    'category': 'Invoicing Management',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description':
    '''
        Invoice Business Type
        ====================

        Add business type in Invoice to manage multiple sequence
    ''',
    'depends': [
        'account',
        'fal_business_type',
    ],
    'data': [
        'security/move_business_security.xml',
        'views/business_type_views.xml',
        'views/invoice_views.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 0.00,
    'currency': 'EUR',
    'application': False,
}
