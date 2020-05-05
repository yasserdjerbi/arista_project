# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.depends('company_id', 'location_id', 'owner_id', 'product_id', 'quantity')
    def _compute_value(self):
        """ We Split the method, if it's cost method by lot, we inject on the if cost_method part, to consider fifo/lot else, just move like usual
        """
        for quant in self:
            if quant.product_id.cost_method == 'lot':
                # If the user didn't enter a location yet while enconding a quant.
                if not quant.location_id:
                    quant.value = 0
                    return

                if not quant.location_id._should_be_valued() or\
                        (quant.owner_id and quant.owner_id != quant.company_id.partner_id):
                    quant.value = 0
                    continue
                if quant.product_id.cost_method in ('fifo', 'lot'):
                    quantity = quant.product_id.quantity_svl
                    if float_is_zero(quantity, precision_rounding=quant.product_id.uom_id.rounding):
                        quant.value = 0.0
                        continue
                    average_cost = quant.product_id.value_svl / quantity
                    quant.value = quant.quantity * average_cost
                else:
                    quant.value = quant.quantity * quant.product_id.standard_price
            else:
                super(StockQuant, self)._compute_value()
