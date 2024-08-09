# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright Domiup (<http://domiup.com>).
#
##############################################################################

from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class MultiApprovalTypeLine(models.Model):
    _name = 'multi.approval.type.line'
    _description = 'Multi Aproval Type Lines'
    _order = 'sequence'

    name = fields.Char(string='Title')
    stt = fields.Integer(string='Stt', default = 2, 
                         help="""Số thứ tự được đánh bắt đầu từ 2. 
                        Nếu duyệt cùng cấp thì đánh số thứ tự trùng nhau""")
    # user_id = fields.Many2one(string='User', comodel_name="res.users",
    #                           required=True)
    user_id = fields.Many2one(string='User', comodel_name="res.users", related='user_id_approval.authority_id', required=True)
    user_id_approval = fields.Many2one(string='User approval', comodel_name="res.users",
                              required=True)
    sequence = fields.Integer(string='Sequence')
    require_opt = fields.Selection(
        [('Required', 'Required'),
         ('Optional', 'Optional'),
         ], string="Type of Approval", default='Required')
    type_id = fields.Many2one(
        string="Type", comodel_name="multi.approval.type", required=True)
    existing_user_ids = fields.Many2many('res.users', compute='_compute_existing_user_ids')
    product_category = fields.Many2one('product.category', 'Nhóm hàng hóa')
    nhamaywl = fields.Many2many('hr.nhamay.wl', string='Nhà máy')
    xuong = fields.Many2many('xuong.wl', string='Xưởng')
    check_amount = fields.Boolean(string='Áp dụng quy tắc')
    type_values = fields.Selection([
        ('==', 'Bằng')
        , ('<', 'Lớn hơn')
        , ('>', 'Nhỏ hơn')
        , ('<=', 'Lớn hơn hoặc bằng')
        , ('>=', 'Nhỏ hơn hoặc bằng')
        , ('between', 'Trong khoảng')
        , ('!=', 'Khác')
    ], string='Quy tắc')
    gt1 = fields.Float(string='Giá trị')
    gt2 = fields.Float(string='Đến giá trị')


    def get_user(self):
        self.ensure_one()
        return self.user_id.id

    @api.depends('type_id')
    def _compute_existing_user_ids(self):
        for record in self:
            record.existing_user_ids = record.type_id.line_ids.user_id
