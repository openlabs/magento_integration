# -*- coding: utf-8 -*-
"""
    account

    Account

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv, fields


class Tax(osv.Model):
    "Account Tax"
    _inherit = 'account.tax'

    _columns = {
        'used_on_magento': fields.boolean('Is this tax used on magento ?')
    }

Tax()
