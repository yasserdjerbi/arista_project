from odoo import api, fields, models, _
from odoo.exceptions import Warning
import ast
import logging

_logger = logging.getLogger(__name__)


class CreateMenuWizard(models.TransientModel):
    _inherit = "create.menu.wizard"

    select_action = fields.Selection(selection_add=[('account.move', 'Invoice')])

    @api.onchange('select_action')
    def _onchange_select_action(self):
        if self.select_action == 'account.move':
            self.action = ''.join(['ir.actions.act_window', ',', str(self.env.ref('account.action_move_out_invoice_type').id)])
        return super(CreateMenuWizard, self)._onchange_select_action()
