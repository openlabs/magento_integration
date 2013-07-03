# -*- coding: utf-8 -*-
"""
    test_currency

    Tests currency

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest

from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT

from test_base import TestBase


class TestCurrency(TestBase):
    """
    Tests currency
    """

    def test_0010_search_currency_with_valid_code(self):
        """
        Tests if currency can be searched using magento code
        """
        currency_obj = POOL.get('res.currency')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            code = 'USD'

            currency_id, = currency_obj.search(
                txn.cursor, txn.user, [
                    ('name', '=', code)
                ], context=txn.context
            )

            self.assertEqual(
                currency_obj.search_using_magento_code(
                    txn.cursor, txn.user, code, txn.context
                ).id,
                currency_id
            )

    def test_0020_search_currency_with_invalid_code(self):
        """
        Tests if error is raised for searching currency with invalid code
        """
        currency_obj = POOL.get('res.currency')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:

            code = 'abc'

            with self.assertRaises(Exception):
                currency_obj.search_using_magento_code(
                    txn.cursor, txn.user, code, txn.context
                )


def suite():
    """
    Test suite
    """
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestCurrency),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
