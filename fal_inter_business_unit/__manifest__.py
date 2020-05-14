# -*- coding: utf-8 -*-
{
    'name': 'Inter Business Unit',
    'version': '13.2.1.0.0',
    'license': 'OPL-1',
    'summary': 'Add Inter business unit',
    'category': 'Productivity',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description':
    '''
        Inter Business Unit
    ''',
    'depends': [
        'purchase_stock',
        'sale_stock',
        'fal_business_type_sale_ext',
        'fal_business_type_purchase_ext',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/business_type_view.xml',
        'views/res_partner.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 0.00,
    'currency': 'EUR',
    'application': False,
}
