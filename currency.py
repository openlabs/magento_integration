# -*- coding: utf-8 -*-
"""
    currency

    Currency

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv
from openerp.tools.translate import _


class Currency(osv.osv):
    "Currency"
    _inherit = 'res.currency'

    def search_using_magento_code(self, cursor, user, code, context):
        """
        Searches for currency with given magento code.

        :param cursor: Database cursor
        :param user: ID of current user
        :param code: Currency code
        :param context: Application context
        :return: Browse record of currency if found else raises error
        """
        currency_ids = self.search(
            cursor, user, [
                ('name', '=', code)
            ], context=context
        )

        if not currency_ids:
            raise osv.except_osv(
                _('Not Found!'),
                _('Currency with code %s does not exists.' % code)
            )

        currency = self.browse(
            cursor, user, currency_ids[0], context=context
        )
        return currency
