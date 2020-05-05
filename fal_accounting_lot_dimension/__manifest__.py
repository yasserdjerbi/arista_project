{
    "name": "Lot Dimension in Accounting",
    "version": "13.0.2.0.0",
    'license': 'OPL-1',
    'summary': 'Module to add lot number dimension on accounting.',
    'category': 'Accounting',
    'author': 'CLuedoo',
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    "description": """
Module to add lot number dimension on accounting.
=============================================

In Odoo there is no LOT on Accounting Dimension, this module enable it.
    """,
    "depends": [
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 180.00,
    'currency': 'EUR',
    'application': False,
}
