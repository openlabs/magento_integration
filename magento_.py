# -*- coding: UTF-8 -*-
'''
    magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
import logging
import xmlrpclib
from copy import deepcopy
import time

from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import magento

from .api import OrderConfig


_logger = logging.getLogger(__name__)


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
        ),
        order_states=fields.one2many(
            'magento.order_state', 'instance', 'Order States',
        ),
        carriers=fields.one2many(
            'magento.instance.carrier', 'instance',
            'Carriers / Shipping Methods'
        ),
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

    def import_order_states(self, cursor, user, ids, context):
        """
        Imports order states for current instance

        :param cursor: Database cursor
        :param user: Current User ID
        :param ids: Record IDs
        :param context: Application context
        """
        magento_order_state_obj = self.pool.get('magento.order_state')

        for instance in self.browse(cursor, user, ids, context):

            context.update({
                'magento_instance': instance.id
            })

            # Import order states
            with OrderConfig(
                instance.url, instance.api_user, instance.api_key
            ) as order_config_api:
                magento_order_state_obj.create_all_using_magento_data(
                    cursor, user, order_config_api.get_states(), context
                )


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
        magento_products=fields.one2many(
            'magento.website.product', 'website', 'Product',
            readonly=True
        ),
        default_product_uom=fields.many2one(
            'product.uom', 'Default Product UOM',
            help="This is used to set UOM while creating products imported "
            "from magento",
        ),
        magento_root_category_id=fields.integer(
            'Magento Root Category ID', required=True,
        )
    )

    _defaults = dict(
        magento_root_category_id=lambda *a: 1,
    )

    _sql_constraints = [(
        'magento_id_instance_unique', 'unique(magento_id, instance)',
        'A website must be unique in an instance'
    )]

    def get_default_uom(self, cursor, user, context):
        """
        Get default product uom for website.

        :param cursor: Database cursor
        :param user: ID of current user
        :param context: Application context
        :return: UOM browse record
        """
        website = self.browse(
            cursor, user, context['magento_website'], context=context
        )

        if not website.default_product_uom:
            raise osv.except_osv(
                _('UOM not found!'),
                _('Please define Default Product UOM for website %s') %
                website.name,
            )

        return website.default_product_uom

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

    def import_catalog(self, cursor, user, ids=None, context=None):
        """
        Import catalog from magento on cron

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: list of store_view ids
        :param context: dictionary of application context data
        """
        import_catalog_wiz_obj = self.pool.get(
            'magento.instance.import_catalog'
        )

        if not ids:
            ids = self.search(cursor, user, [], context)

        for website in self.browse(cursor, user, ids, context):
            if not website.instance.active:
                continue

            if context:
                context['active_id'] = website.id
            else:
                context = {'active_id': website.id}
            import_catalog_wiz = import_catalog_wiz_obj.create(
                cursor, user, {}, context=context
            )
            import_catalog_wiz_obj.import_catalog(
                cursor, user, [import_catalog_wiz], context
            )

    def export_inventory(self, cursor, user, ids=None, context=None):
        """
        Exports inventory stock information to magento

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of website
        :param context: Application context
        """
        if not ids:
            ids = self.search(cursor, user, [], context)

        for website in self.browse(cursor, user, ids, context):
            self.export_inventory_to_magento(
                cursor, user, website, context
            )

    def export_inventory_to_magento(
        self, cursor, user, website, context
    ):
        """
        Exports stock data of products from openerp to magento for this
        website

        :param cursor: Database cursor
        :param user: ID of current user
        :param website: Browse record of website
        :param context: Application context
        :return: List of products
        """
        products = []
        instance = website.instance
        for magento_product in website.magento_products:
            products.append(magento_product.product)

            is_in_stock = '1' if magento_product.product.qty_available > 0 \
                else '0'

            product_data = {
                'qty': magento_product.product.qty_available,
                'is_in_stock': is_in_stock,
            }

            # Update stock information to magento
            with magento.Inventory(
                instance.url, instance.api_user, instance.api_key
            ) as inventory_api:
                inventory_api.update(
                    magento_product.magento_id, product_data
                )

        return products


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
        price_tiers=fields.one2many(
            'magento.store.price_tier', 'store', 'Price Tiers'
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

    def export_tier_prices_to_magento(
        self, cursor, user, store, context
    ):
        """
        Exports tier prices of products from openerp to magento for this store

        :param cursor: Database cursor
        :param user: ID of current user
        :param store: Browse record of store
        :param context: Application context
        :return: List of products
        """
        pricelist_obj = self.pool.get('product.pricelist')

        products = []
        instance = store.website.instance
        for magento_product in store.website.magento_products:
            products.append(magento_product.product)

            price_tiers = magento_product.product.price_tiers or \
                store.price_tiers

            price_data = []
            for tier in price_tiers:
                if hasattr(tier, 'product'):
                    # The price tier comes from a product, then it has a
                    # function field for price, we use it directly
                    price = tier.price
                else:
                    # The price tier comes from the default tiers on store,
                    # we donr have a product on tier, so we use the current
                    # product in loop for computing the price for this tier
                    price = pricelist_obj.price_get(
                        cursor, user, [store.shop.pricelist_id.id],
                        magento_product.product.id,
                        tier.quantity, context={
                            'uom': store.website.default_product_uom.id
                        }
                    )[store.shop.pricelist_id.id]

                price_data.append({
                    'qty': tier.quantity,
                    'price': price,
                })

            # Update stock information to magento
            with magento.ProductTierPrice(
                instance.url, instance.api_user, instance.api_key
            ) as tier_price_api:
                tier_price_api.update(
                    magento_product.magento_id, price_data
                )

        return products


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
        last_shipment_export_time=fields.datetime('Last Shipment Export Time'),
        export_tracking_information=fields.boolean(
            'Export tracking information', help='Checking this will make sure'
            ' that only the done shipments which have a carrier and tracking '
            'reference are exported. This will update carrier and tracking '
            'reference on magento for the exported shipments as well.'
        )
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
        magento_state_obj = self.pool.get('magento.order_state')

        instance = store_view.instance
        if context:
            new_context = deepcopy(context)
        else:
            new_context = {}

        new_context.update({
            'magento_instance': instance.id,
            'magento_website': store_view.website.id,
            'magento_store_view': store_view.id,
        })
        new_sales = []

        order_states = magento_state_obj.search(cursor, user, [
            ('instance', '=', instance.id),
            ('use_for_import', '=', True)
        ])
        order_states_to_import_in = [
            state.code for state in magento_state_obj.browse(
                cursor, user, order_states, context=context
            )
        ]

        if not order_states_to_import_in:
            raise osv.except_osv(
                _('Order States Not Found!'),
                _(
                    'No order states found for importing orders! '
                    'Please configure the order states on magento instance'
                )
            )

        with magento.Order(
            instance.url, instance.api_user, instance.api_key
        ) as order_api:
            # Filter orders with date and store_id using list()
            # then get info of each order using info()
            # and call find_or_create_using_magento_data on sale
            filter = {
                'store_id': {'=': store_view.magento_id},
                'state': {'in': order_states_to_import_in},
            }
            if store_view.last_order_import_time:
                filter.update({
                    'updated_at': {'gteq': store_view.last_order_import_time},
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

    def export_shipment_status(self, cursor, user, ids=None, context=None):
        """
        Export Shipment status for shipments related to current store view.
        This method is called by cron.

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of store_view ids
        :param context: Dictionary of application context
        """
        if not ids:
            ids = self.search(cursor, user, [], context)

        for store_view in self.browse(cursor, user, ids, context):
            # Set the instance in context
            if context:
                context['magento_instance'] = store_view.instance.id
            else:
                context = {
                    'magento_instance': store_view.instance.id
                }

            self.export_shipment_status_to_magento(
                cursor, user, store_view, context
            )

    def export_shipment_status_to_magento(
        self, cursor, user, store_view, context
    ):
        """
        Exports shipment status for shipments to magento, if they are shipped

        :param cursor: Database cursor
        :param user: ID of current user
        :param store_view: Browse record of Store View
        :param context: Dictionary of application context
        :return: List of browse record of shipment
        """
        shipment_obj = self.pool.get('stock.picking')
        instance_obj = self.pool.get('magento.instance')

        instance = instance_obj.browse(
            cursor, user, context['magento_instance'], context
        )

        domain = [
            ('sale_id', '!=', None),
            ('sale_id.magento_store_view', '=', store_view.id),
            ('state', '=', 'done'),
            ('sale_id.magento_id', '!=', None),
            ('is_tracking_exported_to_magento', '=', False),
        ]

        if store_view.last_shipment_export_time:
            domain.append(
                ('write_date', '>=', store_view.last_shipment_export_time)
            )

        if store_view.export_tracking_information:
            domain.extend([
                ('carrier_tracking_ref', '!=', None),
                ('carrier_id', '!=', None),
            ])

        shipment_ids = shipment_obj.search(
            cursor, user, domain, context=context
        )
        shipments = []
        if not shipment_ids:
            raise osv.except_osv(
                _('Shipments Not Found!'),
                _(
                    'Seems like there are no shipments to be exported '
                    'for the orders in this store view'
                )
            )

        for shipment in shipment_obj.browse(
            cursor, user, shipment_ids, context
        ):
            shipments.append(shipment)
            increment_id = shipment.sale_id.name[
                len(instance.order_prefix): len(shipment.sale_id.name)
            ]

            try:
                # FIXME This method expects the shipment to be made for all
                # products in one picking. Split shipments is not supported yet
                with magento.Shipment(
                    instance.url, instance.api_user, instance.api_key
                ) as shipment_api:
                    shipment_increment_id = shipment_api.create(
                        order_increment_id=increment_id, items_qty={}
                    )
                    shipment_obj.write(
                        cursor, user, shipment.id, {
                            'magento_increment_id': shipment_increment_id,
                        }, context=context
                    )

                    # Rebrowse the record
                    shipment = shipment_obj.browse(
                        cursor, user, shipment.id, context=context
                    )
                    if store_view.export_tracking_information:
                        self.export_tracking_info_to_magento(
                            cursor, user, shipment, context
                        )
            except xmlrpclib.Fault, fault:
                if fault.faultCode == 102:
                    # A shipment already exists for this order, log this
                    # detail and continue
                    _logger.info(
                        'Shipment for sale %s already exists on magento'
                        % shipment.sale_id.name
                    )
                    continue

        self.write(cursor, user, store_view.id, {
            'last_shipment_export_time': time.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT
            )
        }, context=context)

        return shipments

    def export_tracking_info_to_magento(
        self, cursor, user, shipment, context
    ):
        """
        Export tracking info to magento for the specified shipment.

        :param cursor: Database cursor
        :param user: ID of current user
        :param shipment: Browse record of shipment
        :param context: Dictionary of application context
        :return: Shipment increment ID
        """
        magento_carrier_obj = self.pool.get('magento.instance.carrier')
        instance_obj = self.pool.get('magento.instance')
        picking_obj = self.pool.get('stock.picking')

        instance = instance_obj.browse(
            cursor, user, context['magento_instance'], context
        )

        carriers = magento_carrier_obj.search(
            cursor, user, [
                ('instance', '=', instance.id),
                ('carrier', '=', shipment.carrier_id.id)
            ], context=context
        )

        if not carriers:
            _logger.error(
                'No matching carrier has been configured on instance %s'
                ' for the magento carrier/shipping method %s'
                % (instance.name, shipment.carrier_id.name)
            )
            return

        carrier = magento_carrier_obj.browse(
            cursor, user, carriers[0], context
        )

        # Add tracking info to the shipment on magento
        with magento.Shipment(
            instance.url, instance.api_user, instance.api_key
        ) as shipment_api:
            shipment_increment_id = shipment_api.addtrack(
                shipment.magento_increment_id,
                carrier.code,
                carrier.title,
                shipment.carrier_tracking_ref,
            )

            picking_obj.write(
                cursor, user, shipment.id, {
                    'is_tracking_exported_to_magento': True
                }, context=context
            )

        return shipment_increment_id


class StorePriceTier(osv.Model):
    """Price Tiers for store

    This model stores the default price tiers to be used while sending
    tier prices for a product from OpenERP to Magento.
    The product also has a similar table like this. If there are no entries in
    the table on product, then these tiers are used.
    """
    _name = 'magento.store.price_tier'
    _description = 'Price Tiers for store'

    _columns = dict(
        store=fields.many2one(
            'magento.website.store', 'Magento Store', required=True,
            readonly=True,
        ),
        quantity=fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoS'),
            required=True
        ),
    )

    _sql_constraints = [
        ('store_quantity_unique', 'unique(store, quantity)',
         'Quantity in price tiers must be unique for a store'),
    ]
