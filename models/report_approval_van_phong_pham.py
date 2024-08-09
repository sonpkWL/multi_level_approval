from odoo import models, fields, tools, _
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
    
class ReportMultiApprovalVanPhongPham(models.Model):
    _name = 'report.multi.approval.van.phong.pham'
    _description = 'Multi-level Approval Report for Van Phong Pham'
    _auto = False
    _order = 'request_date DESC'

    code = fields.Char(string='Mã', readonly=True)
    name = fields.Char(string='Tiêu đề', readonly=True)
    description = fields.Html('Mô tả', readonly=True)
    request_date = fields.Datetime(string='Ngày yêu cầu', readonly=True)
    state = fields.Selection(
        [('Draft', 'Draft'),
         ('Submitted', 'Submitted'),
         ('Approved', 'Approved'),
         ('Refused', 'Refused'),
         ('Cancel', 'Cancel')], string='Trạng thái', tracking=True, readonly=True)
    mnv = fields.Char(string='Mã nhân viên',readonly=True)
    user_id = fields.Many2one('res.users', string='Người tạo', readonly=True)
    nhamaywl = fields.Many2one('hr.nhamay.wl', string='Nhà máy', readonly=True)
    type_id = fields.Many2one('multi.approval.type', string='Loại phiếu', readonly=True)
    line_id = fields.Many2one('multi.approval.line', string='line', readonly=True)
    pic_id = fields.Many2one('res.users', string='Người duyệt', readonly=True)
    deadline = fields.Date(string='Ngày đến hạn', readonly=True)
    priority = fields.Selection(
        [('0', 'Normal'),
         ('1', 'Medium'),
         ('2', 'High'),
         ('3', 'Very High')], string='Ưu tiên', default='0', readonly=True)
    name_item = fields.Many2one('multi.approval.item.line', string='Tên sản phẩm', readonly=True)
    Uom = fields.Many2one('multi.approval.item.line', string='Đơn vị tính', readonly=True)
    quantity = fields.Many2one('multi.approval.item.line', string='Số lượng', readonly=True)
    yckt = fields.Many2one('multi.approval.item.line', string='Yêu cầu kỹ thuật', readonly=True)
    xuatxu = fields.Many2one('multi.approval.item.line', string='Xuất xứ', readonly=True)
    bpsd = fields.Many2one('multi.approval.item.line', string='Bộ phận sử dụng', readonly=True)
    masp = fields.Many2one('multi.approval.item.line', string='Mã sản phẩm', readonly=True)
    comment = fields.Many2one('multi.approval.item.line', string='Mục đích', readonly=True)
    item_state = fields.Selection(
        [('Approved', 'Phê duyệt'),
         ('Submitted', 'Chờ duyệt'),
         ('Refused', 'Từ chối')], default='Submitted', string='Trạng thái')
    

    def _select(self):
        return """
           SELECT row_number() OVER () as id, l.code, l.name, l.description, l.request_date
					, l.state, emp.description as mnv
					, l.user_id, emp.nhamaywl
                    , l.type_id as type_id, l.line_id, line.user_id as pic_id
                    , line.deadline, l.priority
					,item.name as name_item,item."Uom" as Uom,item.quantity,item.yckt
					,item.xuatxu,item.bpsd,item.masp,item.comment,item.state as item_state
        """
    def _from(self):
        return """
           multi_approval as l
                left join res_users as r on l.user_id = r.id
                left join multi_approval_type as t on t.id = l.type_id
                left join multi_approval_line as line on line.id = l.line_id
                left join hr_employee as emp on emp.user_id = r.id
				left join multi_approval_item_line as item on item.multi_approval_id = l.id
        """
    def _where(self):
        return """
            t.id = 14
        """
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM %s
            WHERE %s
            )""" % (self._table, self._select(), self._from(),
                    self._where()))
        