# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['discount_fixed'] = self.x_studio_adms_discount
        return res
