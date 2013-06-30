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
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.country_obj = POOL.get('res.country')

            code = 'US'

            country_id = self.country_obj.search(
                txn.cursor, txn.user, [
                    ('code', '=', code)
                ], context=txn.context
            )[0]

            self.assertEqual(
                self.country_obj.search_using_magento_code(
                    txn.cursor, txn.user, code, txn.context
                ).id,
                country_id
            )

    def test_0020_search_country_with_invalid_code(self):
        """
        Tests if error is raised for searching country with invalid code
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.country_obj = POOL.get('res.country')

            code = 'abc'

            with self.assertRaises(Exception):
                self.country_obj.search_using_magento_code(
                    txn.cursor, txn.user, code, txn.context
                )


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
