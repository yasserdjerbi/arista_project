# -*- coding: utf-8 -*-
# Copyright 2004-2009 Tiny SPRL (<http://tiny.be>).
# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.constrains('discount')
    def _check_discount(self):
        if self.discount < 0:
            raise UserError(_('You can only put discount from 0% to less than 100%'))
