from odoo import api, fields, models, _
import ast


class CreateMenuWizard(models.TransientModel):
    _name = "create.menu.wizard"
    _description = 'Business unit create menu wizard'

    name = fields.Char(String='Menu', required=True)
    parent_menu_id = fields.Many2one('ir.ui.menu', String='Parent Menu')
    select_action = fields.Selection([], string='Menu Action',)
    action = fields.Reference(
        selection=[
            ('ir.actions.report', 'ir.actions.report'),
            ('ir.actions.act_window', 'ir.actions.act_window'),
            ('ir.actions.act_url', 'ir.actions.act_url'),
            ('ir.actions.server', 'ir.actions.server'),
            ('ir.actions.client', 'ir.actions.client')], string="Action")

    @api.onchange('select_action')
    def _onchange_select_action(self):
        pass

    def create_business_menu(self):
        menu_env = self.env['ir.ui.menu']
        action_base = self.action
        action_created = action_base.copy()

        try:
            replace_text = action_created.context
            replace_domain = action_created.domain
            replace_text = replace_text.replace(" ", "")
            replace_domain = replace_domain.replace(" ", "")
            context_dict = ast.literal_eval(replace_text)
            domain_dict = ast.literal_eval(replace_domain)
            domain_dict.append(('fal_business_type', '=', self._context.get('active_id')))
            context_dict.update({'default_fal_business_type': self._context.get('active_id')})
        except:
            domain_dict = [('fal_business_type', '=', self._context.get('active_id'))]
            context_dict = {'default_fal_business_type': self._context.get('active_id')}

        action_created.write({
            'name': self.name,
            'domain': domain_dict,
            'context': str(context_dict)
        })

        menu_env.create({
            'name': self.name,
            'parent_id': self.parent_menu_id.id,
            'action': ''.join(['ir.actions.act_window', ',', str(action_created.id)])
        })
