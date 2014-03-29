# -*- coding: UTF-8 -*-
'''
    magento

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
import magento
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class Category(osv.Model):
    """Product Category
    """
    _inherit = 'product.category'

    _columns = dict(
        magento_ids=fields.one2many(
            'magento.instance.product_category', 'category',
            string='Magento IDs',
        ),
    )

    def create_tree_using_magento_data(
        self, cursor, user, category_tree, context
    ):
        """Create the categories from the category tree

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_tree: Category Tree from magento
        :param context: Application context
        """
        # Create the root
        root_categ = self.find_or_create_using_magento_data(
            cursor, user, category_tree, context=context
        )
        for child in category_tree['children']:
            self.find_or_create_using_magento_data(
                cursor, user, child, parent=root_categ.id, context=context
            )
            if child['children']:
                self.create_tree_using_magento_data(
                    cursor, user, child, context
                )

    def find_or_create_using_magento_data(
        self, cursor, user, category_data, parent=None, context=None
    ):
        """Find or Create category using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_data: Category Data from magento
        :param parent: openerp ID of parent if present else None
        :param context: Application context
        :returns: Browse record of category found/created
        """
        category = self.find_using_magento_data(
            cursor, user, category_data, context
        )
        if not category:
            category = self.create_using_magento_data(
                cursor, user, category_data, parent, context
            )

        return category

    def find_or_create_using_magento_id(
        self, cursor, user, magento_id, parent=None, context=None
    ):
        """Find or Create category using magento ID of category

        :param cursor: Database cursor
        :param user: ID of current user
        :param magento_id: Category ID from magento
        :param parent: openerp ID of parent if present else None
        :param context: Application context
        :returns: Browse record of category found/created
        """
        instance_obj = self.pool.get('magento.instance')

        category = self.find_using_magento_id(
            cursor, user, magento_id, context
        )
        if not category:
            instance = instance_obj.browse(
                cursor, user, context['magento_instance'], context=context
            )

            with magento.Category(
                instance.url, instance.api_user, instance.api_key
            ) as category_api:
                category_data = category_api.info(magento_id)

            category = self.create_using_magento_data(
                cursor, user, category_data, parent, context
            )

        return category

    def find_using_magento_data(
        self, cursor, user, category_data, context=None
    ):
        """Find category using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_data: Category Data from magento
        :param context: Application context
        :returns: Browse record of category found or None
        """
        magento_category_obj = self.pool.get(
            'magento.instance.product_category'
        )
        record_ids = magento_category_obj.search(cursor, user, [
            ('magento_id', '=', int(category_data['category_id'])),
            ('instance', '=', context['magento_instance'])
        ], context=context)
        return record_ids and magento_category_obj.browse(
            cursor, user, record_ids[0], context=context
        ).category or None

    def find_using_magento_id(
        self, cursor, user, magento_id, context=None
    ):
        """Find category using magento id or category

        :param cursor: Database cursor
        :param user: ID of current user
        :param magento_id: Category ID from magento
        :param context: Application context
        :returns: Browse record of category found or None
        """
        magento_category_obj = self.pool.get(
            'magento.instance.product_category'
        )
        record_ids = magento_category_obj.search(cursor, user, [
            ('magento_id', '=', magento_id),
            ('instance', '=', context['magento_instance'])
        ], context=context)
        return record_ids and magento_category_obj.browse(
            cursor, user, record_ids[0], context=context
        ).category or None

    def create_using_magento_data(
        self, cursor, user, category_data, parent=None, context=None
    ):
        """Create category using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param category_data: Category Data from magento
        :param parent: openerp ID of parent if present else None
        :param context: Application context
        :returns: Browse record of category created
        """
        category_id = self.create(cursor, user, {
            'name': category_data['name'],
            'parent_id': parent,
            'magento_ids': [(0, 0, {
                'magento_id': int(category_data['category_id']),
                'instance': context['magento_instance'],
            })]
        }, context=context)

        return self.browse(cursor, user, category_id, context=context)


class MagentoInstanceCategory(osv.Model):
    """Magento Instance - Product category store

    This model keeps a record of a category's association with an instance and
    the ID of category on that instance
    """
    _name = 'magento.instance.product_category'
    _description = 'Magento Instance - Product category store'

    _columns = dict(
        magento_id=fields.integer(
            'Magento ID', required=True, select=True,
        ),
        instance=fields.many2one(
            'magento.instance', 'Magento Instance', readonly=True,
            select=True, required=True
        ),
        category=fields.many2one(
            'product.category', 'Product Category', readonly=True,
            required=True, select=True
        )
    )

    _sql_constraints = [
        (
            'magento_id_instance_unique',
            'unique(magento_id, instance)',
            'Each category in an instance must be unique!'
        ),
    ]


class Product(osv.Model):
    """Product
    """
    _inherit = 'product.product'

    _columns = dict(
        magento_product_type=fields.selection([
            ('simple', 'Simple'),
            ('configurable', 'Configurable'),
            ('grouped', 'Grouped'),
            ('bundle', 'Bundle'),
            ('virtual', 'Virtual'),
            ('downloadable', 'Downloadable'),
        ], 'Magento Product type', readonly=True),
        magento_ids=fields.one2many(
            'magento.website.product', 'product',
            string='Magento IDs',
        ),
        price_tiers=fields.one2many(
            'product.price_tier', 'product', string='Price Tiers'
        ),
    )

    def find_or_create_using_magento_id(
        self, cursor, user, magento_id, context
    ):
        """
        Find or create product using magento_id

        :param cursor: Database cursor
        :param user: ID of current user
        :param magento_id: Product ID from magento
        :param context: Application context
        :returns: Browse record of product found/created
        """
        website_obj = self.pool.get('magento.instance.website')

        product = self.find_using_magento_id(
            cursor, user, magento_id, context
        )
        if not product:
            # If product is not found, get the info from magento and delegate
            # to create_using_magento_data
            website = website_obj.browse(
                cursor, user, context['magento_website'], context=context
            )

            instance = website.instance
            with magento.Product(
                instance.url, instance.api_user, instance.api_key
            ) as product_api:
                product_data = product_api.info(magento_id)

            product = self.create_using_magento_data(
                cursor, user, product_data, context
            )

        return product

    def find_using_magento_id(self, cursor, user, magento_id, context):
        """
        Finds product using magento id

        :param cursor: Database cursor
        :param user: ID of current user
        :param magento_id: Product ID from magento
        :param context: Application context
        :returns: Browse record of product found
        """
        magento_product_obj = self.pool.get('magento.website.product')

        record_ids = magento_product_obj.search(
            cursor, user, [
                ('magento_id', '=', magento_id),
                ('website', '=', context['magento_website'])
            ], context=context
        )

        return record_ids and magento_product_obj.browse(
            cursor, user, record_ids[0], context=context
        ).product or None

    def find_or_create_using_magento_data(
        self, cursor, user, product_data, context=None
    ):
        """Find or Create product using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param product_data: Product Data from magento
        :param context: Application context
        :returns: Browse record of product found/created
        """
        product = self.find_using_magento_data(
            cursor, user, product_data, context
        )
        if not product:
            product = self.create_using_magento_data(
                cursor, user, product_data, context
            )

        return product

    def find_using_magento_data(
        self, cursor, user, product_data, context=None
    ):
        """Find product using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param product_data: Category Data from magento
        :param context: Application context
        :returns: Browse record of product found or None
        """
        magento_product_obj = self.pool.get('magento.website.product')
        record_ids = magento_product_obj.search(cursor, user, [
            ('magento_id', '=', int(product_data['product_id'])),
            ('website', '=', context['magento_website'])
        ], context=context)
        return record_ids and magento_product_obj.browse(
            cursor, user, record_ids[0], context=context
        ).product or None

    def update_catalog(self, cursor, user, ids=None, context=None):
        """
        Updates catalog from magento to openerp

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of website
        :param context: Application context
        """
        if not ids:
            ids = self.search(cursor, user, [], context)

        for product in self.browse(cursor, user, ids, context):
            self.update_from_magento(
                cursor, user, product, context
            )

    def update_from_magento(
        self, cursor, user, product, context=None
    ):
        """Update product using magento ID for that product

        :param cursor: Database cursor
        :param user: ID of current user
        :param product: Browse record of product to be updated
        :param context: Application context
        :returns: Browse record of product updated
        """
        website_obj = self.pool.get('magento.instance.website')
        magento_product_obj = self.pool.get('magento.website.product')

        website = website_obj.browse(
            cursor, user, context['magento_website'], context=context
        )
        instance = website.instance

        with magento.Product(
            instance.url, instance.api_user, instance.api_key
        ) as product_api:
            magento_product_id, = magento_product_obj.search(
                cursor, user, [
                    ('product', '=', product.id),
                    ('website', '=', website.id),
                ], context=context
            )
            magento_product = magento_product_obj.browse(
                cursor, user, magento_product_id, context=context
            )
            product_data = product_api.info(magento_product.magento_id)

        return self.update_from_magento_using_data(
            cursor, user, product, product_data, context
        )

    def extract_product_values_from_data(self, product_data):
        """Extract product values from the magento data
        These values are used for creation/updation of product

        :param product_data: Product Data from magento
        :return: Dictionary of values
        """
        return {
            'name': product_data['name'],
            'default_code': product_data['sku'],
            'description': product_data['description'],
            'list_price': float(
                product_data.get('special_price') or
                product_data.get('price') or 0.00
            ),
        }

    def update_from_magento_using_data(
        self, cursor, user, product, product_data, context=None
    ):
        """Update product using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param product: Browse record of product to be updated
        :param product_data: Product Data from magento
        :param context: Application context
        :returns: Browse record of product updated
        """
        product_values = self.extract_product_values_from_data(product_data)
        self.write(cursor, user, product.id, product_values, context=context)

        # Rebrowse the record
        product = self.browse(cursor, user, product.id, context=context)

        return product

    def create_using_magento_data(
        self, cursor, user, product_data, context=None
    ):
        """Create product using magento data

        :param cursor: Database cursor
        :param user: ID of current user
        :param product_data: Product Data from magento
        :param context: Application context
        :returns: Browse record of product created
        """
        category_obj = self.pool.get('product.category')
        website_obj = self.pool.get('magento.instance.website')

        # Get only the first category from list of categories
        # If not category is found, put product under unclassified category
        # which is created by default data
        if product_data.get('categories'):
            category_id = category_obj.find_or_create_using_magento_id(
                cursor, user, int(product_data['categories'][0]),
                context=context
            ).id
        else:
            category_id, = category_obj.search(cursor, user, [
                ('name', '=', 'Unclassified Magento Products')
            ], context=context)

        product_values = self.extract_product_values_from_data(product_data)
        product_values.update({
            'categ_id': category_id,
            'uom_id':
                website_obj.get_default_uom(
                    cursor, user, context
                ).id,
            'magento_product_type': product_data['type'],
            'procure_method': product_values.get(
                'procure_method', 'make_to_order'
            ),
            'magento_ids': [(0, 0, {
                'magento_id': int(product_data['product_id']),
                'website': context['magento_website'],
            })]
        })

        if product_data['type'] == 'bundle':
            # Bundles are produced
            product_values['supply_method'] = 'produce'

        product_id = self.create(cursor, user, product_values, context=context)

        return self.browse(cursor, user, product_id, context=context)

    def get_product_values_for_export_to_magento(
        self, product, categories, websites, context
    ):
        """Creates a dictionary of values which have to exported to magento for
        creating a product

        :param product: Browse record of product
        :param categories: List of Browse record of categories
        :param websites: List of Browse record of websites
        :param context: Application context
        """
        return {
            'categories': map(
                lambda mag_categ: mag_categ.magento_id,
                categories[0].magento_ids
            ),
            'websites': map(lambda website: website.magento_id, websites),
            'name': product.name,
            'description': product.description or product.name,
            'short_description': product.description or product.name,
            'status': '1',
            'weight': product.weight_net,
            'visibility': '4',
            'price': product.lst_price,
            'tax_class_id': '1',
        }

    def export_to_magento(self, cursor, user, product, category, context):
        """Export the given `product` to the magento category corresponding to
        the given `category` under the current website in context

        :param cursor: Database cursor
        :param user: ID of current user
        :param product: Browserecord of product to be exported
        :param category: Browserecord of category to which the product has
                         to be exported
        :param context: Application context
        :return: Browserecord of product
        """
        website_obj = self.pool.get('magento.instance.website')
        website_product_obj = self.pool.get('magento.website.product')

        if not category.magento_ids:
            raise osv.except_osv(
                _('Invalid Category!'),
                _('Category %s must have a magento category associated') %
                category.complete_name,
            )

        if product.magento_ids:
            raise osv.except_osv(
                _('Invalid Product!'),
                _('Product %s already has a magento product associated') %
                product.name,
            )

        if not product.default_code:
            raise osv.except_osv(
                _('Invalid Product!'),
                _('Product %s has a missing code.') %
                product.name,
            )

        website = website_obj.browse(
            cursor, user, context['magento_website'], context=context
        )
        instance = website.instance

        with magento.Product(
            instance.url, instance.api_user, instance.api_key
        ) as product_api:
            # We create only simple products on magento with the default
            # attribute set
            # TODO: We have to call the method from core API extension
            # because the method for catalog create from core API does not seem
            # to work. This should ideally be from core API rather than
            # extension
            magento_id = product_api.call(
                'ol_catalog_product.create', [
                    'simple',
                    int(context['magento_attribute_set']),
                    product.default_code,
                    self.get_product_values_for_export_to_magento(
                        product, [category], [website], context
                    )
                ]
            )
            website_product_obj.create(cursor, user, {
                'magento_id': magento_id,
                'website': context['magento_website'],
                'product': product.id,
            }, context=context)
            self.write(cursor, user, product.id, {
                'magento_product_type': 'simple'
            }, context=context)
        return product


class MagentoWebsiteProduct(osv.Model):
    """Magento Website - Product store

    This model keeps a record of a product's association with a website and
    the ID of product on that website
    """
    _name = 'magento.website.product'
    _description = 'Magento Website - Product store'

    _columns = dict(
        magento_id=fields.integer(
            'Magento ID', required=True, select=True,
        ),
        website=fields.many2one(
            'magento.instance.website', 'Magento Website', readonly=True,
            select=True, required=True
        ),
        product=fields.many2one(
            'product.product', 'Product', readonly=True,
            required=True, select=True
        )
    )

    _sql_constraints = [
        (
            'magento_id_website_unique',
            'unique(magento_id, website)',
            'Each product in a website must be unique!'
        ),
    ]

    def update_product_from_magento(self, cursor, user, ids, context):
        """Update the product from magento with the details from magento
        for the current website

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: Record IDs
        :param context: Application context
        """
        product_obj = self.pool.get('product.product')

        for record in self.browse(cursor, user, ids, context=context):
            context.update({
                'magento_website': record.website.id,
            })
            product_obj.update_from_magento(
                cursor, user, record.product, context
            )

        return {}


class ProductPriceTier(osv.Model):
    """Price Tiers for product

    This model stores the price tiers to be used while sending
    tier prices for a product from OpenERP to Magento.
    """
    _name = 'product.price_tier'
    _description = 'Price Tiers for product'
    _rec_name = 'quantity'

    def get_price(self, cursor, user, ids, name, _, context):
        """Calculate the price of the product for quantity set in record

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: Records IDs
        :param name: Nameo of field
        :param context: Application context
        """
        pricelist_obj = self.pool.get('product.pricelist')
        store_obj = self.pool.get('magento.website.store')

        res = {}

        if not context.get('magento_store'):
            return res

        for tier in self.browse(cursor, user, ids, context=context):
            store = store_obj.browse(
                cursor, user, context['magento_store'], context=context
            )
            res[tier.id] = pricelist_obj.price_get(
                cursor, user, [store.shop.pricelist_id.id], tier.product.id,
                tier.quantity, context={
                    'uom': store.website.default_product_uom.id
                }
            )[store.shop.pricelist_id.id]
        return res

    _columns = dict(
        product=fields.many2one(
            'product.product', 'Product', required=True,
            readonly=True,
        ),
        quantity=fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoS'),
            required=True
        ),
        price=fields.function(get_price, type='float', string='Price'),
    )

    _sql_constraints = [
        ('product_quantity_unique', 'unique(product, quantity)',
         'Quantity in price tiers must be unique for a product'),
    ]
