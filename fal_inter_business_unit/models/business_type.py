from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import Warning


class BusinessType(models.Model):
    _inherit = 'fal.business.type'

    interbusinesstype_transaction_message = fields.Char(compute='_compute_interbusinesstype_transaction_message')

    @api.depends('rule_type', 'applicable_on', 'auto_validation', 'warehouse_id', 'name')
    def _compute_interbusinesstype_transaction_message(self):
        self.interbusinesstype_transaction_message = self._interbusinesstype_transaction_message(self.rule_type, self.auto_validation, self.applicable_on, self.warehouse_id)

    def _interbusinesstype_transaction_message(self, rule_type, auto_validation, applicable_on, warehouse_id):
        if rule_type == 'not_synchronize':
            return ''
        if rule_type == 'invoice_and_refund':
            return _('Generate a bill/invoice when a business type confirms an invoice/bill for %s.') % self.name

        genereted_object = {
            'sale': _('purchase order'),
            'purchase': _('sales order'),
            'sale_purchase': _('purchase/sales order'),
            False: ''
        }
        event_type = {
            'sale': _('sales order'),
            'purchase': _('purchase order'),
            'sale_purchase': _('sales/purchase order'),
            False: ''
        }
        text = {
            'validation': _('validated') if auto_validation else _('draft'),
            'generated_object': genereted_object[applicable_on],
            'warehouse': warehouse_id.display_name,
            'event_type': event_type[applicable_on],
            'businesstype': self.name,
        }
        if applicable_on != 'sale':
            return _('Generate a %(validation)s %(generated_object)s\
                using warehouse %(warehouse)s when a business type confirms a %(event_type)s for %(businesstype)s.') % text
        else:
            return _('Generate a %(validation)s %(generated_object)s\
                when a business type confirms a %(event_type)s for %(businesstype)s.') % text

    rule_type = fields.Selection([('not_synchronize', 'Do not synchronize'),
        ('invoice_and_refund', 'Synchronize invoices/bills'),
        ('so_and_po', 'Synchronize sales/purchase orders')], string="Rule",
        help='Select the type to setup inter business rules in selected business type/unit.', default='not_synchronize')
    applicable_on = fields.Selection([('sale', 'Sales Order'), ('purchase', 'Purchase Order'),
          ('sale_purchase', 'Sales and Purchase Order')], string="Apply on")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse",
        help="Default value to set on Purchase(Sales) Orders that will be created based on Sale(Purchase) Orders made to this business")
    auto_validation = fields.Boolean(string="Automatic Validation")
    interbusiness_user_id = fields.Many2one("res.users", string="Assign to", default=SUPERUSER_ID,
        help="Responsible user for creation of documents triggered by interbusiness rules.")

    @api.model
    def _find_business_from_partner(self, partner_id):
        business = self.sudo().search([('partner_id', '=', partner_id)], limit=1)
        return business or False
