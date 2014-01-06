# -*- coding: utf-8 -*-
"""
    test_sale

    Test Sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from copy import deepcopy
from contextlib import nested
import unittest
import datetime
from dateutil.relativedelta import relativedelta

import magento
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from mock import patch, MagicMock
from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase, load_json
from api import OrderConfig
import settings


def mock_product_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Product)

    handle = MagicMock(spec=magento.Product)
    handle.info.side_effect = lambda id: load_json('products', str(id))
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


def mock_order_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Order)

    handle = MagicMock(spec=magento.Order)
    handle.info.side_effect = lambda id: load_json('orders', str(id))
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


def mock_customer_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Customer)

    handle = MagicMock(spec=magento.Customer)
    handle.info.side_effect = lambda id: load_json('customers', str(id))
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


def mock_shipment_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Shipment)

    handle = MagicMock(spec=magento.Shipment)
    handle.create.side_effect = lambda *args, **kwargs: 'Shipment created'
    handle.addtrack.side_effect = lambda *args, **kwargs: True
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


class TestSale(TestBase):
    """
    Tests import of sale order
    """

    def test_0005_import_sale_order_states(self):
        """Test the import and creation of sale order states for an instance
        """
        magento_order_state_obj = POOL.get('magento.order_state')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
            })

            states_before_import = magento_order_state_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            states = magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states,
                context=context
            )

            states_after_import = magento_order_state_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            self.assertTrue(states_after_import > states_before_import)

            for state in states:
                self.assertEqual(
                    state.instance.id, context['magento_instance']
                )

    def test_0006_import_sale_order_states(self):
        """
        Test the import and creation of sale order states for an instance when
        order state is unknown
        """
        magento_order_state_obj = POOL.get('magento.order_state')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
            })

            states_before_import = magento_order_state_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            states = magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, {'something': 'something'},
                context=context
            )
            states_after_import = magento_order_state_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            self.assertTrue(states_after_import > states_before_import)

            for state in states:
                self.assertEqual(
                    state.instance.id, context['magento_instance']
                )

    def test_0010_import_sale_order_with_products(self):
        """
        Tests import of sale order using magento data
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states,
                context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            orders_before_import = sale_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000001')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'], context
                    )

                # Create sale order using magento data
                with patch(
                        'magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])

                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            self.assertEqual(order.state, 'manual')

            orders_after_import = sale_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertTrue(orders_after_import > orders_before_import)

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(
                len(order.order_line), len(order_data['items']) + 1
            )

            self.assertEqual(
                order.amount_total, float(order_data['base_grand_total'])
            )

    def test_0020_find_or_create_order_using_increment_id(self):
        """
        Tests finding and creating order using increment id
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states,
                context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            orders_before_import = sale_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000001')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento increment_id
                with nested(
                    patch('magento.Product', mock_product_api(), create=True),
                    patch('magento.Order', mock_order_api(), create=True),
                ):
                    order = sale_obj.find_or_create_using_magento_increment_id(
                        txn.cursor, txn.user, order_data['increment_id'],
                        context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])

                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'],
                    context
                )
                order = sale_obj.find_or_create_using_magento_increment_id(
                    txn.cursor, txn.user, order_data['increment_id'],
                    context=context
                )

            orders_after_import = sale_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertTrue(orders_after_import > orders_before_import)

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(
                len(order.order_line), len(order_data['items']) + 1
            )
            self.assertEqual(
                order.amount_total, float(order_data['base_grand_total'])
            )

    def test_0030_import_sale_order_with_bundle_product(self):
        """
        Tests import of sale order with bundle product using magento data
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        product_obj = POOL.get('product.product')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            lines = []
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states,
                context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            orders_before_import = sale_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            if settings.MOCK:
                order_data = load_json('orders', '300000001')

                with patch(
                    'magento.Customer', mock_customer_api(), create=True
                ):
                    partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    for order in orders:
                        if filter(
                            lambda item: item['product_type'] == 'bundle',
                            order['items']
                        ):
                            order_data = order

                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            self.assertEqual(order.state, 'manual')
            self.assertTrue('bundle' in order.order_line[0].magento_notes)

            orders_after_import = sale_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertTrue(orders_after_import > orders_before_import)

            for item in order_data['items']:
                if not item['parent_item_id']:
                    lines.append(item)

                # If the product is a child product of a bundle product, do not
                # create a separate line for this.
                if 'bundle_option' in item['product_options'] and \
                        item['parent_item_id']:
                    continue

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(len(order.order_line), len(lines) + 1)

            self.assertEqual(
                order.amount_total, float(order_data['base_grand_total'])
            )

            if settings.MOCK:
                product_data = load_json('products', '158')
            else:
                with magento.Product(*settings.ARGS) as product_api:
                    product_list = product_api.list()
                    for product in product_list:
                        if product['type'] == 'simple':
                            product_data = product_api.info(
                                product=product['product_id'],
                            )

            # There should be a BoM for the bundle product
            product = product_obj.find_or_create_using_magento_id(
                txn.cursor, txn.user, product_data['product_id'], context
            )
            self.assertTrue(product.bom_ids)
            self.assertEqual(
                len(product.bom_ids[0].bom_lines), len(order.order_line)
            )

            self.assertEqual(
                len(order.picking_ids[0].move_lines), len(order.order_line)
            )

    def test_0033_import_sale_order_with_bundle_product_check_duplicate(self):
        """
        Tests import of sale order with bundle product using magento data
        This tests that the duplication of BoMs doesnot happen
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        product_obj = POOL.get('product.product')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '300000001')

                with patch(
                    'magento.Customer', mock_customer_api(), create=True
                ):
                    partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    for order in orders:
                        if filter(
                            lambda item: item['product_type'] == 'bundle',
                            order['items']
                        ):
                            order_data = order

                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                # Create sale order using magento data
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            if settings.MOCK:
                product_data = load_json('products', '158')
            else:
                with magento.Product(*settings.ARGS) as product_api:
                    product_list = product_api.list()
                    for product in product_list:
                        if product['type'] == 'bundle':
                            product_data = product_api.info(
                                product=product['product_id'],
                            )
                            break

            # There should be a BoM for the bundle product
            product = product_obj.find_or_create_using_magento_id(
                txn.cursor, txn.user, product_data['product_id'], context
            )
            self.assertTrue(product.bom_ids)
            self.assertEqual(
                len(product.bom_ids[0].bom_lines),
                len(order.order_line)
            )

            if settings.MOCK:
                order_data = load_json('orders', '300000001-a')

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    for order in orders:
                        for item in order['items']:
                            if item['product_type'] == 'bundle':
                                order_data = order
                                break

                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            # There should be a BoM for the bundle product
            product = product_obj.find_or_create_using_magento_id(
                txn.cursor, txn.user, product_data['product_id'], context
            )
            self.assertTrue(product.bom_ids)
            self.assertTrue(
                len(product.bom_ids[0].bom_lines), len(order.order_line)
            )

    def test_0036_import_sale_with_bundle_plus_child_separate(self):
        """
        Tests import of sale order with bundle product using magento data
        One of the children of the bundle is bought separately too
        Make sure that the lines are created correctly
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            lines = []
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000004')

                with patch(
                    'magento.Customer', mock_customer_api(), create=True
                ):
                    partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    for order in orders:
                        if filter(
                            lambda item: item['product_type'] == 'bundle',
                            order['items']
                        ):
                            order_data = order

                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                # Create sale order using magento data
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            self.assertEqual(
                order.amount_total, float(order_data['base_grand_total'])
            )

            for item in order_data['items']:
                if not item['parent_item_id']:
                    lines.append(item)

                # If the product is a child product of a bundle product, do not
                # create a separate line for this.
                if 'bundle_option' in item['product_options'] and \
                        item['parent_item_id']:
                    continue

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(
                len(order.order_line), len(lines) + 1
            )

    def test_0039_import_sale_with_tax(self):
        """
        Tests import of sale order with tax
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        tax_obj = POOL.get('account.tax')
        magento_order_state_obj = POOL.get('magento.order_state')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            tax_obj.create(txn.cursor, txn.user, {
                'name': 'VAT',
                'amount': float('0.20'),
                'used_on_magento': True
            })
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )
            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000005')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    for order in orders:
                        if order.get('tax_amount'):
                            order_data = order
                            break
                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                # Create sale order using magento data
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            self.assertEqual(
                order.amount_total, float(order_data['base_grand_total'])
            )

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(
                len(order.order_line), len(order_data['items']) + 1
            )

    def test_00395_import_sale_with_shipping_tax(self):
        """
        Tests import of sale order with shipping tax
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        tax_obj = POOL.get('account.tax')
        magento_order_state_obj = POOL.get('magento.order_state')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            tax_obj.create(txn.cursor, txn.user, {
                'name': 'VAT on Shipping',
                'amount': float('0.20'),
                'used_on_magento': True,
                'apply_on_magento_shipping': True,
                'price_include': True,
            })
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000057')

                with patch(
                    'magento.Customer', mock_customer_api(), create=True
                ):
                    partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'], context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    for order in orders:
                        if order.get('shipping_amount'):
                            order_data = order
                            break
                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                # Create sale order using magento data
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            self.assertEqual(
                order.amount_total, float(order_data['base_grand_total'])
            )

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(
                len(order.order_line), len(order_data['items']) + 1
            )

    def test_0040_import_carriers(self):
        """
        Test If all carriers are being imported from magento
        """
        magento_carrier_obj = POOL.get('magento.instance.carrier')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)

            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
            })

            carriers_before_import = magento_carrier_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            if settings.MOCK:
                mag_carriers = load_json('carriers', 'shipping_methods')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    mag_carriers = order_config_api.get_shipping_methods()

            carriers = magento_carrier_obj.create_all_using_magento_data(
                txn.cursor, txn.user, mag_carriers, context=context
            )
            carriers_after_import = magento_carrier_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            self.assertTrue(carriers_after_import > carriers_before_import)
            for carrier in carriers:
                self.assertEqual(
                    carrier.instance.id, context['magento_instance']
                )

    @unittest.skipIf(not settings.MOCK, "requries mock settings")
    def test_0050_export_shipment(self):
        """
        Tests if shipments status is being exported for all the shipments
        related to store view
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        store_view_obj = POOL.get('magento.store.store_view')
        carrier_obj = POOL.get('delivery.carrier')
        product_obj = POOL.get('product.product')
        magento_carrier_obj = POOL.get('magento.instance.carrier')
        picking_obj = POOL.get('stock.picking')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            store_view = store_view_obj.browse(
                txn.cursor, txn.user, self.store_view_id, txn.context
            )

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000001')
                mag_carriers = load_json('carriers', 'shipping_methods')

                with patch(
                    'magento.Customer', mock_customer_api(), create=True
                ):
                    partner = partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])
                with OrderConfig(*settings.ARGS) as order_config_api:
                    mag_carriers = order_config_api.get_shipping_methods()

                partner = partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                # Create sale order using magento data
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            magento_carrier_obj.create_all_using_magento_data(
                txn.cursor, txn.user, mag_carriers, context=context
            )

            product_id = product_obj.search(
                txn.cursor, txn.user, [], context=context
            )[0]

            # Create carrier
            carrier_id = carrier_obj.create(
                txn.cursor, txn.user, {
                    'name': 'DHL',
                    'partner_id': partner.id,
                    'product_id': product_id,
                }, context=context
            )

            # Set carrier for sale order
            sale_obj.write(
                txn.cursor, txn.user, order.id, {
                    'carrier_id': carrier_id
                }, context=context
            )
            order = sale_obj.browse(
                txn.cursor, txn.user, order.id, context
            )

            # Set picking as delivered
            picking_obj.action_assign(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_process(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_done(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )

            pickings = picking_obj.browse(
                txn.cursor, txn.user, map(int, order.picking_ids),
                context=context
            )

            for picking in pickings:
                self.assertFalse(picking.magento_increment_id)

            if settings.MOCK:

                with patch(
                        'magento.Shipment', mock_shipment_api(), create=True):
                    store_view_obj.export_shipment_status_to_magento(
                        txn.cursor, txn.user, store_view, context=context
                    )
            else:
                store_view_obj.export_shipment_status_to_magento(
                    txn.cursor, txn.user, store_view, context=context
                )

            pickings = picking_obj.browse(
                txn.cursor, txn.user, map(int, order.picking_ids),
                context=context
            )

            for picking in pickings:
                self.assertTrue(picking.magento_increment_id)

    @unittest.skipIf(not settings.MOCK, "requries mock settings")
    def test_0060_export_shipment_status_with_tracking_info(self):
        """
        Tests if Tracking information is being updated for shipments
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        store_view_obj = POOL.get('magento.store.store_view')
        carrier_obj = POOL.get('delivery.carrier')
        product_obj = POOL.get('product.product')
        magento_carrier_obj = POOL.get('magento.instance.carrier')
        picking_obj = POOL.get('stock.picking')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            store_view = store_view_obj.browse(
                txn.cursor, txn.user, self.store_view_id, txn.context
            )

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000001')
                mag_carriers = load_json('carriers', 'shipping_methods')

                with patch(
                    'magento.Customer', mock_customer_api(), create=True
                ):
                    partner = partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    for order in orders:
                        for item in order['items']:
                            if item['product_type'] == 'bundle':
                                order_data = order
                                break

                partner = partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                # Create sale order using magento data
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )
                with OrderConfig(*settings.ARGS) as order_config_api:
                    mag_carriers = order_config_api.get_shipping_methods()

            magento_carrier_obj.create_all_using_magento_data(
                txn.cursor, txn.user, mag_carriers, context=context
            )

            product_id = product_obj.search(
                txn.cursor, txn.user, [], context=context
            )[0]

            # Create carrier
            carrier_id = carrier_obj.create(
                txn.cursor, txn.user, {
                    'name': 'DHL',
                    'partner_id': partner.id,
                    'product_id': product_id,
                }, context=context
            )

            # Set carrier for sale order
            sale_obj.write(
                txn.cursor, txn.user, order.id, {
                    'carrier_id': carrier_id
                }, context=context
            )
            order = sale_obj.browse(
                txn.cursor, txn.user, order.id, context
            )

            # Set picking as delivered
            picking_obj.action_assign(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_process(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_done(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )

            with patch('magento.Shipment', mock_shipment_api(), create=True):
                # Export shipment status
                shipments = store_view_obj.export_shipment_status_to_magento(
                    txn.cursor, txn.user, store_view, context=context
                )

                # Export Tracking info
                self.assertEqual(
                    store_view_obj.export_tracking_info_to_magento(
                        txn.cursor, txn.user, shipments[0], context=context
                    ),
                    True
                )

    @unittest.skipIf(not settings.MOCK, "requries mock settings")
    def test_0070_export_shipment_status_with_last_export_date_case1(self):
        """
        Tests that if last shipment export time is there then shipment status
        cannot be exported for shipments delivered before last shipment
        export time
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        store_view_obj = POOL.get('magento.store.store_view')
        carrier_obj = POOL.get('delivery.carrier')
        product_obj = POOL.get('product.product')
        magento_carrier_obj = POOL.get('magento.instance.carrier')
        picking_obj = POOL.get('stock.picking')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            store_view = store_view_obj.browse(
                txn.cursor, txn.user, self.store_view_id, txn.context
            )

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000001')
                mag_carriers = load_json('carriers', 'shipping_methods')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    partner = partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'],
                        context
                    )

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])
                with OrderConfig(*settings.ARGS) as order_config_api:
                    mag_carriers = order_config_api.get_shipping_methods()

                partner = partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            magento_carrier_obj.create_all_using_magento_data(
                txn.cursor, txn.user, mag_carriers, context=context
            )

            product_id = product_obj.search(
                txn.cursor, txn.user, [], context=context
            )[0]

            # Create carrier
            carrier_id = carrier_obj.create(
                txn.cursor, txn.user, {
                    'name': 'DHL',
                    'partner_id': partner.id,
                    'product_id': product_id,
                }, context=context
            )

            # Set carrier for sale order
            sale_obj.write(
                txn.cursor, txn.user, order.id, {
                    'carrier_id': carrier_id
                }, context=context
            )
            order = sale_obj.browse(
                txn.cursor, txn.user, order.id, context
            )

            # Set picking as delivered
            picking_obj.action_assign(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_process(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_done(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )

            pickings = picking_obj.browse(
                txn.cursor, txn.user, map(int, order.picking_ids),
                context=context
            )

            export_date = datetime.date.today() + relativedelta(days=1)
            store_view_obj.write(
                txn.cursor, txn.user, store_view.id, {
                    'last_shipment_export_time': export_date.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )
                }, context=context
            )
            store_view = store_view_obj.browse(
                txn.cursor, txn.user, store_view.id, context=context
            )

            # Since here shipment's write date is smaller than last export
            # time. so it should not export status for these shipment

            for picking in pickings:
                self.assertFalse(
                    picking.write_date >= store_view.last_shipment_export_time
                )

            with self.assertRaises(Exception):
                with patch(
                    'magento.Shipment', mock_shipment_api(), create=True
                ):
                    # Export shipment status
                    store_view_obj.export_shipment_status_to_magento(
                        txn.cursor, txn.user, store_view, context=context
                    )

    @unittest.skipIf(not settings.MOCK, "requries mock settings")
    def test_0080_export_shipment_status_with_last_export_date_case2(self):
        """
        Tests that if last shipment export time is there then shipment status
        are exported for shipments delivered after last shipment export time
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')
        magento_order_state_obj = POOL.get('magento.order_state')
        store_view_obj = POOL.get('magento.store.store_view')
        carrier_obj = POOL.get('delivery.carrier')
        product_obj = POOL.get('product.product')
        magento_carrier_obj = POOL.get('magento.instance.carrier')
        picking_obj = POOL.get('stock.picking')
        website_obj = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            store_view = store_view_obj.browse(
                txn.cursor, txn.user, self.store_view_id, txn.context
            )

            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, txn.context
            )

            if settings.MOCK:
                order_states = load_json('order-states', 'all')
            else:
                with OrderConfig(*settings.ARGS) as order_config_api:
                    order_states = order_config_api.get_states()

            magento_order_state_obj.create_all_using_magento_data(
                txn.cursor, txn.user, order_states, context=context
            )

            if settings.MOCK:
                category_tree = load_json('categories', 'category_tree')
            else:
                with magento.Category(*settings.ARGS) as category_api:
                    category_tree = category_api.tree(
                        website.magento_root_category_id
                    )

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            if settings.MOCK:
                order_data = load_json('orders', '100000001')
                mag_carriers = load_json('carriers', 'shipping_methods')
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])
                with OrderConfig(*settings.ARGS) as order_config_api:
                    mag_carriers = order_config_api.get_shipping_methods()

            if settings.MOCK:
                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    partner = partner_obj.find_or_create_using_magento_id(
                        txn.cursor, txn.user, order_data['customer_id'], context
                    )

                # Create sale order using magento data
                with patch(
                        'magento.Product', mock_product_api(), create=True):
                    order = sale_obj.find_or_create_using_magento_data(
                        txn.cursor, txn.user, order_data, context=context
                    )
            else:
                partner = partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

                # Create sale order using magento data
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            magento_carrier_obj.create_all_using_magento_data(
                txn.cursor, txn.user, mag_carriers, context=context
            )

            product_id = product_obj.search(
                txn.cursor, txn.user, [], context=context
            )[0]

            # Create carrier
            carrier_id = carrier_obj.create(
                txn.cursor, txn.user, {
                    'name': 'DHL',
                    'partner_id': partner.id,
                    'product_id': product_id,
                }, context=context
            )

            # Set carrier for sale order
            sale_obj.write(
                txn.cursor, txn.user, order.id, {
                    'carrier_id': carrier_id
                }, context=context
            )
            order = sale_obj.browse(
                txn.cursor, txn.user, order.id, context
            )

            # Set picking as delivered
            picking_obj.action_assign(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_process(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )
            picking_obj.action_done(
                txn.cursor, txn.user, map(int, order.picking_ids)
            )

            pickings = picking_obj.browse(
                txn.cursor, txn.user, map(int, order.picking_ids),
                context=context
            )

            export_date = datetime.date.today() - relativedelta(days=1)
            store_view_obj.write(
                txn.cursor, txn.user, store_view.id, {
                    'last_shipment_export_time': export_date.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )
                }, context=context
            )
            store_view = store_view_obj.browse(
                txn.cursor, txn.user, store_view.id, context=context
            )

            # Since write date is greater than last shipment export time. It
            # should export shipment status successfully
            for picking in pickings:
                self.assertTrue(
                    picking.write_date >= store_view.last_shipment_export_time
                )

            if settings.MOCK:
                with patch(
                        'magento.Shipment', mock_shipment_api(), create=True):
                    # Export shipment status
                    store_view_obj.export_shipment_status_to_magento(
                        txn.cursor, txn.user, store_view, context=context
                    )
            else:
                store_view_obj.export_shipment_status_to_magento(
                    txn.cursor, txn.user, store_view, context=context
                )


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestSale),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
