# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_account_discount_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Discount Account",
        help="This account will be used when there is a discount for customer invoice.")
    property_stock_account_transit_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Transit Account",
        help="This account will be used when there is a transfer.")
    property_stock_account_output_input_main_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Output Input to Main Account",
        help="This account will be used when there is a transfer between main - branch.")
    property_stock_account_output_input_branch_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Output Input to Branch Account",
        help="This account will be used when there is a transfer between branch - branch.")
