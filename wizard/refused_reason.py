# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright Domiup (<http://domiup.com>).
#
##############################################################################

from odoo import api, fields, models


class RefusedReason(models.TransientModel):
    _name = 'refused.reason'
    _description = 'Refused Reason'

    reason = fields.Text('Reason', required=True)
    start_date = fields.Datetime(string='Ngày')

    def action_reason_apply(self):
        approval = self.env['multi.approval'].browse(
            self.env.context.get('active_ids'))
        return approval.action_refuse(reason=self.reason)
    
class CheckInOut(models.TransientModel):
    _name = 'check.in.out'
    _description = 'Check In Out'

    check = fields.Text('Reason')
    def action_check(self):
        approval = self.env['multi.approval'].browse(
            self.env.context.get('active_ids'))
        return approval.check_out()
