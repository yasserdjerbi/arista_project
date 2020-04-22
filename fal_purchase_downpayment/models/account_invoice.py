# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def unlink(self):
        downpayment_lines = self.mapped('line_ids.purchase_line_id').filtered(lambda line: line.fal_is_downpayment)
        res = super(AccountMove, self).unlink()
        for downpayment_line in downpayment_lines:
            # As we can't use odoo unlink (Blocked by the purchase state, we need to force it by cr)
            query = """
                DELETE FROM purchase_order_line
                WHERE id = %s""" % downpayment_line.id
            self.env.cr.execute(query)
        return res
