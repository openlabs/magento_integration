# -*- coding: utf-8 -*-
"""
    partner

    Partner

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import fields, osv
from openerp.tools.translate import _


class MagentoWebsitePartner(osv.Model):
    "Magento Website partner store"
    _name = 'magento.website.partner'

    _columns = dict(
        magento_id=fields.integer('Magento ID', readonly=True),
        website=fields.many2one(
            'magento.instance.website', 'Website', required=True,
            readonly=True,
        ),
        partner=fields.many2one(
            'res.partner', 'Partner', required=True, readonly=True
        )
    )

    _sql_constraints = [(
        'magento_id_website_unique', 'unique(magento_id, website)',
        'A partner must be unique in an website'
    )]


class Partner(osv.Model):
    "Partner"
    _inherit = 'res.partner'

    _columns = dict(
        magento_ids=fields.one2many(
            'magento.website.partner', 'partner', "Magento IDs", readonly=True
        ),
    )

    def find_or_create(self, cursor, user, values, context):
        """
        Looks for the customer whose `values` are sent by magento against
        the `magento_website_id` in context.
        If a record exists for this, return that else create a new one and
        return

        :param cursor: Database cursor
        :param user: ID of current user
        :param values: Dictionary of values for customer sent by magento
        :param context: Application context. Contains the magento_website to
                        which the customer has to be linked
        :return: Browse record of record created/found
        """
        if not context.get('magento_website_id'):
            raise osv.except_osv(
                _('Not Found!'),
                _('Website does not exists in context. ')
            )

        partner = self.find_using_magento_data(cursor, user, values, context)

        if not partner:
            partner = self.create_using_magento_data(
                cursor, user, values, context
            )

        return partner

    def create_using_magento_data(self, cursor, user, values, context):
        """
        Creates record of customer values sent by magento

        :param cursor: Database cursor
        :param user: ID of current user
        :param values: Dictionary of values for customer sent by magento
        :param context: Application context. Contains the magento_website
                        to which the customer has to be linked
        :return: Browse record of record created
        """
        partner_id = self.create(
            cursor, user, {
                'name': values['firstname'],
                'magento_ids': [
                    (0, 0, {
                        'magento_id': values['customer_id'],
                        'website': context.get('magento_website_id'),
                    })
                ],
            }, context=context
        )

        return self.browse(cursor, user, partner_id, context)

    def find_using_magento_data(self, cursor, user, values, context):
        """
        Looks for the customer whose `values` are sent by magento against
        the `magento_website_id` in context.
        If record exists returns that else None

        :param cursor: Database cursor
        :param user: ID of current user
        :param values: Dictionary of values for customer sent by magento
        :param context: Application context. Contains the magento_website
                        to which the customer has to be linked
        :return: Browse record of record found
        """
        magento_partner_obj = self.pool.get('magento.website.partner')

        partner_ids = magento_partner_obj.search(
            cursor, user, [
                ('magento_id', '=', values['customer_id']),
                ('website', '=', context.get('magento_website_id'))
            ], context=context
        )
        return partner_ids and self.browse(
            cursor, user, partner_ids[0], context
        ) or None
