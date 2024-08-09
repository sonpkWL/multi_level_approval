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
    _name = 'multi.approval.item.line'
    _description = 'Multi Aproval Item Lines'

    multi_approval_id = fields.Many2one('multi.approval')
    approval_state = fields.Selection(related='multi_approval_id.state')
    is_pic = fields.Boolean(compute='_check_pic', related='multi_approval_id.is_pic')
    name = fields.Char(string='Tên SP', required=True)
    quantity = fields.Float(string='Số lượng', required=True)
    Uom = fields.Char(string='Đơn vị tính')
    comment = fields.Char(string='Mục đích')
    yckt = fields.Char(string='Yêu cầu kĩ thuật')
    xuatxu = fields.Char(string='Xuất xứ')
    bpsd = fields.Char(string='Bộ phận sử dụng')
    masp = fields.Char(string='Mã SP')
    state = fields.Selection(
        [('Approved', 'Phê duyệt'),
         ('Submitted', 'Chờ duyệt'),
         ('Refused', 'Từ chối')], default='Submitted', string='Trạng thái')
    # type_id = fields.Many2one(
    #     string="Type", comodel_name="multi.approval.type", required=True)

    def action_approve_item(self):
        for item in self:
            item.write({
                'state': 'Approved'
            })
    def action_refuse_item(self):
        for item in self:
            item.write({
                'state': 'Refused'
            })
