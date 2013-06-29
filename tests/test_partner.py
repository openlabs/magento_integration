# -*- coding: utf-8 -*-
"""
    test_partner

    Tests Partner

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
from copy import deepcopy
import unittest

from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase, load_json


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
                'magento_website_id': self.website_id1
            })
            values = load_json('customers', '1')

            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), 0)

            # Create partner
            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, values, context
            )
            self.assert_(partner)

            self.assertTrue(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('name', '=', values['firstname'])
                    ], context=context
                )
            )
            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )

            self.assertEqual(len(partners), 1)

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
                'magento_website_id': self.website_id1
            })

            values = load_json('customers', '1')

            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, values, context
            )
            self.assert_(partner)
            self.assertTrue(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('name', '=', values['firstname'])
                    ], context=context
                )
            )
            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), 1)

            values = load_json('customers', '1')

            # Create partner with same magento_id and website_id it will not
            # create new one
            partner_obj.find_or_create(
                txn.cursor, txn.user, values, context
            )
            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), 1)

            # Create partner with different website
            context.update({
                'magento_website_id': self.website_id2
            })
            values = load_json('customers', '1')

            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, values, context
            )
            self.assert_(partner)

            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), 2)

            # Create partner with different magento_id
            context.update({
                'magento_website_id': self.website_id1
            })

            values = load_json('customers', '2')

            self.assertFalse(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('name', '=', values['firstname'])
                    ], context=context
                )
            )

            partner = partner_obj.find_or_create(
                txn.cursor, txn.user, values, context
            )
            self.assert_(partner)
            self.assertTrue(
                partner_obj.search(
                    txn.cursor, txn.user, [
                        ('name', '=', values['firstname'])
                    ], context=context
                )
            )
            partners = magento_partner_obj.search(
                txn.cursor, txn.user, [], context=context
            )
            self.assertEqual(len(partners), 3)


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestPartner),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
