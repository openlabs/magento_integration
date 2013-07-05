# -*- coding: utf-8 -*-
"""
    bom

    BoM

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from openerp.osv import osv


class BoM(osv.Model):
    """Bill of material
    """
    _inherit = 'mrp.bom'

    def identify_boms(self, order_data):
        """Create a dict of bundle product data for use in creation of bom

        :param order_data: Order data sent from magento
        :return: Dictionary in format
            {
                <item_id of bundle product>: {
                    'bundle': <item data for bundle product>,
                    'components': [<item data>, <item data>]
                }
            }
        """
        bundles = {}

        # Identify all the bundles in the order
        for item in order_data['items']:
            # Iterate over each item in order items
            if item['product_type'] == 'bundle' and not item['parent_item_id']:
                # If product_type is bundle and does not have a parent(obvious)
                # then create a new entry in bundle_products
                # .. note:: item_id is the unique ID of each order line
                bundles[item['item_id']] = {'bundle': item, 'components': []}

        # Identify and add components
        for item in order_data['items']:
            if item['product_type'] != 'bundle' and \
                    'bundle_option' in item['product_options'] and \
                    item['parent_item_id']:

                bundles[item['parent_item_id']]['components'].append(item)

        return bundles

    def find_or_create_bom_for_magento_bundle(
        self, cursor, user, order_data, context
    ):
        """Find or create a BoM for bundle product from the data sent in
        magento order

        :param cursor: Database cursor
        :param user: ID of current user
        :param order_data: Order Data from magento
        :param context: Application context
        :return: Found or created BoM's browse record
        """
        uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')

        identified_boms = self.identify_boms(order_data)

        if not identified_boms:
            return

        for item_id, data in identified_boms.iteritems():
            bundle_product = product_obj.find_or_create_using_magento_id(
                cursor, user, data['bundle']['product_id'], context=context
            )
            # It contains a list of tuples, in which the first element is the
            # product browse record and second is its quantity in the BoM
            child_products = [(
                    product_obj.find_or_create_using_magento_id(
                        cursor, user, each['product_id'], context=context
                    ), (
                        float(each['qty_ordered']) /
                        float(data['bundle']['qty_ordered'])
                    )
            ) for each in data['components']]

            # Here we match the sets of BoM components for equality
            # Each set contains tuples or product id and quantity of that
            # product in the BoM
            # If everything for a BoM matches, then we dont create a new one
            # and use this BoM itself
            # XXX This might eventually have issues because of rounding
            # in quantity
            for bom in bundle_product.bom_ids:
                existing_bom_set = set([
                    (line.product_id.id, line.product_qty)
                    for line in bom.bom_lines
                ])
                new_bom_set = set([
                    (product.id, qty) for product, qty in child_products
                ])
                if existing_bom_set == new_bom_set:
                    break
            else:
                # No matching BoM found, create a new one
                unit, = uom_obj.search(
                    cursor, user, [('name', '=', 'Unit(s)')], context=context
                )
                bom_id = self.create(cursor, user, {
                    'name': bundle_product.name,
                    'code': bundle_product.default_code,
                    'type': 'phantom',
                    'product_id': bundle_product.id,
                    'product_uom': unit,
                    'bom_lines': [(0, 0, {
                        'name': product.name,
                        'code': product.default_code,
                        'product_id': product.id,
                        'product_uom': unit,
                        'product_qty': quantity,
                    }) for product, quantity in child_products]
                })
                bom = self.browse(cursor, user, bom_id, context=context)

        return bom
