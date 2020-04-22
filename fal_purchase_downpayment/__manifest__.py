# -*- coding: utf-8 -*-
{
    'name': 'Downpayment Purchase',
    'version': '12.1.0.0.0',
    'author': 'Falinwa Limited',
    'website': 'https://falinwa.com',
    'category': 'Purchases',
    'summary': 'Purchase DownPayment',
    'description':
    '''
        This module contain some functions:\n
        1. add downpayment on purchase\n
    ''',
    'depends': [
        'purchase_stock',
        'fal_purchase_discount'
    ],
    'data': [
        'views/res_config_views.xml',
        'views/purchase.xml',
        'wizard/purchase_make_invoice_advance_views.xml',
    ],
    'css': [],
    'js': [],
    'installable': True,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
