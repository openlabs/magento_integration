# -*- coding: utf-8 -*-
"""
    test_partner

    Tests Partner

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from copy import deepcopy
import unittest

import magento
from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase, load_json
import settings


class TestPartner(TestBase):
    """
    Tests partner
    """

    def test0010_create_partner(self):
        """
        Tests if customers imported from magento is created as partners
        in openerp
        """
        partner_obj = POOL.get('res.partner')
        magento_partner_obj = POOL.get('magento.website.partner')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            self.setup_defaults(txn)

            context = deepcopy(CONTEXT)
            context.update({
                'magento_website': self.website_id1,
                'magento_store_view': self.store_view_id,
            })

            if settings.MOCK:
                customer_data = load_json('customers', '1')
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])
                with magento.Customer(*settings.ARGS) as customer_api:
                    if order_data.get('customer_id'):
                        customer_data = customer_api.info(
                            order_data['customer_id']
                        )
                    else:
                        customer_data = {
                            'firstname': order_data['customer_firstname'],
                            'lastname': order_data['customer_lastname'],
                            'email': order_data['customer_email'],
                            'magento_id': 0
                        }

            partners_before_import = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            # Create partner
            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, customer_data, context
            )
            self.assert_(partner)

            self.assertTrue(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('email', '=', customer_data['email'])
                    ], context=context
                )
            )
            partners_after_import = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            self.assertTrue(partners_after_import > partners_before_import)

    def test0020_create_partner_for_same_website(self):
        """
        Tests that partners should be unique in a website
        """
        partner_obj = POOL.get('res.partner')
        magento_partner_obj = POOL.get('magento.website.partner')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            self.setup_defaults(txn)

            context = deepcopy(CONTEXT)
            context.update({
                'magento_website': self.website_id1,
                'magento_store_view': self.store_view_id,
            })

            initial_partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            if settings.MOCK:
                customer_data = load_json('customers', '1')
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])
                with magento.Customer(*settings.ARGS) as customer_api:
                    if order_data.get('customer_id'):
                        customer_data = customer_api.info(
                            order_data['customer_id']
                        )
                    else:
                        customer_data = {
                            'firstname': order_data['customer_firstname'],
                            'lastname': order_data['customer_lastname'],
                            'email': order_data['customer_email'],
                            'magento_id': 0
                        }

            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, customer_data, context
            )
            self.assert_(partner)
            self.assertTrue(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('email', '=', customer_data['email'])
                    ], context=context
                )
            )
            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), len(initial_partners) + 1)

            # Create partner with same magento_id and website_id it will not
            # create new one
            partner_obj.find_or_create(
                txn.cursor, txn.user, customer_data, context
            )
            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), len(initial_partners) + 1)

            # Create partner with different website
            context.update({
                'magento_website': self.website_id2
            })

            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, customer_data, context
            )
            self.assert_(partner)

            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), len(initial_partners) + 2)

            # Create partner with different magento_id
            context.update({
                'magento_website': self.website_id1
            })

            if settings.MOCK:
                customer_data = load_json('customers', '2')
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                with magento.Customer(*settings.ARGS) as customer_api:
                    for order in orders:
                        if order.get('customer_id'):
                            # Search for different cusotmer
                            if order_data['customer_id'] == \
                                    order['customer_id']:
                                continue
                            customer_data = customer_api.info(
                                order['customer_id']
                            )
                        else:
                            customer_data = {
                                'firstname': order['customer_firstname'],
                                'lastname': order['customer_lastname'],
                                'email': order['customer_email'],
                                'magento_id': 0
                            }

            self.assertFalse(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('email', '=', customer_data['email'])
                    ], context=context
                )
            )

            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, customer_data, context
            )
            self.assert_(partner)
            self.assertTrue(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('email', '=', customer_data['email'])
                    ], context=context
                )
            )
            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), len(initial_partners) + 3)

    def test0030_create_address(self):
        """
        Tests if address creation works as expected
        """
        partner_obj = POOL.get('res.partner')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            self.setup_defaults(txn)

            context = deepcopy(CONTEXT)
            context.update({
                'magento_website': self.website_id1,
                'magento_store_view': self.store_view_id,
            })

            if settings.MOCK:
                customer_data = load_json('customers', '1')
                address_data = load_json('addresses', '1')
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = order_api.list()
                    order_data = order_api.info(orders[0]['increment_id'])
                with magento.Customer(*settings.ARGS) as customer_api:
                    if order_data.get('customer_id'):
                        customer_data = customer_api.info(
                            order_data['customer_id']
                        )
                    else:
                        customer_data = {
                            'firstname': order_data['customer_firstname'],
                            'lastname': order_data['customer_lastname'],
                            'email': order_data['customer_email'],
                            'magento_id': 0
                        }
                    address_data = order_data['billing_address']

            # Create partner
            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, customer_data, context
            )

            partners_before_address = partner_obj.search(
                txn.cursor, txn.user, [], context=context, count=True
            )

            address_partner = partner_obj.\
                find_or_create_address_as_partner_using_magento_data(
                    txn.cursor, txn.user, address_data, partner, context
                )

            partners_after_address = partner_obj.search(
                txn.cursor, txn.user, [], context=context, count=True
            )

            self.assertTrue(partners_after_address > partners_before_address)

            self.assertEqual(
                address_partner.name, ' '.join(
                    [address_data['firstname'], address_data['lastname']]
                )
            )

    def test0040_match_address(self):
        """
        Tests if address matching works as expected
        """
        partner_obj = POOL.get('res.partner')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            self.setup_defaults(txn)

            context = deepcopy(CONTEXT)
            context.update({
                'magento_website': self.website_id1,
                'magento_store_view': self.store_view_id,
            })

            if settings.MOCK:
                customer_data = load_json('customers', '1')
                address_data = load_json('addresses', '1')
                address_data2 = load_json('addresses', '1b')
                address_data3 = load_json('addresses', '1c')
                address_data4 = load_json('addresses', '1d')
                address_data5 = load_json('addresses', '1e')
            else:
                with magento.Order(*settings.ARGS) as order_api:
                    orders = [
                        order_api.info(order['increment_id'])
                            for order in order_api.list()
                    ]
                    order_data = orders[0]
                with magento.Customer(*settings.ARGS) as customer_api:
                    if order_data.get('customer_id'):
                        customer_data = customer_api.info(
                            order_data['customer_id']
                        )
                    else:
                        customer_data = {
                            'firstname': order_data['customer_firstname'],
                            'lastname': order_data['customer_lastname'],
                            'email': order_data['customer_email'],
                            'magento_id': 0
                        }
                    address_data = order_data['billing_address']
                    for order in orders:
                        # Search for address with different country
                        if order['billing_address']['country_id'] != \
                                address_data['country_id']:
                            address_data2 = order['billing_address']

                        # Search for address with different state
                        if order['billing_address']['region'] != \
                                address_data['region']:
                            address_data3 = order['billing_address']

                        # Search for address with different telephone
                        if order['billing_address']['telephone'] != \
                                address_data['telephone']:
                            address_data4 = order['billing_address']

                        # Search for address with different street
                        if order['billing_address']['street'] != \
                                address_data['street']:
                            address_data5 = order['billing_address']

            # Create partner
            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, customer_data, context
            )

            address = partner_obj.\
                find_or_create_address_as_partner_using_magento_data(
                    txn.cursor, txn.user, address_data, partner, context
                )

            # Same address imported again
            self.assertTrue(
                partner_obj.match_address_with_magento_data(
                    txn.cursor, txn.user, address, address_data
                )
            )

            # Exactly similar address imported again
            self.assertTrue(
                partner_obj.match_address_with_magento_data(
                    txn.cursor, txn.user, address, address_data
                )
            )

            # Similar with different country
            self.assertFalse(
                partner_obj.match_address_with_magento_data(
                    txn.cursor, txn.user, address, address_data2
                )
            )

            # Similar with different state
            self.assertFalse(
                partner_obj.match_address_with_magento_data(
                    txn.cursor, txn.user, address, address_data3
                )
            )

            # Similar with different telephone
            self.assertFalse(
                partner_obj.match_address_with_magento_data(
                    txn.cursor, txn.user, address, address_data4
                )
            )

            # Similar with different street
            self.assertFalse(
                partner_obj.match_address_with_magento_data(
                    txn.cursor, txn.user, address, address_data5
                )
            )


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestPartner),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
