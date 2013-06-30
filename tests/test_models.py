# -*- coding: utf-8 -*-
"""
    test_models

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
import unittest

from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from .test_base import TestBase


class TestModels(TestBase):
    """Test the model structure of instance, website, store and store views
    """

    def test_0010_create_instance(self):
        """
        Test creation of a new instance
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            instance_obj = POOL.get('magento.instance')

            values = {
                'name': 'Test Instance',
                'url': 'some test url',
                'api_user': 'admin',
                'api_key': 'testkey',
            }
            instance_id = instance_obj.create(
                txn.cursor, txn.user, values, txn.context
            )
            instance = instance_obj.browse(txn.cursor, txn.user, instance_id)
            self.assertEqual(instance.name, values['name'])

    def test_0020_create_website(self):
        """
        Test creation of a new website under an instance
        Also check if the related field for company works as expected
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            instance_obj = POOL.get('magento.instance')
            website_obj = POOL.get('magento.instance.website')

            values = {
                'name': 'Test Instance',
                'url': 'some test url',
                'api_user': 'admin',
                'api_key': 'testkey',
            }
            instance_id = instance_obj.create(
                txn.cursor, txn.user, values, txn.context
            )
            instance = instance_obj.browse(txn.cursor, txn.user, instance_id)

            website_id = website_obj.create(txn.cursor, txn.user, {
                'name': 'A test website',
                'magento_id': 1,
                'code': 'test_code',
                'instance': instance.id,
            })
            website = website_obj.browse(txn.cursor, txn.user, website_id)
            self.assertEqual(website.name, 'A test website')
            self.assertEqual(website.company, instance.company)
            self.assertEqual(instance.websites[0].id, website.id)

    def test_0030_create_store(self):
        """
        Test creation of a new store under a website
        Also check if the related fields work as expected
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            instance_obj = POOL.get('magento.instance')
            website_obj = POOL.get('magento.instance.website')
            store_obj = POOL.get('magento.website.store')

            values = {
                'name': 'Test Instance',
                'url': 'some test url',
                'api_user': 'admin',
                'api_key': 'testkey',
            }
            instance_id = instance_obj.create(
                txn.cursor, txn.user, values, txn.context
            )
            instance = instance_obj.browse(txn.cursor, txn.user, instance_id)

            website_id = website_obj.create(txn.cursor, txn.user, {
                'name': 'A test website',
                'magento_id': 1,
                'code': 'test_code',
                'instance': instance.id,
            })
            website = website_obj.browse(txn.cursor, txn.user, website_id)

            store_id = store_obj.create(txn.cursor, txn.user, {
                'name': 'A test store',
                'magento_id': 1,
                'website': website.id,
            })
            store = store_obj.browse(txn.cursor, txn.user, store_id)

            self.assertEqual(store.name, 'A test store')
            self.assertEqual(store.instance, website.instance)
            self.assertEqual(store.company, website.company)
            self.assertEqual(website.stores[0].id, store.id)

    def test_0040_create_store_view(self):
        """
        Test creation of a new store view under a store
        Also check if the related fields work as expected
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            instance_obj = POOL.get('magento.instance')
            website_obj = POOL.get('magento.instance.website')
            store_obj = POOL.get('magento.website.store')
            store_view_obj = POOL.get('magento.store.store_view')

            values = {
                'name': 'Test Instance',
                'url': 'some test url',
                'api_user': 'admin',
                'api_key': 'testkey',
            }
            instance_id = instance_obj.create(
                txn.cursor, txn.user, values, txn.context
            )
            instance = instance_obj.browse(txn.cursor, txn.user, instance_id)

            website_id = website_obj.create(txn.cursor, txn.user, {
                'name': 'A test website',
                'magento_id': 1,
                'code': 'test_code',
                'instance': instance.id,
            })
            website = website_obj.browse(txn.cursor, txn.user, website_id)

            store_id = store_obj.create(txn.cursor, txn.user, {
                'name': 'A test store',
                'magento_id': 1,
                'website': website.id,
            })
            store = store_obj.browse(txn.cursor, txn.user, store_id)

            store_view_id = store_view_obj.create(txn.cursor, txn.user, {
                'name': 'A test store view',
                'code': 'test_code',
                'magento_id': 1,
                'store': store.id,
            })
            store_view = store_view_obj.browse(
                txn.cursor, txn.user, store_view_id
            )

            self.assertEqual(store_view.name, 'A test store view')
            self.assertEqual(store_view.instance, store.instance)
            self.assertEqual(store_view.company, store.company)
            self.assertEqual(store.store_views[0].id, store_view.id)


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestModels),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
