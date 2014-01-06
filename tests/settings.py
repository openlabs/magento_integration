# -*- coding: utf-8 -*-
"""
    settings

    A settings environment for the tests to run

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
import os

DEFAULT_URL = 'Some URL'

URL = os.environ.get('MAGENTO_URL', DEFAULT_URL)
API_USER = os.environ.get('MAGENTO_API_USER', 'apiuser')
API_PASSWORD = os.environ.get('MAGENTO_API_PASS', 'apipass')

MOCK = (URL == DEFAULT_URL)

ARGS = (URL, API_USER, API_PASSWORD)
