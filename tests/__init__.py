# -*- coding: utf-8 -*-
"""
    __init__

    Test Suite

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
import unittest
from .test_models import TestModels
from .test_country import TestCountry


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestModels),
        unittest.TestLoader().loadTestsFromTestCase(TestCountry),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
