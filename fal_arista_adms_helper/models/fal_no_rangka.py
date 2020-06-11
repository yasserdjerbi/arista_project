# -*- coding: utf-8 -*-
from odoo import fields, models, api
from lxml.builder import E


class NoRangka(models.Model):
    _name = 'x_no_rangka'
    _description = "Nomor Rangka"

    name = fields.Char("Name")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    no_rangka_id = fields.Many2one('x_no_rangka', string='No Rangka', copy=False)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    no_rangka_id = fields.Many2one('x_no_rangka', string='No Rangka', copy=False)

    def _prepare_account_move_line(self, move):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals['no_rangka_id'] = self.no_rangka_id
        return vals

    def _prepare_invoice_line(self):
        res = super(PurchaseOrderLine, self)._prepare_invoice_line()
        res['no_rangka_id'] = self.no_rangka_id and self.no_rangka_id.id or False
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    no_rangka_id = fields.Many2one('x_no_rangka', string='No Rangka', copy=False)

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['no_rangka_id'] = self.no_rangka_id and self.no_rangka_id.id or False
        return res
