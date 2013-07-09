# -*- coding: utf-8 -*-
"""
    export_inventory

    Exports Inventory

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv
from openerp.tools.translate import _


class ExportInventory(osv.TransientModel):
    "Export Inventory"
    _name = 'magento.instance.website.export_inventory'

    def export_inventory(self, cursor, user, ids, context):
        """
        Export product stock information to magento for the current website

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of records for this model
        :param context: Application context
        :return: View for products
        """
        website_obj = self.pool.get('magento.instance.website')

        website = website_obj.browse(
            cursor, user, context.get('active_id'), context
        )

        products = website_obj.export_inventory_to_magento(
            cursor, user, website, context
        )

        return self.open_products(cursor, user, map(int, products), context)

    def open_products(self, cursor, user, product_ids, context):
        """
        Open view for products for current website

        :param cursor: Database cursor
        :param user: ID of current user
        :param product_ids: List of product ids
        :param context: Application context
        :return: Tree view for products
        """
        ir_model_data = self.pool.get('ir.model.data')

        tree_res = ir_model_data.get_object_reference(
            cursor, user, 'product', 'product_product_tree_view'
        )
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Products that have been exported to Magento'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.product',
            'views': [(tree_id, 'tree')],
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', product_ids)]
        }
