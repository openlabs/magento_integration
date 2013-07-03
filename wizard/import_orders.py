# -*- coding: utf-8 -*-
"""
    import_orders

    Import orders

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv
from openerp.tools.translate import _


class ImportOrders(osv.TransientModel):
    "Import orders"
    _name = 'magento.store.store_view.import_orders'

    def import_orders(self, cursor, user, ids, context):
        """
        Import sale orders from magento for the current store view.

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of records for this model
        :param context: Application context
        """
        store_view_obj = self.pool.get('magento.store.store_view')

        store_view = store_view_obj.browse(
            cursor, user, context.get('active_id')
        )

        sales = store_view_obj.import_orders_from_store_view(
            cursor, user, store_view, context
        )

        return self.open_sales(cursor, user, map(int, sales), context)

    def open_sales(self, cursor, user, sale_ids, context):
        """
        Open view for sales imported from the magento store view

        :param cursor: Database cursor
        :param user: ID of current user
        :param sale_ids: List of sale ids
        :param context: Application context
        :return: Tree view for sales
        """
        ir_model_data = self.pool.get('ir.model.data')

        tree_res = ir_model_data.get_object_reference(
            cursor, user, 'sale', 'view_order_tree'
        )
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Magento Sale Orders'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'sale.order',
            'views': [(tree_id, 'tree')],
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', sale_ids)]
        }
