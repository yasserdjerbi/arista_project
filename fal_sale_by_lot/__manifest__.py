{
    "name": "Sale By Serial Number",
    "version": "13.0.2.0.0",
    'license': 'OPL-1',
    'summary': 'Module to add lot number selection on Sale.',
    'category': 'Sale',
    'author': 'CLuedoo',
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    "description": """
Module to add lot number selection on Sale.
=============================================

In Odoo you can't select which serial number of product you wanted to sell on sales order. This module will enable it.
    """,
    "depends": [
        'sale_stock',
        'fal_accounting_lot_dimension',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 180.00,
    'currency': 'EUR',
    'application': False,
    'auto_install': True,
}
