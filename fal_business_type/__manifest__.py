# -*- coding: utf-8 -*-
{
    'name': 'Business Type',
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Add business type object',
    'category': 'Base',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description':
    '''
        Business Type
        =========================

        Business type Engine.
    ''',
    'depends': [
        'web_enterprise',
    ],
    'data': [
        'data/business_type_data.xml',
        'security/business_unit_security.xml',
        'security/ir.model.access.csv',
        'views/ir_property_view.xml',
        'views/web_client_template.xml',
        'views/res_partner_views.xml',
        'views/business_type_views.xml',
        'views/res_users_views.xml',
        'wizard/create_menu_wizard.xml',
    ],
    'demo': [
        'demo/res_users_demo.xml',
    ],
    'qweb': [
        "static/src/xml/base.xml",
    ],
    'images': [
        'static/description/business_type_screenshot.png'
    ],
    'demo': [
    ],
    'price': 270.00,
    'currency': 'EUR',
    'application': False,
}
