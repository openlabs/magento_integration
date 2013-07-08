# -*- coding: UTF-8 -*-
'''
    magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details
'''
import magento
from openerp.osv import fields, osv


class Category(osv.Model):
    """Product Category
    """
    _inherit = 'product.category'

    _columns = dict(
        magento_ids=fields.one2many(
            'magento.instance.product_category', 'category',
            string='Magento IDs', readonly=True,
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
            'Magento ID', readonly=True, required=True, select=True,
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
            string='Magento IDs', readonly=True,
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

        product_values = {
            'name': product_data['name'],
            'categ_id': category_id,
            'default_code': product_data['sku'],
            'uom_id':
                website_obj.get_default_uom(
                    cursor, user, context
                ).id,
            'list_price': float(
                product_data.get('special_price') or
                product_data.get('price') or 0.00
            ),
            'standard_price': float(product_data.get('price') or 0.00),
            'description': product_data['description'],
            'magento_product_type': product_data['type'],
            'procure_method': 'make_to_order',
            'magento_ids': [(0, 0, {
                'magento_id': int(product_data['product_id']),
                'website': context['magento_website'],
            })]
        }

        if product_data['type'] == 'bundle':
            # Bundles are produced
            product_values['supply_method'] = 'produce'

        product_id = self.create(cursor, user, product_values, context=context)

        return self.browse(cursor, user, product_id, context=context)


class MagentoWebsiteProduct(osv.Model):
    """Magento Website - Product store

    This model keeps a record of a product's association with a website and
    the ID of product on that website
    """
    _name = 'magento.website.product'
    _description = 'Magento Website - Product store'

    _columns = dict(
        magento_id=fields.integer(
            'Magento ID', readonly=True, required=True, select=True,
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
