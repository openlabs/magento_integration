# -*- coding: utf-8 -*-
"""
    test_models

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
from copy import deepcopy
import unittest
import magento

from mock import patch, MagicMock
from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase, load_json


def mock_inventory_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Inventory)

    handle = MagicMock(spec=magento.Inventory)
    handle.update.side_effect = lambda id, data: True
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


class TestProduct(TestBase):
    """Test the import of product
    """

    def test_0010_import_product_categories(self):
        """Test the import of product category using magento data
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({'magento_instance': self.instance_id1})

            category_obj = POOL.get('product.category')
            magento_category_obj = POOL.get(
                'magento.instance.product_category'
            )

            categories_before_import = category_obj.search(
                txn.cursor, txn.user, [], count=True
            )

            category_tree = load_json('categories', 'category_tree')

            category_obj.create_tree_using_magento_data(
                txn.cursor, txn.user, category_tree, context
            )

            categories_after_import = category_obj.search(
                txn.cursor, txn.user, [], count=True
            )
            self.assertTrue(categories_before_import < categories_after_import)

            # Look for root category
            root_category_id, = category_obj.search(
                txn.cursor, txn.user, [
                    ('magento_ids', '!=', []),
                    ('parent_id', '=', None)
                ]
            )
            root_category = category_obj.browse(
                txn.cursor, txn.user, root_category_id, context
            )
            self.assertEqual(root_category.magento_ids[0].magento_id, 1)

            self.assertEqual(len(root_category.child_id), 1)
            self.assertEqual(len(root_category.child_id[0].child_id), 4)

            # Make sure the categs created only in instance1 and not in
            # instance2
            self.assertTrue(
                magento_category_obj.search(txn.cursor, txn.user, [
                    ('instance', '=', self.instance_id1)
                ], count=True) > 0
            )
            self.assertTrue(
                magento_category_obj.search(txn.cursor, txn.user, [
                    ('instance', '=', self.instance_id2)
                ], count=True) == 0
            )

    def test_0020_import_simple_product(self):
        """Test the import of simple product using magento data
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_website': self.website_id1,
            })

            category_obj = POOL.get('product.category')
            product_obj = POOL.get('product.product')
            magento_product_obj = POOL.get('magento.website.product')

            category_data = load_json('categories', '8')

            category_obj.create_using_magento_data(
                txn.cursor, txn.user, category_data, context=context
            )

            products_before_import = product_obj.search(
                txn.cursor, txn.user, [], context=context, count=True
            )

            product_data = load_json('products', '17')
            product = product_obj.find_or_create_using_magento_data(
                txn.cursor, txn.user, product_data, context
            )
            self.assertEqual(product.categ_id.magento_ids[0].magento_id, 8)
            self.assertEqual(product.magento_product_type, 'simple')
            self.assertEqual(product.name, 'BlackBerry 8100 Pearl')

            products_after_import = product_obj.search(
                txn.cursor, txn.user, [], context=context, count=True
            )
            self.assertTrue(products_after_import > products_before_import)

            self.assertEqual(
                product, product_obj.find_using_magento_data(
                    txn.cursor, txn.user, product_data, context
                )
            )

            # Make sure the categs created only in website1 and not in
            # website2
            self.assertTrue(
                magento_product_obj.search(txn.cursor, txn.user, [
                    ('website', '=', self.website_id1)
                ], count=True) > 0
            )
            self.assertTrue(
                magento_product_obj.search(txn.cursor, txn.user, [
                    ('website', '=', self.website_id2)
                ], count=True) == 0
            )

    def test_0030_import_product_wo_categories(self):
        """Test the import of a product using magento data which does not have
        any categories associated
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_website': self.website_id1,
            })

            product_obj = POOL.get('product.product')

            product_data = load_json('products', '17-wo-category')
            product = product_obj.find_or_create_using_magento_data(
                txn.cursor, txn.user, product_data, context
            )
            self.assertEqual(product.magento_product_type, 'simple')
            self.assertEqual(product.name, 'BlackBerry 8100 Pearl')
            self.assertEqual(
                product.categ_id.name, 'Unclassified Magento Products'
            )

    def test_0040_import_configurable_product(self):
        """Test the import of a configurable product using magento data
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_website': self.website_id1,
            })

            category_obj = POOL.get('product.category')
            product_obj = POOL.get('product.product')

            category_data = load_json('categories', '17')

            category_obj.create_using_magento_data(
                txn.cursor, txn.user, category_data, context=context
            )

            product_data = load_json('products', '135')
            product = product_obj.find_or_create_using_magento_data(
                txn.cursor, txn.user, product_data, context
            )
            self.assertEqual(product.categ_id.magento_ids[0].magento_id, 17)
            self.assertEqual(product.magento_product_type, 'configurable')

    def test_0050_import_bundle_product(self):
        """Test the import of a bundle product using magento data
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_website': self.website_id1,
            })

            category_obj = POOL.get('product.category')
            product_obj = POOL.get('product.product')

            category_data = load_json('categories', '27')

            category_obj.create_using_magento_data(
                txn.cursor, txn.user, category_data, context=context
            )

            product_data = load_json('products', '164')
            product = product_obj.find_or_create_using_magento_data(
                txn.cursor, txn.user, product_data, context
            )
            self.assertEqual(product.categ_id.magento_ids[0].magento_id, 27)
            self.assertEqual(product.magento_product_type, 'bundle')

    def test_0060_import_grouped_product(self):
        """Test the import of a grouped product using magento data
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_website': self.website_id1,
            })

            category_obj = POOL.get('product.category')
            product_obj = POOL.get('product.product')

            category_data = load_json('categories', '22')

            category_obj.create_using_magento_data(
                txn.cursor, txn.user, category_data, context=context
            )

            product_data = load_json('products', '54')
            product = product_obj.find_or_create_using_magento_data(
                txn.cursor, txn.user, product_data, context
            )
            self.assertEqual(product.categ_id.magento_ids[0].magento_id, 22)
            self.assertEqual(product.magento_product_type, 'grouped')

    def test_0070_import_downloadable_product(self):
        """Test the import of a downloadable product using magento data
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_website': self.website_id1,
            })

            product_obj = POOL.get('product.product')

            product_data = load_json('products', '170')
            product = product_obj.find_or_create_using_magento_data(
                txn.cursor, txn.user, product_data, context
            )
            self.assertEqual(product.magento_product_type, 'downloadable')
            self.assertEqual(
                product.categ_id.name, 'Unclassified Magento Products'
            )

    def test_0080_export_product_stock_information(self):
        """
        This test checks if the method to call for updation of product
        stock info does not break anywhere in between.
        This method does not check the API calls
        """
        product_obj = POOL.get('product.product')
        website_obj = POOL.get('magento.instance.website')
        category_obj = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults(txn)
            context = deepcopy(CONTEXT)
            context.update({
                'magento_instance': self.instance_id1,
                'magento_website': self.website_id1,
            })

            category_data = load_json('categories', '17')

            category_obj.create_using_magento_data(
                txn.cursor, txn.user, category_data, context=context
            )

            product_data = load_json('products', '135')
            product_obj.find_or_create_using_magento_data(
                txn.cursor, txn.user, product_data, context
            )
            website = website_obj.browse(
                txn.cursor, txn.user, self.website_id1, context
            )

            with patch(
                'magento.Inventory', mock_inventory_api(), create=True
            ):
                website_obj.export_inventory_to_magento(
                    txn.cursor, txn.user, website, context
                )


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestProduct),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
