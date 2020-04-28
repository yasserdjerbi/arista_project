# -*- coding: utf-8 -*-
# © 2004-2009 Tiny SPRL (<http://tiny.be>).
# © 2014-2017 Tecnativa - Pedro M. Baeza
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "Purchase order lines with discounts",
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    "summary": "add constraint only put discount from 0% to less than 100%, and fix wrong price on stock",
    "category": "Purchases",
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    "depends": ["purchase_discount"],
    "data": [
    ],
    'images': [
        'static/description/fal_purchase_additional_info_screenshot.png'
    ],
    'installable': True,
    'price': 270.00,
    'currency': 'EUR',
}
