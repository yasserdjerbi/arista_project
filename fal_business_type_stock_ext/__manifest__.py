# -*- coding: utf-8 -*-
{
    'name': 'Stock Multi-channels',
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Add business type object in stock',
    'category': 'Inventory',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description':
    '''
        Stock Business Type
        ===================

        Add business type in stock to manage multiple sequence
    ''',
    'depends': [
        'stock',
        'fal_business_type_invoice_ext',
    ],
    'data': [
        'security/stock_business_security.xml',
        'views/stock_location_views.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_picking_views.xml',
    ],
    'images': [
        'static/description/crm_business_type_screenshot.png'
    ],
    'demo': [
    ],
    'price': 270.00,
    'currency': 'EUR',
    'application': False,
}
