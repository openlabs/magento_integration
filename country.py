# -*- coding: utf-8 -*-
"""
    country

    Country

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv
from openerp.tools.translate import _


class Country(osv.osv):
    "Country"
    _inherit = 'res.country'

    def search_using_magento_code(self, cursor, user, code, context):
        """
        Searches for country with given magento code.

        :param cursor: Database cursor
        :param user: ID of current user
        :param code: ISO code of country
        :param context: Application context
        :return: Browse record of country if found else raises error
        """
        country_ids = self.search(
            cursor, user, [('code', '=', code)], context=context
        )

        if not country_ids:
            raise osv.except_osv(
                _('Not Found!'),
                _('Country with ISO code %s does not exists.' % code)
            )

        country = self.browse(
            cursor, user, country_ids[0], context=context
        )
        return country
