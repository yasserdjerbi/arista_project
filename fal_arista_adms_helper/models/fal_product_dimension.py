# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class ProductDimension(models.Model):
    _name = 'x_product_dimension'
    _description = "Product Dimension (Account)"

    name = fields.Char("Name")
    company_id = fields.Many2one('res.company', string='Company')
    fal_business_type = fields.Many2one("fal.business.type", string="Business Type", domain="[('company_id', '=', company_id)]")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_dimension_id = fields.Many2one('x_product_dimension', string='Product Dimension', copy=False)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_dimension_id = fields.Many2one('x_product_dimension', string='Product Dimension', copy=False)

    def _prepare_account_move_line(self, move):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals['product_dimension_id'] = self.product_dimension_id
        return vals

    def _prepare_invoice_line(self):
        res = super(PurchaseOrderLine, self)._prepare_invoice_line()
        res['product_dimension_id'] = self.product_dimension_id and self.product_dimension_id.id or False
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_dimension_id = fields.Many2one('x_product_dimension', string='Product Dimension', copy=False)

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['product_dimension_id'] = self.product_dimension_id and self.product_dimension_id.id or False
        return res
