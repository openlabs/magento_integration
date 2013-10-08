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
        'used_on_magento': fields.boolean('Is this tax used on magento ?'),
        'apply_on_magento_shipping': fields.boolean(
            'Is this tax applied on magento shipping ?',
            help='This tax should have *Tax Included in Price* set as True'
        )
    }

    def check_apply_on_magento_shipping(self, cursor, user, ids, context=None):
        """
        Checks that only one tax has been chosen to be applied on magento
        shipping

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: IDs of records
        :param context: Application context
        :return: True or False
        """
        if len(self.search(cursor, user, [
            ('apply_on_magento_shipping', '=', True)
        ], context=context)) > 1:
            return False
        return True

    _constraints = [
        (
            check_apply_on_magento_shipping,
            'Error: Only 1 tax can be chosen to apply on magento shipping',
            []
        )
    ]

    def onchange_apply_on_magento_shipping(
        self, cursor, user, ids, apply_on_magento_shipping, context=None
    ):
        """Set *Tax Included in Price* set as True
        """
        return {'value': {'price_include': apply_on_magento_shipping}}

Tax()
