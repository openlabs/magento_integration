# -*- coding: UTF-8 -*-
'''
    magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
from copy import deepcopy
import time

from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import magento


class Instance(osv.Model):
    """Magento Instance

    Refers to a magento installation identifiable via url, api_user and api_key
    """
    _name = 'magento.instance'
    _description = "Magento Instance"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        url=fields.char('Magento Site URL', required=True, size=255),
        api_user=fields.char('API User', required=True, size=50),
        api_key=fields.char('API Password / Key', required=True, size=100),
        order_prefix=fields.char(
            'Sale Order Prefix', size=10, help=
            "This helps to distinguish between orders from different instances"
        ),
        active=fields.boolean('Active'),
        company=fields.many2one(
            'res.company', 'Company', required=True
        ),
        websites=fields.one2many(
            'magento.instance.website', 'instance', 'Websites',
            readonly=True,
        )
    )

    def default_company(self, cursor, user, context):
        """Return default company

        :param cursor: Database cursor
        :param user: Current User ID
        :param context: Application context
        """
        company_obj = self.pool.get('res.company')

        return company_obj._company_default_get(
            cursor, user, 'magento.instance', context=context
        )

    _defaults = dict(
        active=lambda *a: 1,
        company=default_company,
        order_prefix=lambda *a: 'mag_'
    )

    _sql_constraints = [
        ('url_unique', 'unique(url)', 'URL of an instance must be unique'),
    ]


class InstanceWebsite(osv.Model):
    """Magento Instance Website

    A magento instance can have multiple websites.
    They act as  ‘parents’ of stores. A website consists of one or more stores.
    """
    _name = 'magento.instance.website'
    _description = "Magento Instance Website"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        code=fields.char('Code', required=True, size=50, readonly=True,),
        magento_id=fields.integer('Magento ID', readonly=True,),
        instance=fields.many2one(
            'magento.instance', 'Instance', required=True,
            readonly=True,
        ),
        company=fields.related(
            'instance', 'company', type='many2one', relation='res.company',
            string='Company', readonly=True
        ),
        stores=fields.one2many(
            'magento.website.store', 'website', 'Stores',
            readonly=True,
        ),
    )

    _sql_constraints = [(
        'magento_id_instance_unique', 'unique(magento_id, instance)',
        'A website must be unique in an instance'
    )]

    def find_or_create(self, cursor, user, instance_id, values, context):
        """
        Looks for the website whose `values` are sent by magento against
        the instance with `instance_id` in openerp.
        If a record exists for this, return that else create a new one and
        return

        :param cursor: Database cursor
        :param user: ID of current user
        :param instance_id: ID of instance
        :param values: Dictionary of values for a website sent by magento
        :return: ID of record created/found
        """
        website_ids = self.search(
            cursor, user, [
                ('instance', '=', instance_id),
                ('magento_id', '=', values['website_id'])
            ], context=context
        )

        if website_ids:
            return website_ids[0]

        return self.create(
            cursor, user, {
                'name': values['name'],
                'code': values['code'],
                'instance': instance_id,
                'magento_id': values['website_id'],
            }, context=context
        )


class WebsiteStore(osv.Model):
    """Magento Website Store or Store view groups

    Stores are ‘children’ of websites. The visibility of products and
    categories is managed on magento at store level by specifying the
    root category on a store.
    """
    _name = 'magento.website.store'
    _description = "Magento Website Store"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        magento_id=fields.integer('Magento ID', readonly=True,),
        website=fields.many2one(
            'magento.instance.website', 'Website', required=True,
            readonly=True,
        ),
        shop=fields.many2one(
            'sale.shop', 'Sales Shop',
            help="Imported sales for this store will go into this shop",
        ),
        instance=fields.related(
            'website', 'instance', type='many2one',
            relation='magento.instance', string='Instance', readonly=True,
        ),
        company=fields.related(
            'website', 'company', type='many2one', relation='res.company',
            string='Company', readonly=True
        ),
        store_views=fields.one2many(
            'magento.store.store_view', 'store', 'Store Views', readonly=True,
        ),
    )

    _sql_constraints = [(
        'magento_id_website_unique', 'unique(magento_id, website)',
        'A store must be unique in a website'
    )]

    def find_or_create(self, cursor, user, website_id, values, context):
        """
        Looks for the store whose `values` are sent by magento against the
        website with `website_id` in openerp.
        If a record exists for this, return that else create a new one and
        return

        :param cursor: Database cursor
        :param user: ID of current user
        :param website_id: ID of website
        :param values: Dictionary of values for a store sent by magento
        :return: ID of record created/found
        """
        store_ids = self.search(
            cursor, user, [
                ('website', '=', website_id),
                ('magento_id', '=', values['group_id'])
            ], context=context
        )

        if store_ids:
            return store_ids[0]

        return self.create(
            cursor, user, {
                'name': values['name'],
                'magento_id': values['group_id'],
                'website': website_id,
            }, context=context
        )


class WebsiteStoreView(osv.Model):
    """Magento Website Store View

    A store needs one or more store views to be browse-able in the front-end.
    It allows for multiple presentations of a store. Most implementations
    use store views for different languages.
    """
    _name = 'magento.store.store_view'
    _description = "Magento Website Store View"

    _columns = dict(
        name=fields.char('Name', required=True, size=50),
        code=fields.char('Code', required=True, size=50, readonly=True,),
        magento_id=fields.integer('Magento ID', readonly=True,),
        last_order_import_time=fields.datetime('Last Order Import Time'),
        store=fields.many2one(
            'magento.website.store', 'Store', required=True, readonly=True,
        ),
        last_order_export_time=fields.datetime('Last Order Export Time'),
        instance=fields.related(
            'store', 'instance', type='many2one',
            relation='magento.instance', string='Instance', readonly=True,
        ),
        website=fields.related(
            'store', 'website', type='many2one',
            relation='magento.instance.website', string='Website',
            readonly=True,
        ),
        company=fields.related(
            'store', 'company', type='many2one', relation='res.company',
            string='Company', readonly=True
        ),
        shop=fields.related(
            'store', 'shop', type='many2one', relation='sale.shop',
            string='Sales Shop', readonly=True,
        ),
    )

    _sql_constraints = [(
        'magento_id_store_unique', 'unique(magento_id, store)',
        'A storeview must be unique in a store'
    )]

    def find_or_create(self, cursor, user, store_id, values, context):
        """
        Looks for the store view whose `values` are sent by magento against
        the store with `store_id` in openerp.
        If a record exists for this, return that else create a new one and
        return

        :param cursor: Database cursor
        :param user: ID of current user
        :param store_id: ID of store
        :param values: Dictionary of values for store view sent by magento
        :return: ID of record created/found
        """
        store_view_ids = self.search(
            cursor, user, [
                ('store', '=', store_id),
                ('magento_id', '=', values['store_id'])
            ], context=context
        )

        if store_view_ids:
            return store_view_ids[0]

        return self.create(
            cursor, user, {
                'name': values['name'],
                'code': values['code'],
                'store': store_id,
                'magento_id': values['store_id']
            }, context=context
        )

    def import_orders(self, cursor, user, ids=None, context=None):
        """
        Import orders from magento

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: list of store_view ids
        :param context: dictionary of application context data
        """
        if not ids:
            ids = self.search(cursor, user, [], context)

        for store_view in self.browse(cursor, user, ids, context):
            self.import_orders_from_store_view(
                cursor, user, store_view, context
            )

    def export_orders(self, cursor, user, ids=None, context=None):
        """
        Export sales orders status to magento.

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of store_view ids
        :param context: Dictionary of application context
        """
        if not ids:
            ids = self.search(cursor, user, [], context)

        for store_view in self.browse(cursor, user, ids, context):
            self.export_orders_to_magento(cursor, user, store_view, context)

    def import_orders_from_store_view(self, cursor, user, store_view, context):
        """
        Imports orders from store view

        :param cursor: Database cursor
        :param user: ID of current user
        :param store_view: browse record of store_view
        :param context: dictionary of application context data
        :return: list of sale ids
        """
        sale_obj = self.pool.get('sale.order')

        instance = store_view.instance
        new_context = deepcopy(context)
        new_context.update({
            'magento_instance': instance.id,
            'magento_website': store_view.website.id,
            'magento_store_view': store_view.id,
        })
        new_sales = []

        with magento.Order(
            instance.url, instance.api_user, instance.api_key
        ) as order_api:
            # Filter orders with date and store_id using list()
            # then get info of each order using info()
            # and call find_or_create_using_magento_data on sale
            filter = {'store_id': {'=': store_view.magento_id}}
            if store_view.last_order_import_time:
                filter.update({
                    'updated_at': {'gteq': store_view.last_order_import_time}
                })
            self.write(cursor, user, [store_view.id], {
                'last_order_import_time': time.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                )
            }, context=context)
            orders = order_api.list(filter)
            for order in orders:
                new_sales.append(
                    sale_obj.find_or_create_using_magento_data(
                        cursor, user,
                        order_api.info(order['increment_id']), new_context
                    )
                )

        return new_sales

    def export_orders_to_magento(self, cursor, user, store_view, context):
        """
        Export sale orders to magento for the current store view.
        Export only those orders which are updated after last export time.

        :param cursor: Database cursor
        :param user: ID of current user
        :param store_view: Browse record of store_view
        :param context: Dictionary of application context
        """
        sale_obj = self.pool.get('sale.order')

        exported_sales = []
        domain = [('magento_store_view', '=', store_view.id)]

        # FIXME: Shitty openerp date comparison needs some magical
        # logic to be implemented.
        # TODO: Add date comparison or write date with last_order_export_time

        order_ids = sale_obj.search(cursor, user, domain, context=context)

        self.write(cursor, user, [store_view.id], {
            'last_order_export_time': time.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT
            )
        }, context=context)
        for sale_order in sale_obj.browse(cursor, user, order_ids):
            exported_sales.append(sale_obj.export_order_status_to_magento(
                cursor, user, sale_order, context
            ))

        return exported_sales
