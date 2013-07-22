# -*- coding: utf-8 -*-
"""
    export_catalog

    Exports Catalog

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
import magento
from openerp.osv import osv, fields
from openerp.tools.translate import _


class ExportCatalog(osv.TransientModel):
    "Export Catalog"
    _name = 'magento.instance.website.export_catalog'
    _description = __doc__

    def get_attribute_sets(self, cursor, user, context=None):
        """Get the list of attribute sets from magento for the current website's
        instance

        :param cursor: Database cursor
        :param user: ID of current user
        :param context: Application context
        :return: Tuple of attribute sets where each tuple consists of (ID, Name)
        """
        website_obj = self.pool.get('magento.instance.website')

        if not context.get('active_id'):
            return []

        website = website_obj.browse(
            cursor, user, context['active_id'], context
        )
        instance = website.instance

        with magento.ProductAttributeSet(
            instance.url, instance.api_user, instance.api_key
        ) as attribute_set_api:
            attribute_sets = attribute_set_api.list()

        return [(
            attribute_set['set_id'], attribute_set['name']
        ) for attribute_set in attribute_sets]

    _columns = dict(
        category=fields.many2one(
            'product.category', 'Magento Category', required=True,
            domain=[('magento_ids', '!=', None)],
        ),
        products=fields.many2many(
            'product.product', 'website_product_rel', 'website', 'product',
            'Products', required=True, domain=[('magento_ids', '=', None)],
        ),
        attribute_set=fields.selection(
            get_attribute_sets, 'Attribute Set', required=True,
        )
    )

    def export_catalog(self, cursor, user, ids, context):
        """
        Export the products selected to the selected category for this website

        :param cursor: Database cursor
        :param user: ID of current user
        :param ids: List of ids of records for this model
        :param context: Application context
        """
        website_obj = self.pool.get('magento.instance.website')
        product_obj = self.pool.get('product.product')

        website = website_obj.browse(
            cursor, user, context['active_id'], context
        )

        record = self.browse(cursor, user, ids[0], context=context)

        context.update({
            'magento_website': website.id,
            'magento_attribute_set': record.attribute_set,
        })
        for product in record.products:
            product_obj.export_to_magento(
                cursor, user, product, record.category, context=context
            )

        return self.open_products(
            cursor, user, ids, map(int, record.products), context
        )

    def open_products(self, cursor, user, ids, product_ids, context):
        """
        Opens view for products exported to current website

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
            'name': _('Products exported to magento'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'product.product',
            'views': [(tree_id, 'tree')],
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', product_ids)]
        }
