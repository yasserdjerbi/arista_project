# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.osv.expression import OR


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_subcontract_mo_vals(self, subcontract_move, bom):
        vals = super(StockPicking, self)._prepare_subcontract_mo_vals(subcontract_move, bom)
        if bom.product_tmpl_id.cost_method in ('fifo', 'average', 'lot'):
            vals = dict(vals, extra_cost=subcontract_move._get_price_unit())
        return vals
