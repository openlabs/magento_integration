# -*- coding: utf-8 -*-
"""
    import_catalog

    Import catalog

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from magento.catalog import Category, Product
from openerp.osv import osv
from openerp.tools.translate import _


class ImportCatalog(osv.TransientModel):
    "Import catalog"
    _name = 'magento.instance.import_catalog'

    def import_catalog(self, cursor, user, ids, context):
        """
        Import the product categories and products

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of records for this model
        :param context: Application context
        """
        Pool = self.pool
        website_obj = Pool.get('magento.instance.website')

        website = website_obj.browse(
            cursor, user, context['active_id'], context
        )

        self.import_category_tree(cursor, user, website, context)
        product_ids = self.import_products(cursor, user, website, context)

        return self.open_products(
            cursor, user, ids, product_ids, context
        )

    def import_category_tree(self, cursor, user, website, context):
        """
        Imports category tree

        :param cursor: Database cursor
        :param user: ID of current user
        :param website: Browse record of website
        :param context: Application context
        """
        category_obj = self.pool.get('product.category')

        instance = website.instance
        context.update({
            'magento_instance': instance.id
        })

        with Category(
            instance.url, instance.api_user, instance.api_key
        ) as category_api:
            category_tree = category_api.tree(website.magento_root_category_id)

            category_obj.create_tree_using_magento_data(
                cursor, user, category_tree, context
            )

    def import_products(self, cursor, user, website, context):
        """
        Imports products for current instance

        :param cursor: Database cursor
        :param user: ID of current user
        :param website: Browse record of website
        :param context: Application context
        :return: List of product IDs
        """
        product_obj = self.pool.get('product.product')

        instance = website.instance

        with Product(
            instance.url, instance.api_user, instance.api_key
        ) as product_api:
            mag_products = []
            products = []

            # Products are linked to websites. But the magento api filters
            # the products based on store views. The products available on
            # website are always available on all of its store views.
            # So we get one store view for each website in current instance.
            mag_products.extend(
                product_api.list(
                    store_view=website.stores[0].store_views[0].magento_id
                )
            )
            context.update({
                'magento_website': website.id
            })

            for mag_product in mag_products:
                products.append(
                    product_obj.find_or_create_using_magento_id(
                        cursor, user, mag_product['product_id'], context,
                    )
                )
        return map(int, products)

    def open_products(self, cursor, user, ids, product_ids, context):
        """
        Opens view for products for current instance

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of records for this model
        :param product_ids: List or product IDs
        :param context: Application context
        :return: View for products
        """
        ir_model_data = self.pool.get('ir.model.data')

        tree_res = ir_model_data.get_object_reference(
            cursor, user, 'product', 'product_product_tree_view'
        )
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Magento Instance Products'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'product.product',
            'views': [(tree_id, 'tree')],
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', product_ids)]
        }

ImportCatalog()
