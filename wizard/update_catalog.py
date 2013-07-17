# -*- coding: utf-8 -*-
"""
    update_catalog

    Update catalog

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv
from openerp.tools.translate import _


class UpdateCatalog(osv.TransientModel):
    "Update catalog"
    _name = 'magento.instance.update_catalog'

    def update_catalog(self, cursor, user, ids, context):
        """
        Update the already imported products

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

        product_ids = self.update_products(cursor, user, website, context)

        return self.open_products(
            cursor, user, ids, product_ids, context
        )

    def update_products(self, cursor, user, website, context):
        """
        Updates products for current website

        :param cursor: Database cursor
        :param user: ID of current user
        :param website: Browse record of website
        :param context: Application context
        :return: List of product IDs
        """
        product_obj = self.pool.get('product.product')

        context.update({
            'magento_website': website.id
        })

        products = []
        for mag_product in website.magento_products:
            products.append(
                product_obj.update_from_magento(
                    cursor, user, mag_product.product, context=context
                )
            )

        return map(int, products)

    def open_products(self, cursor, user, ids, product_ids, context):
        """
        Opens view for products for current website

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of records for this model
        :param product_ids: List or product IDs
        :param context: Application context
        :return: View for products
        """
        ir_model_data = self.pool.get('ir.model.data')

        model, tree_id = ir_model_data.get_object_reference(
            cursor, user, 'product', 'product_product_tree_view'
        )

        return {
            'name': _('Products Updated from magento'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'product.product',
            'views': [(tree_id, 'tree')],
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', product_ids)]
        }

UpdateCatalog()
