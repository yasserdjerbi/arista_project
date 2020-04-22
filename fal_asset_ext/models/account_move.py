# -*- encoding: utf-8 -*-

import logging
from datetime import date, datetime
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ##############################################################################################
    # Override Odoo Method
    # Manage Split Asset per invoice line qty
    def _auto_create_asset(self):
        create_list = []
        invoice_list = []
        auto_validate = []
        for move in self:
            if not move.is_invoice():
                continue
            # loping for sum analytic account and product
            _type = []
            res = {}
            final_move_line = []
            # Define the asset_type
            if move.type == 'out_invoice':
                asset_type = 'sale'
            elif move.type == 'in_invoice':
                asset_type = 'purchase'
            else:
                asset_type = 'expense'
            for move_line in move.line_ids:
                if move_line.account_id and (move_line.account_id.can_create_asset) and move_line.account_id.create_asset != 'no' and not move.reversed_entry_id:
                    if not move_line.name:
                        raise UserError(_('Journal Items of {account} should have a label in order to generate an asset').format(account=move_line.account_id.display_name))
                    # Change Start Here
                    if move_line.account_id.asset_model.fal_manage_selection =='separate_unit':  
                        if not move_line.quantity.is_integer():
                            raise UserError(_("Automatic Separate Asset only Work on Whole Quantity"))
                        for move_line_qty in range(int(move_line.quantity)):
                            # Get the move_line debit / credit
                            total_credit = move_line.credit
                            total_debit = move_line.debit

                            # Original Value is the credit + debit / (quantity)
                            vals = {
                                'name': move_line.name,
                                'company_id': move_line.company_id.id,
                                'currency_id': move_line.company_currency_id.id,
                                'original_move_line_ids': [(6, False, move_line.ids)],
                                'original_value': (total_credit + total_debit) / (move_line.quantity or 1),
                                'state': 'draft',
                                'fal_manage_selection': 'separate_unit',
                                'asset_type': asset_type,
                            }
                            model_id = move_line.account_id.asset_model
                            if model_id:
                                vals.update({
                                    'model_id': model_id.id,
                                    'account_analytic_id': move_line.analytic_account_id.id or model_id.account_analytic_id.id,
                                })

                            auto_validate.append(move_line.account_id.create_asset == 'validate')
                            invoice_list.append(move)
                            create_list.append(vals)

                    # overwrite begin here to to procces combine state       
                    elif move_line.account_id.asset_model.fal_manage_selection=='combine':  
                        _type.append((move_line.product_id, move_line))

                    else:
                        vals = {
                            'name': move_line.name,
                            'company_id': move_line.company_id.id,
                            'currency_id': move_line.company_currency_id.id,
                            'original_move_line_ids': [(6, False, move_line.ids)],
                            'state': 'draft',
                        }
                        model_id = move_line.account_id.asset_model
                        if model_id:
                            vals.update({
                                'model_id': model_id.id,
                                'account_analytic_id': move_line.analytic_account_id.id or model_id.account_analytic_id.id,
                            })

                        auto_validate.append(move_line.account_id.create_asset == 'validate')
                        invoice_list.append(move)
                        create_list.append(vals)
                    # Change End Here

            for product, mv_line in _type:
                if product in res:
                    res[product] += mv_line
                else:
                    res[product] = mv_line
            _type2 = []
            res2 = {}

            for product_id in res:
                if len(res[product_id]) > 1:
                    for mv in res[product_id]:
                        _type2.append((mv.analytic_account_id, mv))
                    for analytic, mv_line2 in _type2:
                        if analytic in res2:
                            res2[analytic] += mv_line2
                        else:
                            res2[analytic] = mv_line2

                else:
                    final_move_line.append(res[product_id])

            for analytic in res2:
                final_move_line.append(res2[analytic])
            # overwrite for condition when product and analytic_account_id not same    
            for final in final_move_line:
                if len(final) == 1:
                    vals = {
                        'name': final.name,
                        'company_id': final.company_id.id,
                        'currency_id': final.company_currency_id.id,
                        'state': 'draft',
                        'fal_manage_selection': 'combine',
                        'asset_type': asset_type,
                        'original_move_line_ids': [(6, False, final.ids)],
                    }
                    model_id = final.account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                            'account_analytic_id': final.analytic_account_id.id or model_id.account_analytic_id.id
                        })

                    auto_validate.append(final.account_id.create_asset == 'validate')
                    invoice_list.append(move)
                    create_list.append(vals)
                # condition when to combine asset when product and analytic_account_id same           
                else:
                    original_value = 0
                    for item in final:
                        original_value += item.credit + item.debit

                    vals = {
                        'name': final[0].name,
                        'company_id': final[0].company_id.id,
                        'currency_id': final[0].company_currency_id.id,
                        'state': 'draft',
                        'fal_manage_selection': 'combine',
                        'asset_type': asset_type,
                        'original_move_line_ids': [(6, False, final.ids)],
                    }
                    model_id = final[0].account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                            'account_analytic_id': final[0].analytic_account_id.id or model_id.account_analytic_id.id
                        })

                    auto_validate.append(final[0].account_id.create_asset == 'validate')
                    invoice_list.append(move)
                    create_list.append(vals)

                # end of overwrite

        # raise EnvironmentError
        assets = self.env['account.asset'].create(create_list)
        for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):
            if 'model_id' in vals:
                if asset.fal_manage_selection != 'default':
                    model = asset.model_id
                    if model:
                        asset.method = model.method
                        asset.method_number = model.method_number
                        asset.method_period = model.method_period
                        asset.method_progress_factor = model.method_progress_factor
                        asset.prorata = model.prorata
                        asset.prorata_date = fields.Date.today()
                        asset.account_depreciation_id = model.account_depreciation_id
                        asset.account_depreciation_expense_id = model.account_depreciation_expense_id
                        asset.journal_id = model.journal_id
                    asset._onchange_method_period()
                else:
                    asset._onchange_model_id()
                    asset._onchange_method_period()
                    if move_line.analytic_account_id:
                        asset.account_analytic_id = move_line.analytic_account_id.id
                if validate:
                    asset.validate()
            if invoice:
                asset_name = {
                    'purchase': _('Asset'),
                    'sale': _('Deferred revenue'),
                    'expense': _('Deferred expense'),
                }[asset.asset_type]
                msg = _('%s created from invoice') % (asset_name)
                msg += ': <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>' % (invoice.id, invoice.name)
                asset.message_post(body=msg)
        return assets


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    # Override this field from Many2one to Many2many
    asset_id = fields.Many2many('account.asset', string='Asset Linked', help="Asset created from this Journal Item", copy=False)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    # Override this field fso it can't choose view models asset
    asset_model = fields.Many2one('account.asset', domain=lambda self: [('state', '=', 'model'), ('asset_type', '=', self.asset_type), ('fal_type', '=', 'normal')], help="If this is selected, an asset will be created automatically when Journal Items on this account are posted.")
