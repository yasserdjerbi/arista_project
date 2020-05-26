from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_invoice_line(self):
        res = super(PurchaseOrderLine, self)._prepare_invoice_line()
        res['lot_id'] = self.lot_id and self.lot_id.id or False
        return res
