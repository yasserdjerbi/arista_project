{
    "name": "Fleet By Serial Number",
    "version": "13.0.2.0.0",
    'license': 'OPL-1',
    'summary': 'Module to add lot number selection on Fleet.',
    'category': 'Fleet',
    'author': 'CLuedoo',
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    "description": """
Module to add lot number selection on Fleet.
=============================================

In Odoo you can't select which serial number of product you wanted to relate on Fleet. This module will enable it.
    """,
    "depends": [
        'fleet',
        'fal_accounting_lot_dimension',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 180.00,
    'currency': 'EUR',
    'application': False,
}
