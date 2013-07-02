# -*- coding: utf-8 -*-
"""
    test_sale

    Test Sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from copy import deepcopy
import unittest

import magento
from mock import patch, MagicMock
from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase, load_json


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


class TestSale(TestBase):
    """
    Tests import of sale order
    """

    def test_0010_import_sale_order_with_products(self):
        """
        Tests import of sale order using magento data
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            category_tree = load_json('categories', 'category_tree')
            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            orders = sale_obj.search(txn.cursor, txn.user, [], context=context)
            self.assertEqual(len(orders), 0)

            order_data = load_json('orders', '100000001')

            with patch('magento.Customer', mock_customer_api(), create=True):
                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

            # Create sale order using magento data
            with patch('magento.Product', mock_product_api(), create=True):
                order = sale_obj.find_or_create_using_magento_data(
                    txn.cursor, txn.user, order_data, context=context
                )

            self.assertEqual(order.state, 'manual')

            orders = sale_obj.search(txn.cursor, txn.user, [], context=context)
            self.assertEqual(len(orders), 1)

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(
                len(order.order_line), len(order_data['items']) + 1
            )

    def test_0020_find_or_create_order_using_increment_id(self):
        """
        Tests finding and creating order using increment id
        """
        sale_obj = POOL.get('sale.order')
        partner_obj = POOL.get('res.partner')
        category_obj = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_store_view': self.store_view_id,
                'magento_website': self.website_id1,
            })

            category_tree = load_json('categories', 'category_tree')
            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            orders = sale_obj.search(txn.cursor, txn.user, [], context=context)
            self.assertEqual(len(orders), 0)

            order_data = load_json('orders', '100000001')

            with patch('magento.Customer', mock_customer_api(), create=True):
                partner_obj.find_or_create_using_magento_id(
                    txn.cursor, txn.user, order_data['customer_id'], context
                )

            # Create sale order using magento increment_id
            with patch('magento.Order', mock_order_api(), create=True):
                order = sale_obj.find_or_create_using_magento_increment_id(
                    txn.cursor, txn.user, order_data['increment_id'],
                    context=context
                )

            orders = sale_obj.search(txn.cursor, txn.user, [], context=context)

            self.assertEqual(len(orders), 1)

            # Item lines + shipping line should be equal to lines on openerp
            self.assertEqual(
                len(order.order_line), len(order_data['items']) + 1
            )


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestSale),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
