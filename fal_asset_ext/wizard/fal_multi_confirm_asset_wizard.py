from odoo import api, models, _
from odoo.exceptions import UserError


class fal_multi_confirm_asset_wizard(models.TransientModel):
    _name = "fal.multi.confirm.asset.wizard"
    _description = "Multi Confirm Asset Wizard"

    def action_confirm(self):
        if self.env.context.get('active_ids', False):
            asset_obj = self.env['account.asset']
            asset_ids = asset_obj.browse(
                self.env.context.get('active_ids', False))
            asset_ids_not_draft = asset_ids.filtered(
                lambda r: r.state != 'draft')
            if asset_ids_not_draft:
                raise UserError(_('Asset should be in draft to confirm it!'))
            for asset_id in asset_ids:
                asset_id.validate()
        return {'type': 'ir.actions.act_window_close'}
