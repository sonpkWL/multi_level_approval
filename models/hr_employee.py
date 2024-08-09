# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
from odoo.osv import expression
from odoo.tools import format_date, Query

class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    multi_approval_type_ids = fields.Many2many('multi.approval.type', 'hr_employee_approval_type_rel'
                                               , 'employee_id', 'approval_type_id'
                                               , string='Các đề xuất', compute_sudo=True)

    # def _compute_coach(self):
    #     for employee in self:
    #         manager = employee.parent_id
    #         previous_manager = employee._origin.parent_id
    #         if manager and (employee.coach_id == previous_manager or not employee.coach_id):
    #             employee.coach_id = manager
    #         elif not employee.coach_id:
    #             employee.coach_id = False
