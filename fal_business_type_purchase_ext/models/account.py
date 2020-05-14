# -*- coding: utf-8 -*-
from odoo import fields, models, api


class account_move(models.Model):
    _inherit = 'account.move'

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        if self.purchase_vendor_bill_id.vendor_bill_id:
            if not self.fal_business_type:
                self.fal_business_type = self.purchase_vendor_bill_id.vendor_bill_id.fal_business_type.id
        elif self.purchase_vendor_bill_id.purchase_order_id:
            if not self.fal_business_type:
                self.fal_business_type = self.purchase_vendor_bill_id.purchase_order_id.fal_business_type.id
        elif self.purchase_id:
            self.fal_business_type = self.purchase_id.fal_business_type.id
        return super(account_move, self)._onchange_purchase_auto_complete()
