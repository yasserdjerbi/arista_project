# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GenerateFakturPajak(models.TransientModel):
    _name = 'generate.faktur.pajak'
    _description = "Generate Faktur Pajak"

    kode_cabang = fields.Char(
        string="Kode Cabang ", size=3, required=True)
    nomor_awal = fields.Char(string='Nomor Faktur Awal', size=8, required=True)
    nomor_akhir = fields.Char(
        string='Nomor Faktur Akhir', size=8, required=True)
    tahun = fields.Char(
        string='Tahun Penerbit', size=2,
        required=True,
        default=lambda self: fields.Date.from_string(
            fields.Date.context_today(self)
        ).strftime('%y')
    )
    pajak_type = fields.Selection(
        [
            ('in', 'Faktur Pajak Masukan'),
            ('out', 'Faktur Pajak Keluaran')
        ], string='Type', default='out'
    )

    def generate_faktur(self):
        for item in self:
            pajak_obj = self.env['faktur.pajak']
            awal = int(item.nomor_awal)
            akhir = int(item.nomor_akhir)
            while (awal <= akhir):
                vals = {
                    'tahun_penerbit': item.tahun,
                    'kode_cabang': item.kode_cabang,
                    'nomor_urut': '%08d' % awal,
                    'state': '0',
                    'pajak_type': item.pajak_type,
                }
                pajak_obj.create(vals)
                awal += 1
        return {'type': 'ir.actions.act_window_close'}
