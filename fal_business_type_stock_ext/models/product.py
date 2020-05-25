# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _svl_empty_stock_am(self, stock_valuation_layers):
        move_vals_list = super(ProductProduct, self)._svl_empty_stock_am(stock_valuation_layers)
        for move_val in move_vals_list:
            move_val['fal_business_type'] = self.env.user.fal_business_type_id
        return move_vals_list

    def _svl_replenish_stock_am(self, stock_valuation_layers):
        move_vals_list = super(ProductProduct, self)._svl_replenish_stock_am(stock_valuation_layers)
        for move_val in move_vals_list:
            move_val['fal_business_type'] = self.env.user.fal_business_type_id
        return move_vals_list
