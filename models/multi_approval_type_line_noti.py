# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright Domiup (<http://domiup.com>).
#
##############################################################################

from odoo import api, models, fields
import logging

# _logger = logging.getLogger(__name__)


class MultiApprovalTypeLineNoti(models.Model):
    _name = 'multi.approval.type.line.noti'
    _description = 'Multi Aproval Type Lines Noti'
    _rec_name = 'user_id'
    _order = 'sequence'

    name = fields.Char(string='Title')
    # company_id = fields.Many2one('res.company', related='approv_id.company_id')
    user_id = fields.Many2one(string='User', comodel_name="res.users",
                              required=True, ondelete='cascade'
                              )
    department_id = fields.Many2one(string='Department', comodel_name='hr.department')
    sequence = fields.Integer(string='Sequence')
    require_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ], string="Type of Approval", default='Optional')
    approv_id = fields.Many2one(
        string="Type", comodel_name="multi.approval.type", required=True)
    # approv_idss = fields.Many2one(
    #     string="Types", comodel_name="multi.approval", required=True)
    existing_user_ids = fields.Many2many('res.users', compute='_compute_existing_user_ids')
    product_category = fields.Many2one('product.category', string='Nhóm hàng hóa')
    nhamaywl = fields.Many2many('hr.nhamay.wl', string='Nhà máy')
    xuong = fields.Many2many('xuong.wl', string='Xưởng')
    # def get_user(self):
    #     self.ensure_one()
    #     return self.user_id.id

    @api.depends('approv_id')
    def _compute_existing_user_ids(self):
        for record in self:
            record.existing_user_ids = record.approv_id.approv_ids.user_id

    @api.onchange("user_id")
    def _onchange_department_id(self):
        self.department_id = self.user_id.department_id



