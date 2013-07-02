# -*- coding: utf-8 -*-
"""
    __init__

    Test Suite

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
import unittest
from itsbroken.testing import drop_database

from .test_models import TestModels
from .test_country import TestCountry
from .test_product import TestProduct
from .test_partner import TestPartner
from .test_sale import TestSale
from .test_currency import TestCurrency


def tearDownModule():
    """
    Drop the database at the end of this test module
    Works only with unittest2 (default in python 2.7+)
    """
    drop_database()


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestModels),
        unittest.TestLoader().loadTestsFromTestCase(TestCountry),
        unittest.TestLoader().loadTestsFromTestCase(TestProduct),
        unittest.TestLoader().loadTestsFromTestCase(TestPartner),
        unittest.TestLoader().loadTestsFromTestCase(TestSale),
        unittest.TestLoader().loadTestsFromTestCase(TestCurrency),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
