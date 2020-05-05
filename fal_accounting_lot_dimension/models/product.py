# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # -------------------------------------------------------------------------
    # Override SVL creation helpers
    # -------------------------------------------------------------------------
    def _prepare_in_svl_vals(self, quantity, unit_cost):
        """Adding new Condition 'lot' on the vals management
        """
        self.ensure_one()
        vals = super(ProductProduct, self)._prepare_in_svl_vals(quantity, unit_cost)
        if self.cost_method in ('lot'):
            vals['remaining_qty'] = quantity
            vals['remaining_value'] = vals['value']
        return vals

    def _prepare_out_svl_vals(self, quantity, company):
        """Adding new Condition 'lot' to be considered in vals
        """
        self.ensure_one()
        vals = super(ProductProduct, self)._prepare_out_svl_vals(quantity, company)
        quantity = -1 * quantity
        if self.cost_method in ('lot'):
            fifo_vals = self._run_fifo(abs(quantity), company)
            vals['remaining_qty'] = fifo_vals.get('remaining_qty')
            vals.update(fifo_vals)
        return vals

    def _run_fifo(self, quantity, company):
        self.ensure_one()
        # We split here, if cost method are lot, we do something else
        if self.cost_method == 'lot':
            # Find back incoming stock valuation layers (called candidates here) to value `quantity`.
            qty_to_take_on_candidates = quantity
            if self._context.get('lot_id'):
                candidates = self.env['stock.valuation.layer'].sudo().search([
                    ('product_id', '=', self.id),
                    ('remaining_qty', '>', 0),
                    ('company_id', '=', company.id),
                    ('lot_id', '=', self._context.get('lot_id')),
                ])
            else:
                candidates = self.env['stock.valuation.layer'].sudo().search([
                    ('product_id', '=', self.id),
                    ('remaining_qty', '>', 0),
                    ('company_id', '=', company.id),
                ])
            new_standard_price = 0
            tmp_value = 0  # to accumulate the value taken on the candidates
            for candidate in candidates:
                qty_taken_on_candidate = min(qty_to_take_on_candidates, candidate.remaining_qty)

                candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                new_standard_price = candidate_unit_cost
                value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                candidate_vals = {
                    'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                    'remaining_value': new_remaining_value,
                }

                candidate.write(candidate_vals)

                qty_to_take_on_candidates -= qty_taken_on_candidate
                tmp_value += value_taken_on_candidate
                if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                    break

            # Update the standard price with the price of the last used candidate, if any.
            if new_standard_price and self.cost_method == 'lot':
                self.sudo().with_context(force_company=company.id).standard_price = new_standard_price

            # If there's still quantity to value but we're out of candidates, we fall in the
            # negative stock use case. We chose to value the out move at the price of the
            # last out and a correction entry will be made once `_fifo_vacuum` is called.
            vals = {}
            if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                vals = {
                    'value': -tmp_value,
                    'unit_cost': tmp_value / quantity,
                }
            else:
                assert qty_to_take_on_candidates > 0
                last_fifo_price = new_standard_price or self.standard_price
                negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
                tmp_value += abs(negative_stock_value)
                vals = {
                    'remaining_qty': -qty_to_take_on_candidates,
                    'value': -tmp_value,
                    'unit_cost': last_fifo_price,
                }
            return vals
        else:
            return super(ProductProduct, self)._run_fifo(quantity, company)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_cost_method = fields.Selection(selection_add=[('lot', 'Lot/Serial Number')])
