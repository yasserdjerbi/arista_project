# -*- encoding: utf-8 -*-

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero, float_round
import logging

_logger = logging.getLogger(__name__)


class account_asset(models.Model):
    _inherit = 'account.asset'

    ##############################################################################################
    # Fields Definition
    # 1. Parent-Childs Definition
    fal_type = fields.Selection([
        ('view', 'View'),
        ('normal', 'Normal')
    ], 'Type', required=True, default='normal')
    parent_id = fields.Many2one('account.asset', 'Parent Model', domain="[('fal_type', '=', 'view')]")
    child_ids = fields.One2many('account.asset', 'parent_id', 'Children(s)', copy=False)
    # 2. Additional Info
    fal_closing_date = fields.Date(string='Closing Date', help="The Closing Date", compute='_fal_closing_date', store=True)
    fal_asset_number = fields.Char('Asset Number', size=64)
    # 3. New Depreciation Second Date Method
    date_first_depreciation = fields.Selection([
        ('manual', 'Manual'),
        ('end_of_last_month', 'Based on Last Day of Purchase Period')],
        string='Depreciation Dates', default='manual', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    fal_second_depreciation_date = fields.Date('Second Depreciation Date', readonly=True, states={'draft': [('readonly', False)]})
    # 4. To Manage if create separate unit
    # fal_separate_unit = fields.Boolean('Separate Unit', help='Create Separate Asset per Unit on Vendor Bills')
    # 4. To Manage if create separate unit or Combine and default
    fal_manage_selection = fields.Selection([
        ('separate_unit', 'Separate Unit'),
        ('combine', 'Combine'),
        ('default', 'Default')
    ], 'Manage Asset', required=True, default='default')
    # 5. Override this field from One2many to Many2many
    original_move_line_ids = fields.Many2many('account.move.line', string='Journal Items', readonly=True, states={'draft': [('readonly', False)]}, copy=False)

    ##################################################################################################
    # Constrains
    # Parent Relation Recursive Check
    @api.constrains('parent_id')
    def _check_parent_id(self):
        if any(not asset_model._check_recursion() for asset_model in self):
            raise ValidationError(_("Error! You can't create recursive hierarchy of Activity."))

    ###################################################################################################
    # Onchange
    # If select Parent, get all the parent info and set to record
    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.journal_id = self.parent_id.journal_id
            self.account_asset_id = self.parent_id.account_asset_id
            self.account_depreciation_id = self.parent_id.account_depreciation_id
            self.account_depreciation_expense_id = self.parent_id.account_depreciation_expense_id
            self.method_number = self.parent_id.method_number
            self.method_period = self.parent_id.method_period
            self.method = self.parent_id.method
            self.method_progress_factor = self.parent_id.method_progress_factor

    # If select Date First Depreciation not manual, set the first depreciation date
    @api.onchange('date_first_depreciation')
    def _onchange_date_first_depreciation(self):
        if self.date_first_depreciation == 'end_of_last_month':
            self.first_depreciation_date = self._get_first_depreciation_date()

    ###################################################################################################
    # Compute Logic
    # Define The closing Date Logic
    @api.depends('depreciation_move_ids')
    def _fal_closing_date(self):
        for record in self:
            temp_last_date = False
            for line in record.depreciation_move_ids:
                if temp_last_date:
                    if temp_last_date < line.date:
                        temp_last_date = line.date
                else:
                    temp_last_date = line.date
            record.fal_closing_date = temp_last_date

    ####################################################################################################
    # completely override odoo method
    # Manage Value if we use split
    @api.depends('original_move_line_ids', 'original_move_line_ids.account_id', 'asset_type')
    def _compute_value(self):
        for record in self:
            misc_journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('company_id', '=', record.company_id.id)], limit=1)
            if not record.original_move_line_ids:
                record.account_asset_id = record.account_asset_id or False
                record.original_value = record.original_value or False
                record.display_model_choice = record.state == 'draft' and self.env['account.asset'].search([('state', '=', 'model'), ('asset_type', '=', record.asset_type)])
                record.display_account_asset_id = True
                continue
            if any(line.move_id.state == 'draft' for line in record.original_move_line_ids):
                raise UserError(_("All the lines should be posted"))
            if any(account != record.original_move_line_ids[0].account_id for account in record.original_move_line_ids.mapped('account_id')):
                raise UserError(_("All the lines should be from the same account"))
            record.account_asset_id = record.original_move_line_ids[0].account_id
            record.display_model_choice = record.state == 'draft' and len(self.env['account.asset'].search([('state', '=', 'model'), ('account_asset_id.user_type_id', '=', record.user_type_id.id)]))
            record.display_account_asset_id = False
            if not record.journal_id:
                record.journal_id = misc_journal_id
            total_credit = sum(line.credit for line in record.original_move_line_ids)
            total_debit = sum(line.debit for line in record.original_move_line_ids)
            # Change Start Here
            if record.fal_manage_selection=='separate_unit':
                record.original_value = (total_credit + total_debit) / (sum(line.quantity for line in record.original_move_line_ids) or 1)
            else:
                record.original_value = (total_credit + total_debit)
            # Change End Here
            if (total_credit and total_debit) or record.original_value == 0:
                raise UserError(_("You cannot create an asset from lines containing credit and debit on the account or with a null amount"))

    def _recompute_board(self, depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids):
        self.ensure_one()
        residual_amount = amount_to_depreciate
        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        move_vals = []
        prorata = self.prorata and not self.env.context.get("ignore_prorata")
        if amount_to_depreciate != 0.0:
            for asset_sequence in range(starting_sequence + 1, depreciation_number + 1):
                while amount_change_ids and amount_change_ids[0].date <= depreciation_date:
                    residual_amount -= amount_change_ids[0].amount_total
                    amount_to_depreciate -= amount_change_ids[0].amount_total
                    already_depreciated_amount += amount_change_ids[0].amount_total
                    amount_change_ids[0].write({
                        'asset_remaining_value': float_round(residual_amount, precision_rounding=self.currency_id.rounding),
                        'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                    })
                    amount_change_ids -= amount_change_ids[0]
                amount = self._compute_board_amount(asset_sequence, residual_amount, amount_to_depreciate, depreciation_number, starting_sequence, depreciation_date)
                prorata_factor = 1
                move_ref = self.name + ' (%s/%s)' % (prorata and asset_sequence - 1 or asset_sequence, self.method_number)
                if prorata and asset_sequence == 1:
                    move_ref = self.name + ' ' + _('(prorata entry)')
                    first_date = self.prorata_date
                    if int(self.method_period) % 12 != 0:
                        month_days = calendar.monthrange(first_date.year, first_date.month)[1]
                        days = month_days - first_date.day + 1
                        prorata_factor = days / month_days
                    else:
                        total_days = (depreciation_date.year % 4) and 365 or 366
                        days = (self.company_id.compute_fiscalyear_dates(first_date)['date_to'] - first_date).days + 1
                        prorata_factor = days / total_days
                amount = self.currency_id.round(amount * prorata_factor)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount

                move_vals.append(self.env['account.move']._prepare_move_for_asset_depreciation({
                    'amount': amount,
                    'asset_id': self,
                    'move_ref': move_ref,
                    'date': depreciation_date,
                    'asset_remaining_value': float_round(residual_amount, precision_rounding=self.currency_id.rounding),
                    'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                }))

                initial_depreciation_date = depreciation_date
                depreciation_date = depreciation_date + relativedelta(months=+int(self.method_period))
                # datetime doesn't take into account that the number of days is not the same for each month
                if (not self.prorata or self.env.context.get("ignore_prorata")) and int(self.method_period) % 12 != 0:
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=max_day_in_month)
                # Change Start Here
                # If we are using second depreciation date method and the start of depreciation date is lower thatn the second depreciation date
                if self.fal_second_depreciation_date and initial_depreciation_date < self.fal_second_depreciation_date:
                    depreciation_date = self.fal_second_depreciation_date
                # Change End Here
        return move_vals

    ############################################################################################
    # Manage Create Method, to put the sequence number on the asset
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['fal_asset_number'] = self.env['ir.sequence'].next_by_code('fal.account.asset.asset') or 'New'
        return super(account_asset, self).create(vals_list)
