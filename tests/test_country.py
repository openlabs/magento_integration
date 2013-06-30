# -*- coding: utf-8 -*-
"""
    test_country

    Tests country

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPLv3, see LICENSE for more details.
"""
import unittest

from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase


class TestCountry(TestBase):
    """
    Tests country
    """

    def test_0010_search_country_with_valid_code(self):
        """
        Tests if country can be searched using magento code
        """
        country_obj = POOL.get('res.country')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            code = 'US'

            country_id, = country_obj.search(
                txn.cursor, txn.user, [
                    ('code', '=', code)
                ], context=txn.context
            )

            self.assertEqual(
                country_obj.search_using_magento_code(
                    txn.cursor, txn.user, code, txn.context
                ).id,
                country_id
            )

    def test_0020_search_country_with_invalid_code(self):
        """
        Tests if error is raised for searching country with invalid code
        """
        country_obj = POOL.get('res.country')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            code = 'abc'

            with self.assertRaises(Exception):
                country_obj.search_using_magento_code(
                    txn.cursor, txn.user, code, txn.context
                )

    def test_0030_search_state_using_magento_region(self):
        """
        Tests if state can be searched using magento region
        """
        state_obj = POOL.get('res.country.state')
        country_obj = POOL.get('res.country')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            country = country_obj.search_using_magento_code(
                txn.cursor, txn.user, 'US', txn.context
            )
            state_ids = state_obj.search(
                txn.cursor, txn.user, [
                    ('name', '=', 'Florida'),
                    ('country_id', '=', country.id),
                ], context=txn.context
            )
            self.assertTrue(state_ids)
            self.assertEqual(len(state_ids), 1)

            # Create state and it should return id of existing record instead
            # of creating new one
            state = state_obj.find_or_create_using_magento_region(
                txn.cursor, txn.user, country, 'Florida', txn.context
            )

            self.assertEqual(state.id, state_ids[0])

            state_ids = state_obj.search(
                txn.cursor, txn.user, [
                    ('name', '=', 'Florida'),
                    ('country_id', '=', country.id),
                ], context=txn.context
            )
            self.assertEqual(len(state_ids), 1)

    def test_0040_create_state_using_magento_region(self):
        """
        Tests if state is being created when not found using magento region
        """
        state_obj = POOL.get('res.country.state')
        country_obj = POOL.get('res.country')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            country = country_obj.search_using_magento_code(
                txn.cursor, txn.user, 'IN', txn.context
            )

            states = state_obj.search(
                txn.cursor, txn.user, [
                    ('name', '=', 'UP'),
                    ('country_id', '=', country.id),
                ], context=txn.context
            )
            self.assertEqual(len(states), 0)

            # Create state
            state_obj.find_or_create_using_magento_region(
                txn.cursor, txn.user, country, 'UP', txn.context
            )

            states = state_obj.search(
                txn.cursor, txn.user, [
                    ('name', '=', 'UP'),
                    ('country_id', '=', country.id),
                ], context=txn.context
            )
            self.assertEqual(len(states), 1)


def suite():
    """
    Test suite
    """
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestCountry),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
