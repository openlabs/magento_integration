# -*- coding: utf-8 -*-
"""
    test_models

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
from copy import deepcopy
import unittest

from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase, get_loaded_json


class TestProduct(TestBase):
    """Test the import of product
    """

    def test_0010_import_product_categories(self):
        """Test the import of product using magento data
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

            category_tree = get_loaded_json('categories', 'category_tree')

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


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestProduct),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
